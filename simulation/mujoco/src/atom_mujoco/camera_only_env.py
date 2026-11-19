"""Experimental RGB-reward residual environment without privileged task feedback."""
import time

import mujoco
import numpy as np

from .camera_manipulation_env import CameraManipulationEnv
from .native_motion import ACTOR_PHASES
from .camera_policy import PHASES
from .visual_verification import VisualVerification
from .neighbor_vision import NeighborEvidence
from .piece_vision import PieceAppearance
from .contact_supervision import NonTargetContacts
from .board_piece_localization import square_offsets
from .chess_commands import fen_occupancy


class CameraOnlyEnv(CameraManipulationEnv):
    VERSION = 2

    def __init__(self, configuration):
        self.current_target = None
        super().__init__(configuration)
        # The inherited planner derives nominal poses from static model geometry.
        # Privileged task evaluation is never invoked in this environment.
        self.reward_evaluator = None
        self.qualification = bool(self.config.get('visual_qualification', False))
        if self.qualification:
            self.VERSION = 6
        self.targets = self.config.get('task_targets', [self.config['target']])
        if (not isinstance(self.targets, list) or not self.targets
                or len(set(self.targets)) != len(self.targets)
                or any(not isinstance(s, str) or len(s) != 2
                       or s[0] not in 'abcdefgh' or s[1] not in '12345678'
                       or s == self.config['source'] for s in self.targets)):
            raise ValueError('Expected distinct destination squares')
        if 'task_targets' in self.config:
            self.VERSION = 3
        if self.motion.has_wrist:
            self.VERSION = 4
        if self.config.get("obstacle_pieces"):
            self.VERSION = 5
        if self.qualification:
            self.VERSION = 6
        jitter = float(self.config.get('placement_jitter_m', 0.))
        if not np.isfinite(jitter) or not 0 <= jitter < self.sim.manifest['scene']['square_size_m']/4:
            raise ValueError('Placement jitter must be finite and below a quarter square')
        if self.motion.has_wrist:
            for key in ('wrist_nominal_rad', 'transport_wrist_rad'):
                value = float(self.config.get(key, self.motion.default_wrist))
                if not np.isfinite(value) or not self.sim.lower[-1] <= value <= self.sim.upper[-1]:
                    raise ValueError('Configured wrist orientation exceeds its joint limits')
            speed = float(self.config.get('wrist_residual_speed_rad_s', .4))
            angle = float(self.config.get('wrist_residual_rad', .35))
            if not np.isfinite([speed, angle]).all() or not 0 < speed <= self.sim.speed[-1] or not 0 < angle <= np.pi:
                raise ValueError('Wrist residual range and speed must respect the model limits')
        topple = float(self.config.get('topple_penalty', 50.))
        if not np.isfinite(topple) or topple < 0:
            raise ValueError('Topple penalty must be finite and nonnegative')
        self.contact_penalty = float(self.config.get('non_target_contact_penalty', 0.))
        if not np.isfinite(self.contact_penalty) or self.contact_penalty < 0:
            raise ValueError('Contact penalty must be finite and nonnegative')
        self.contact_guard = NonTargetContacts(
            self.sim.model, self.collision.robot,
            [p['name'] for p in self.sim.manifest['pieces']], self.config['piece'])
        self.localize_source_rgb = bool(self.config.get('localize_source_rgb', False))
        self.centered_reference = None
        self.displacement_penalty_per_mm = float(self.config.get('neighbor_displacement_penalty_per_mm', 0.))
        if not np.isfinite(self.displacement_penalty_per_mm) or self.displacement_penalty_per_mm < 0:
            raise ValueError('Displacement penalty must be finite and nonnegative')
        self.supervise = bool(self.contact_penalty or self.displacement_penalty_per_mm)
        self.reward_source = 'rgb_plus_non_target_contacts' if self.contact_penalty else 'rgb_only'
        if self.displacement_penalty_per_mm:
            self.reward_source = 'rgb_plus_simulated_piece_supervision'
        if self.contact_penalty:
            self.VERSION = 7
        if self.localize_source_rgb:
            self.VERSION = 8
            self.occupied = fen_occupancy(self.config['board_fen'])
            source = self.config['source']
            pieces = self.sim.manifest['pieces']
            symbols = dict(pawn='p', knight='n', bishop='b', rook='r', queen='q', king='k')
            fixture = {piece['initial_square']: (symbols[piece['kind']].upper()
                       if piece['color'] == 'white' else symbols[piece['kind']]) for piece in pieces}
            if (pieces[0]['initial_square'] != source or fixture != self.occupied
                    or any(target in self.occupied for target in self.targets)):
                raise ValueError('Chess Core FEN, fixture or transfer endpoints disagree')
        if self.displacement_penalty_per_mm:
            self.VERSION = 9

    @property
    def task_target(self):
        return self.current_target or self.config['target']

    def reset(self, *, seed=None, options=None):
        if options and (set(options) != {'target'} or options['target'] not in self.targets):
            raise ValueError('Evaluation target must belong to the configured curriculum')
        if seed is not None:
            self.np_random = np.random.default_rng(seed)
        self.current_target = (options['target'] if options else
                               str(self.np_random.choice(self.targets)))
        self._configure_nominal()
        self.reward_evaluator = None
        self.visual = VisualVerification(self.config['source'], self.task_target,
                                         self.sim.manifest['pieces'][0]['color'])
        self.motion.default_wrist = self.config.get('wrist_nominal_rad', self.motion.default_wrist)
        self.command = self.sim.validate(self.config['initial_command']).copy()
        self.sim.reset(self.command)
        jitter = self.config.get('placement_jitter_m', 0.)
        if jitter:
            model = self.sim.model
            for piece in self.sim.manifest['pieces']:
                body = model.body(piece['name']).id
                address = model.jnt_qposadr[model.body_jntadr[body]]
                self.sim.data.qpos[address:address+2] += self.np_random.uniform(-jitter, jitter, 2)
            mujoco.mj_forward(model, self.sim.data)
        for _ in range(60):
            self.controller.step(self.command)
        self.contact_guard.reset()
        if self.supervise and self.contact_guard.observe(self.sim.data):
            raise RuntimeError('RESET_PIECE_TOPPLED')
        if self.displacement_penalty_per_mm:
            self.contact_guard.start_displacement(self.sim.data)
        self.contact_steps = 0
        # Synthetic empty-board calibration is isolated from the live episode.
        scratch = mujoco.MjData(self.sim.model)
        if self.localize_source_rgb:
            if self.centered_reference is None:
                model = self.sim.model
                scratch.qpos[:] = model.qpos0
                scratch.qpos[self.sim.qadr] = self.command
                for piece in self.sim.manifest['pieces']:
                    body = model.body(piece['name']).id
                    address = model.jnt_qposadr[model.body_jntadr[body]]
                    scratch.qpos[address+2] = -10.
                mujoco.mj_forward(model, scratch)
                self.renderer.update_scene(scratch, camera=self.camera)
                empty_rgb = self.renderer.render().copy()
                if not self.vision.set_empty(empty_rgb):
                    raise RuntimeError('EMPTY_CAMERA_CALIBRATION_FAILED')
                self.empty_reference = self.vision.observe(empty_rgb)
                mujoco.mj_resetData(model, scratch)
                scratch.qpos[self.sim.qadr] = self.command
                scratch.ctrl[:] = self.command
                for _ in range(60*self.sim.substeps):
                    mujoco.mj_step(model, scratch)
                mujoco.mj_forward(model, scratch)
                self.renderer.update_scene(scratch, camera=self.camera)
                self.centered_reference = self.vision.observe(self.renderer.render().copy())
        else:
            scratch.qpos[:] = self.sim.data.qpos
            body = self.sim.model.body(self.config['piece']).id
            address = self.sim.model.jnt_qposadr[self.sim.model.body_jntadr[body]]
            scratch.qpos[address+2] = -10
            mujoco.mj_forward(self.sim.model, scratch)
            self.renderer.update_scene(scratch, camera=self.camera)
            if not self.vision.set_empty(self.renderer.render().copy()):
                raise RuntimeError('EMPTY_CAMERA_CALIBRATION_FAILED')
        self.phase = self.dwell_count = self.steps = 0
        self.inspect_destination = False
        self.wrist_travel_rad = 0.
        self.wrist_offset = 0.
        self.wrist_target_offset = 0.
        self.wrist_selected_phase = None
        self.previous_action = np.zeros(self.action_count, dtype=np.float32)
        self.visual.reset()
        self.reward_totals = {}
        self.episode_started = time.perf_counter()
        observation, info = self._observation()
        if info['perception_failure']:
            raise RuntimeError('RESET_PERCEPTION_FAILED')
        if self.last_camera_frame.candidates[self.visual.source] != self.visual.color:
            raise RuntimeError('SOURCE_PIECE_NOT_CONFIRMED_BY_CAMERA')
        squares = [p['initial_square'] for p in self.sim.manifest['pieces']
                   if p['name'] != self.config['piece']]
        if any(square in self.targets or square == self.config['source'] for square in squares):
            raise ValueError('Obstacle squares must be distinct from task endpoints')
        self.observed_offsets = None
        if self.localize_source_rgb:
            source = self.config['source']
            self.observed_offsets = square_offsets(
                self.empty_reference, self.centered_reference, self.last_camera_frame, self.occupied,
                self.sim.manifest['scene']['square_size_m'])
            if source not in self.observed_offsets:
                raise RuntimeError('SOURCE_POSITION_UNVERIFIED_BY_CAMERA')
            self.source[:2] += self.observed_offsets[source]
            self.poses = self.motion.plan(self.source, self.destination, self.safe_z, self.pick_z)
            squares = [square for square in self.occupied if square != source]
        self.neighbors = NeighborEvidence(self.last_camera_frame, squares)
        self.appearance = None
        if self.qualification:
            calibration = mujoco.MjData(self.sim.model)
            calibration.qpos[:] = self.sim.model.qpos0
            calibration.qpos[self.sim.qadr] = self.command
            body = self.sim.model.body(self.config['piece']).id
            address = self.sim.model.jnt_qposadr[self.sim.model.body_jntadr[body]]
            calibration.qpos[address+2] = -10
            mujoco.mj_forward(self.sim.model, calibration)
            self.renderer.update_scene(calibration, camera=self.camera)
            empty = self.vision.observe(self.renderer.render().copy())
            calibration.qpos[address:address+3] = [*self.destination[:2], self.support_z]
            upright_images = []
            for yaw in np.linspace(0, 2*np.pi, 16, endpoint=False):
                calibration.qpos[address+3:address+7] = [np.cos(yaw/2), 0, 0, np.sin(yaw/2)]
                mujoco.mj_forward(self.sim.model, calibration)
                self.renderer.update_scene(calibration, camera=self.camera)
                upright = self.vision.observe(self.renderer.render().copy())
                if not empty.oriented or not upright.oriented:
                    raise RuntimeError('TARGET_APPEARANCE_CALIBRATION_FAILED')
                upright_images.append(upright.rectified_rgb)
            pitch = self.sim.manifest['scene']['square_size_m']
            base_radius = float(self.sim.model.geom(self.config['piece']+'_base').size[0])
            # Permit image translation only while the modeled base fits its square.
            tolerance = int(np.floor((pitch/2-base_radius)*100/pitch/2)*2)
            self.appearance = PieceAppearance(empty.rectified_rgb, upright_images,
                                              self.task_target, placement_tolerance_px=tolerance)
        self.finished = False
        return observation, dict(info, verification='rgb_candidates_only', target=self.task_target, observed_offsets_m=self.observed_offsets)

    def step(self, action):
        if self.finished:
            raise RuntimeError('Reset required')
        action = np.asarray(action, dtype=np.float32)
        if action.shape != self.action_space.shape or not np.isfinite(action).all() or np.any(abs(action)>1):
            raise ValueError('Expected one normalized action per policy dimension')
        pose = self.poses[self.phase, :3]+action[:3]*self.residual_bounds[:3]
        opening = float(np.clip(self.openings[self.phase]+action[3]*self.residual_bounds[3],
                                self.sim.lower[3], self.sim.upper[3]))
        wrist = None
        if self.motion.has_wrist:
            offset_target = float(action[4])*self.config.get('wrist_residual_rad', .35)
            if self.qualification:
                if self.phase in (0, 4) and self.wrist_selected_phase != self.phase:
                    self.wrist_target_offset = offset_target
                    self.wrist_selected_phase = self.phase
                offset_target = self.wrist_target_offset
            increment = self.config.get('wrist_residual_speed_rad_s', .4)*self.sim.dt*self.repeat
            self.wrist_offset += float(np.clip(offset_target-self.wrist_offset, -increment, increment))
            nominal = (self.config.get('transport_wrist_rad', self.motion.default_wrist)
                       if self.phase >= 4 else self.motion.default_wrist)
            wrist = float(np.clip(nominal+self.wrist_offset,
                                  self.sim.lower[-1], self.sim.upper[-1]))
        desired = (np.array(self.config['initial_command'], dtype=float) if self.inspect_destination
                   else self.motion.solve(pose, opening, wrist=wrist))
        maximum = self.sim.speed*self.sim.dt*self.repeat
        delta = np.clip(desired-self.command, -maximum, maximum)
        if self.motion.has_wrist:
            self.wrist_travel_rad += abs(float(delta[-1]))
        self.command += delta
        self.previous_action = action.copy()
        self.contact_guard.begin_step()
        for _ in range(self.repeat):
            if self.supervise:
                self.controller.step(self.command, stop_when=lambda: self.contact_guard.observe(self.sim.data))
                if self.contact_guard.topple_event is not None:
                    break
            else:
                self.controller.step(self.command)
        self.steps += 1
        self.dwell_count = self.dwell_count+1 if np.allclose(
            self.command, desired, atol=1e-8, rtol=0) else 0
        phase_complete = self.dwell_count >= self.dwell
        if self.qualification and self.phase in (0, 4):
            phase_complete = phase_complete and abs(self.wrist_offset-self.wrist_target_offset) < 1e-6
        observation, visual = self._observation()
        confirmed = visual['visual_state'] == 'TARGET_TEMPORALLY_PRESENT_CANDIDATE'
        appearance_iou = (self.appearance.score(self.last_camera_frame.rectified_rgb)
                          if self.appearance and self.inspect_destination and phase_complete else None)
        appearance_ok = self.appearance is None or (appearance_iou is not None
                                                    and appearance_iou >= self.appearance.minimum_iou)
        success = bool(self.inspect_destination and phase_complete and confirmed and appearance_ok)
        failure = 'PERCEPTION_FAILED' if visual['perception_failure'] else None
        if self.contact_penalty and self.contact_guard.step_events:
            self.contact_steps += 1
        if self.supervise and self.contact_guard.topple_event is not None:
            failure = 'PIECE_TOPPLED'
            success = False
        neighbor_change = None
        if self.inspect_destination and phase_complete and not failure:
            neighbor_change = self.neighbors.observe(self.last_camera_frame)
            if neighbor_change is None:
                failure = 'NEIGHBOR_EVIDENCE_UNAVAILABLE'
            elif any(score > self.neighbors.limit for score in neighbor_change.values()):
                failure = 'NEIGHBOR_VISUAL_CHANGE'
            success = success and failure is None
        truncated = self.steps >= self.horizon and not success and not failure
        if truncated:
            failure = 'TIME_LIMIT'
        components = dict(time=-.01, action=-.001*float(np.square(action).sum()))
        if neighbor_change:
            components['neighbor_disturbance'] = -5.*max(neighbor_change.values())
        if self.contact_guard.displacement_delta_mm:
            components['neighbor_displacement'] = -self.displacement_penalty_per_mm*self.contact_guard.displacement_delta_mm
        if success:
            components['visual_success'] = 10.
        if self.contact_penalty and self.contact_guard.step_events:
            components['non_target_contact'] = -self.contact_penalty
        if failure == 'PIECE_TOPPLED':
            components['topple'] = -float(self.config.get('topple_penalty', 50.))
        if failure:
            components['failure'] = -5.
        info = dict(visual, success=success, failure=failure, grasp=None, lift=None,
                    placement=success, collisions=None, reward_source=self.reward_source, forbidden_contact=self.contact_guard.event if self.contact_penalty else None,
                    contact_steps=self.contact_steps, topple_event=self.contact_guard.topple_event, neighbor_change=neighbor_change, target=self.task_target,
                    visual_confirmed=success, reward_components=components, appearance_iou=appearance_iou,
                    neighbor_displacements_mm=(self.contact_guard.displacements_mm()
                                               if self.displacement_penalty_per_mm else None),
                    observed_offsets_m=self.observed_offsets, wrist_travel_rad=self.wrist_travel_rad,
                    wrist_command_rad=float(self.command[-1]) if self.motion.has_wrist else None,
                    phase=ACTOR_PHASES[self.phase], episode_steps=self.steps,
                    episode_wall_s=time.perf_counter()-self.episode_started)
        self._accumulate_reward(info)
        self.finished = bool(success or failure)
        if phase_complete and not self.finished and self.phase == 7 and not self.inspect_destination:
            self.inspect_destination = True
            self.dwell_count = 0
        if phase_complete and not self.finished and self.phase < 7:
            self.phase += 1
            self.dwell_count = 0
            observation['phase'] = np.array([PHASES.index(ACTOR_PHASES[self.phase])], dtype=np.int64)
        return observation, sum(components.values()), bool(success or failure and not truncated), bool(truncated), info
