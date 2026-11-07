"""Camera and physics resources for autonomous tasks, without a nominal path."""
import json
from pathlib import Path
import time

import mujoco
import numpy as np

from .backend import Simulation
from .board_piece_localization import square_offsets
from .chess_commands import fen_occupancy
from .collision import SceneCollision
from .contact_supervision import NonTargetContacts
from .motion_controller import MotionController
from .native_motion import NativeMotion
from .native_vision import NativeVision
from .virtual_camera import make_camera


def collision_height(model, piece):
    """Static local bounds of the active primitive colliders, in meters."""
    body = model.body(piece).id
    bounds = []
    for index in range(model.ngeom):
        if model.geom_bodyid[index] != body or not model.geom_contype[index]:
            continue
        rotation = np.empty(9)
        mujoco.mju_quat2Mat(rotation, model.geom_quat[index])
        normal = rotation.reshape(3, 3)[2]
        kind, size = model.geom_type[index], model.geom_size[index]
        if kind == mujoco.mjtGeom.mjGEOM_SPHERE:
            extent = size[0]
        elif kind == mujoco.mjtGeom.mjGEOM_BOX:
            extent = np.abs(normal) @ size
        elif kind == mujoco.mjtGeom.mjGEOM_CYLINDER:
            extent = size[0]*np.linalg.norm(normal[:2])+size[1]*abs(normal[2])
        else:
            raise ValueError(f'Unsupported piece collider bounds: {model.geom(index).name}')
        center = model.geom_pos[index, 2]
        bounds.append((center-extent, center+extent))
    if not bounds:
        raise ValueError('Selected piece has no physical colliders')
    return float(max(high for _, high in bounds)-min(low for low, _ in bounds))


class AutonomousScene:
    def __init__(self, configuration):
        self.config = (json.loads(Path(configuration).read_text(encoding='utf-8'))
                       if isinstance(configuration, (str, Path)) else dict(configuration))
        cfg = self.config
        if cfg.get('schema') != 1 or not cfg.get('localize_source_rgb'):
            raise ValueError('Autonomous scene requires a schema 1 RGB-localized fixture')
        self.sim = Simulation(cfg['bundle'])
        self.vision = self.renderer = None
        try:
            pieces = self.sim.manifest['pieces']
            expected = {cfg['piece'], *cfg.get('obstacle_pieces', [])}
            if {piece['name'] for piece in pieces} != expected:
                raise ValueError('Fixture pieces differ from the configured task')
            self.selected = next(piece for piece in pieces if piece['name'] == cfg['piece'])
            symbols = dict(pawn='p', knight='n', bishop='b', rook='r', queen='q', king='k')
            self.occupied = fen_occupancy(cfg['board_fen'])
            fixture = {piece['initial_square']: (symbols[piece['kind']].upper()
                       if piece['color'] == 'white' else symbols[piece['kind']]) for piece in pieces}
            if fixture != self.occupied or self.selected['initial_square'] != cfg['source']:
                raise ValueError('Logical task context and physical fixture disagree')
            self.targets = cfg.get('task_targets', [cfg['target']])
            if not self.targets or any(target in self.occupied for target in self.targets):
                raise ValueError('Autonomous transfer destinations must be empty')
            self.controller = MotionController(self.sim)
            self.motion = NativeMotion(cfg['motion_library'], self.sim)
            if not self.motion.has_wrist:
                raise ValueError('Autonomous manipulation requires the bounded wrist')
            self.collision = SceneCollision(self.sim)
            self.vision = NativeVision(cfg['vision_library'], layout=cfg['layout'])
            camera = cfg['camera']
            self.renderer = mujoco.Renderer(self.sim.model, height=camera['height'], width=camera['width'])
            self.camera = make_camera(camera)
            self.dwell = cfg['dwell_steps']
            if type(self.dwell) is not int or self.dwell <= 0:
                raise ValueError('Positive dwell count required')
            self.piece_height = collision_height(self.sim.model, cfg['piece'])
            self.pitch = self.sim.manifest['scene']['square_size_m']
            self.contact_guard = NonTargetContacts(self.sim.model, self.collision.robot,
                                                   [piece['name'] for piece in pieces], cfg['piece'])
            self.contact_penalty = float(cfg.get('non_target_contact_penalty', 20.))
            self.displacement_penalty_per_mm = float(cfg.get('neighbor_displacement_penalty_per_mm', 1.))
            if not np.isfinite([self.contact_penalty, self.displacement_penalty_per_mm]).all() or min(
                    self.contact_penalty, self.displacement_penalty_per_mm) < 0:
                raise ValueError('Contact and displacement penalties must be finite and nonnegative')
            self.localize_source_rgb = self.supervise = True
            self.centered_reference = None
            self.task_target = self.targets[0]
            self.np_random = np.random.default_rng()
            self.park = self.sim.validate(cfg['initial_command']).copy()
            model = self.sim.model
            board = model.geom('board_frame')
            self.surface_z = float(model.body('chessboard').pos[2]+board.pos[2]+board.size[2])
            # Fixed board-to-robot calibration, never a live object pose query.
            self.square_source = (model.body('chessboard').pos
                                  +model.site('square_center_'+cfg['source']).pos).copy()
        except Exception:
            self.close()
            raise

    def render(self, data=None):
        self.renderer.update_scene(self.sim.data if data is None else data, camera=self.camera)
        return self.renderer.render().copy()

    def observe(self, data=None):
        captured = time.monotonic()
        return self.vision.observe(self.render(data), captured_at_s=captured)

    def calibrate(self):
        if self.centered_reference is not None:
            return
        model = self.sim.model
        scratch = mujoco.MjData(model)
        scratch.qpos[self.sim.qadr] = self.park
        for piece in self.sim.manifest['pieces']:
            body = model.body(piece['name']).id
            address = model.jnt_qposadr[model.body_jntadr[body]]
            scratch.qpos[address+2] = -10.
        mujoco.mj_forward(model, scratch)
        empty = self.render(scratch)
        if not self.vision.set_empty(empty):
            raise RuntimeError('EMPTY_CAMERA_CALIBRATION_FAILED')
        self.empty_reference = self.vision.observe(empty)
        mujoco.mj_resetData(model, scratch)
        scratch.qpos[self.sim.qadr] = self.park
        scratch.ctrl[:] = self.park
        for _ in range(60*self.sim.substeps):
            mujoco.mj_step(model, scratch)
        mujoco.mj_forward(model, scratch)
        self.centered_reference = self.observe(scratch)
        if not self.centered_reference.oriented:
            raise RuntimeError('CENTERED_CAMERA_CALIBRATION_FAILED')

    def reset(self, *, seed=None, options=None):
        if seed is not None:
            self.np_random = np.random.default_rng(seed)
        if options and (set(options) != {'target'} or options['target'] not in self.targets):
            raise ValueError('Evaluation target must belong to the configured task')
        self.task_target = options['target'] if options else str(self.np_random.choice(self.targets))
        self.calibrate()
        self.command = self.park.copy()
        self.sim.reset(self.command)
        jitter = float(self.config.get('placement_jitter_m', 0.))
        if not np.isfinite(jitter) or not 0 <= jitter < self.pitch/4:
            raise ValueError('Placement jitter must be below a quarter square')
        for piece in self.sim.manifest['pieces']:
            body = self.sim.model.body(piece['name']).id
            address = self.sim.model.jnt_qposadr[self.sim.model.body_jntadr[body]]
            self.sim.data.qpos[address:address+2] += self.np_random.uniform(-jitter, jitter, 2)
        mujoco.mj_forward(self.sim.model, self.sim.data)
        for _ in range(60):
            self.controller.step(self.command)
        self.last_camera_frame = self.observe()
        offsets = square_offsets(self.empty_reference, self.centered_reference, self.last_camera_frame,
                                 [self.config['source']], self.pitch)
        if self.config['source'] not in offsets:
            raise RuntimeError('SOURCE_POSITION_UNVERIFIED_BY_CAMERA')
        self.source = self.square_source.copy()
        self.source[:2] += offsets[self.config['source']]
        self.observed_offsets = offsets
        self.contact_guard.reset()
        self.contact_guard.start_displacement(self.sim.data)
        if self.contact_guard.observe(self.sim.data):
            raise RuntimeError('RESET_PIECE_TOPPLED')

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
        if self.vision is not None:
            self.vision.close()
