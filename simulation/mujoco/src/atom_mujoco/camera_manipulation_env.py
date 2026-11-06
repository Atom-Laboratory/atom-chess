"""Camera-guided residual Gym environment over real acmotion nominal planning."""
import json
from pathlib import Path
import time

import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np

from .backend import Simulation
from .camera_policy import policy_observation, PHASES as POLICY_PHASES
from .collision import SceneCollision, SweptChecker, pregrasp_opening
from .motion_controller import MotionController
from .native_motion import NativeMotion, PHASES, ACTOR_PHASES
from .native_vision import NativeVision
from .camera_reward import RewardEvaluator
from .visual_verification import VisualVerification
from .virtual_camera import make_camera


class CameraManipulationEnv(gym.Env):
    metadata = {'render_modes': ['rgb_array']}
    VERSION = 1

    def __init__(self, configuration):
        super().__init__()
        self.config = json.loads(Path(configuration).read_text(encoding='utf-8')) if isinstance(
            configuration, (str, Path)) else dict(configuration)
        cfg = self.config
        if cfg.get('schema') != 1:
            raise ValueError('Unsupported camera environment configuration')
        self.sim = Simulation(cfg['bundle'])
        if len(self.sim.manifest['pieces']) != 1 or self.sim.manifest['pieces'][0]['name'] != cfg['piece']:
            raise ValueError('P038 requires an explicit one-piece fixture')
        self.controller = MotionController(self.sim)
        self.motion = NativeMotion(cfg['motion_library'], self.sim)
        self.vision = NativeVision(cfg['vision_library'], layout=cfg['layout'])
        self.collision = SceneCollision(self.sim)
        camera_cfg = cfg['camera']
        self.renderer = mujoco.Renderer(self.sim.model, height=camera_cfg['height'], width=camera_cfg['width'])
        self.camera = make_camera(camera_cfg)
        self.repeat, self.horizon, self.dwell = cfg['control_repeat'], cfg['horizon'], cfg['dwell_steps']
        if any(type(n) is not int or n <= 0 for n in (self.repeat, self.horizon, self.dwell)):
            raise ValueError('Positive control repeat, horizon and dwell required')
        self.action_space = spaces.Box(-1, 1, (4,), dtype=np.float32)
        self.observation_space = spaces.Dict({
            'image': spaces.Box(0, 255, (3, 96, 96), dtype=np.uint8),
            'task': spaces.Box(0, 1, (4,), dtype=np.float32),
            'previous_action': spaces.Box(-1, 1, (4,), dtype=np.float32),
            'commanded_joints': spaces.Box(self.sim.lower.astype(np.float32),
                                          self.sim.upper.astype(np.float32), dtype=np.float32),
            'phase': spaces.Box(0, 7, (1,), dtype=np.int64),
            'perception_valid': spaces.Box(0, 1, (1,), dtype=np.float32)})
        self.visual = VisualVerification(cfg['source'], cfg['target'],
                                         self.sim.manifest['pieces'][0]['color'])
        self._configure_nominal()
        self.finished = True

    @property
    def task_target(self):
        return self.config['target']

    def _square_position(self, square):
        return self.sim.model.body('chessboard').pos + self.sim.model.site('square_center_'+square).pos

    def _configure_nominal(self):
        sim, model, piece = self.sim, self.sim.model, self.config['piece']
        stem, base = model.geom(piece+'_stem').id, model.geom(piece+'_base').id
        proxies = [model.geom(piece+'_'+suffix).id for suffix in ('base', 'stem', 'head')]
        extents = [model.geom_size[g, 1] if model.geom_type[g] == mujoco.mjtGeom.mjGEOM_CYLINDER
                   else model.geom_size[g, 0] for g in proxies]
        bottom = min(model.geom_pos[g, 2]-extent for g, extent in zip(proxies, extents))
        top = max(model.geom_pos[g, 2]+extent for g, extent in zip(proxies, extents))
        board = model.geom('board_frame')
        surface = model.body('chessboard').pos[2]+board.pos[2]+board.size[2]
        self.source = self._square_position(self.config['source'])
        self.destination = self._square_position(self.task_target)
        self.grasp_offset = float(model.geom_pos[stem, 2]-model.geom_size[stem, 1]/4)
        self.support_z = float(surface-bottom)
        self.pick_z = self.support_z+self.grasp_offset
        self.piece_height = float(top-bottom)
        pad_thickness = float(model.geom('finger_1_pad').size[2]*2)
        self.safe_z = self.pick_z+2*self.piece_height+pad_thickness
        self.aperture = pregrasp_opening(sim, piece)
        self.grasp = pregrasp_opening(sim, piece, side_gap_m=-pad_thickness/6)
        self.poses = self.motion.plan(self.source, self.destination, self.safe_z, self.pick_z)
        self.openings = np.array([self.aperture if pose[3] == 100 else self.grasp for pose in self.poses])
        radius = float(model.geom_size[stem, 0])
        pitch = sim.manifest['scene']['square_size_m']
        clearance = pitch/2-float(model.geom_size[base, 0])
        if clearance <= 0:
            raise ValueError('Piece does not fit inside a board square')
        self.residual_bounds = np.array([min(radius/3, clearance/2)]*2 +
                                        [float(model.geom_size[stem, 1])/4,
                                         min(radius/6, (sim.upper[3]-sim.lower[3])/10)])
        self.reward_evaluator = RewardEvaluator(
            sim, piece, self.destination, self.support_z, self.piece_height,
            clearance, self.config['reward_weights'])
        self.nominal = [self.motion.solve(pose[:3], opening)
                        for pose, opening in zip(self.poses, self.openings)]

    def render(self):
        self.renderer.update_scene(self.sim.data, camera=self.camera)
        return self.renderer.render().copy()

    def _observation(self, rgb=None):
        captured = time.monotonic()
        rgb = self.render() if rgb is None else rgb
        frame = self.vision.observe(rgb, captured_at_s=captured)
        self.last_camera_frame = frame
        visual_state = self.visual.update(frame)
        phase_index = POLICY_PHASES.index(ACTOR_PHASES[self.phase])
        try:
            actor = policy_observation(
                frame, source=self.config['source'], target=self.task_target,
                previous_action=self.previous_action, commanded_joints=self.command,
                phase=ACTOR_PHASES[self.phase], max_age_s=self.config['max_perception_age_s'])
            result = actor.features()
            result['perception_valid'] = np.ones(1, dtype=np.float32)
            error = None
        except ValueError as exception:
            task = [ord(self.config['source'][0])-97, 8-int(self.config['source'][1]),
                    ord(self.task_target[0])-97, 8-int(self.task_target[1])]
            result = dict(image=np.zeros((3, 96, 96), dtype=np.uint8),
                          task=np.array(task, dtype=np.float32)/7,
                          previous_action=self.previous_action.copy(),
                          commanded_joints=self.command.astype(np.float32),
                          phase=np.array([phase_index], dtype=np.int64),
                          perception_valid=np.zeros(1, dtype=np.float32))
            error = str(exception)
        if not self.observation_space.contains(result):
            raise RuntimeError('Actor observation violates declared schema')
        # Byte round-trip keeps actor payloads detached from simulator/native arrays.
        result = {key: np.frombuffer(value.tobytes(), dtype=value.dtype).reshape(value.shape).copy()
                  for key, value in result.items()}
        return result, dict(perception_failure=error, visual_state=visual_state, visual_confirmed=False)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if options:
            raise ValueError('Use a versioned configuration for scenario changes')
        self.finished = True
        self.command = self.sim.validate(self.config['initial_command']).copy()
        self.sim.reset(self.command)
        for _ in range(60):
            self.controller.step(self.command)
        self.phase = self.dwell_count = self.steps = 0
        self.reward_totals = {}
        self.previous_action = np.zeros(4, dtype=np.float32)
        self.visual.reset()
        self.reward_evaluator.reset(self.grasp_offset)
        solutions = [self.nominal[i] for i in (0, 1, 3, 4, 5)]
        destination = np.array([*self.destination[:2], self.support_z])
        self.preflight = self.collision.check_plan(solutions, self.config['piece'], destination,
                                                   aperture=self.aperture, grasp=self.grasp)
        if not self.preflight['valid']:
            raise RuntimeError('NOMINAL_PREFLIGHT_FAILED: '+json.dumps(self.preflight['failure']))
        observation, info = self._observation()
        if info['perception_failure']:
            raise RuntimeError('RESET_PERCEPTION_FAILED: '+info['perception_failure'])
        self.finished = False
        self.episode_started = time.perf_counter()
        return observation, dict(info, seed=seed, verification='simulation_oracle_and_visual_candidates')

    def _supervise(self, start, end):
        sim, model = self.sim, self.sim.model
        selected = model.body(self.config['piece']).id
        selected_geoms = [g for g in self.collision.environment if model.geom_bodyid[g] == selected]
        others = [g for g in self.collision.environment if model.geom_bodyid[g] != selected]
        pairs = self.collision.pairs + [(a, b) for a in selected_geoms for b in others]
        pads = {model.geom('finger_1_pad').id, model.geom('finger_2_pad').id}
        allowed = [(a, b) for a, b in pairs if
                   self.phase > 0 and ((a in pads and model.geom_bodyid[b] == selected)
                   or (b in pads and model.geom_bodyid[a] == selected))]
        support = [g for g in others if model.geom(g).name == 'board_frame'
                   or model.geom(g).name == 'reference_floor'
                   or (model.geom(g).name or '').startswith('graveyard_support_')]
        if self.phase != 4:
            allowed += [(a, b) for a in selected_geoms for b in support]
        checker = SweptChecker(model, sim.data.qpos, sim.joint_ids, pairs)
        configure = None
        coefficients = None
        if self.reward_evaluator.feedback.grip_contacts(self.config['piece']):
            site = model.site('grasp_center').id
            rotation = sim.data.site_xmat[site].reshape(3, 3)
            offset = rotation.T @ (sim.data.xpos[selected]-sim.data.site_xpos[site])
            relative = rotation.T @ sim.data.xmat[selected].reshape(3, 3)
            address = model.jnt_qposadr[model.body_jntadr[selected]]
            def carried(data):
                current = data.site_xmat[site].reshape(3, 3)
                data.qpos[address:address+3] = data.site_xpos[site]+current@offset
                mujoco.mju_mat2Quat(data.qpos[address+3:address+7], (current@relative).reshape(-1))
            configure = carried
            coefficients = checker.coefficients.copy()
            for geom in selected_geoms:
                coefficients[geom] = np.max(checker.coefficients[self.collision.robot], axis=0)
                for j, joint in enumerate(sim.joint_ids):
                    if model.jnt_type[joint] == mujoco.mjtJoint.mjJNT_HINGE:
                        coefficients[geom, j] += 2*(np.linalg.norm(offset)+model.geom_rbound[geom])
        actual = sim.data.qpos[sim.qadr].copy()
        return checker.interval(actual, end, allowed=allowed, configure=configure,
                                extra_coefficients=coefficients)

    def step(self, action):
        if self.finished:
            raise RuntimeError('Reset required after episode termination')
        action = np.asarray(action, dtype=np.float32)
        if action.shape != (4,) or not np.isfinite(action).all() or np.any(np.abs(action) > 1):
            return self._finish_failure('INVALID_ACTION', np.zeros(4, dtype=np.float32))
        phase_name = PHASES[self.phase]
        pose = self.poses[self.phase, :3]+action[:3]*self.residual_bounds[:3]
        opening = float(np.clip(self.openings[self.phase]+action[3]*self.residual_bounds[3],
                                self.sim.lower[3], self.sim.upper[3]))
        try:
            desired = self.motion.solve(pose, opening)
            self.sim.validate(desired)
            maximum = self.sim.speed*self.sim.dt*self.repeat
            target = self.command+np.clip(desired-self.command, -maximum, maximum)
            failure = self._supervise(self.command, target)
            if failure:
                return self._finish_failure('UNSAFE_RESIDUAL', action, detail=failure)
        except ValueError as exception:
            return self._finish_failure('INVALID_RESIDUAL', action, detail=str(exception))
        self.command, self.previous_action = target.copy(), action.copy()
        unexpected = []
        roles = ('APPROACHING', 'GRASPING', 'VERIFYING_GRASP', 'LIFTING',
                 'TRANSPORTING', 'PLACING', 'RELEASING', 'VERIFYING_RELEASE')
        for _ in range(self.repeat):
            self.controller.step(self.command)
            unexpected = self.collision.unexpected_contacts(self.config['piece'], roles[self.phase])
            if unexpected:
                break
        self.steps += 1
        reached = np.allclose(self.command, desired, atol=1e-8, rtol=0)
        self.dwell_count = self.dwell_count+1 if reached else 0
        phase_complete = self.dwell_count >= self.dwell
        reward, info = self.reward_evaluator.evaluate(
            phase_name, action, phase_complete=phase_complete, unexpected=unexpected)
        observation, visual = self._observation()
        info.update(visual)
        if visual['perception_failure']:
            info['failure'] = 'PERCEPTION_FAILED'
            info['oracle_success_before_perception_failure'] = info['success']
            info['success'] = False
            reward -= info['reward_components'].pop('success', 0.)
            reward += self.config['reward_weights']['failure']
            info['reward_components']['failure'] = self.config['reward_weights']['failure']
        terminated = bool(info['success'] or info['failure'])
        truncated = self.steps >= self.horizon and not terminated
        if truncated:
            info['failure'] = 'TIME_LIMIT'
        if phase_complete and not terminated and not truncated and self.phase < 7:
            self.phase += 1
            self.dwell_count = 0
            observation['phase'] = np.array([POLICY_PHASES.index(ACTOR_PHASES[self.phase])], dtype=np.int64)
        self.finished = terminated or truncated
        self._accumulate_reward(info)
        info.update(phase=phase_name, episode_steps=self.steps,
                    episode_wall_s=time.perf_counter()-self.episode_started)
        return observation, reward, terminated, truncated, info

    def _finish_failure(self, reason, action, detail=None):
        self.steps += 1
        reward, info = self.reward_evaluator.evaluate(PHASES[self.phase], action, failure=reason)
        observation, visual = self._observation()
        self.finished = True
        self._accumulate_reward(info)
        info.update(visual, failure=reason, safety_detail=detail, phase=PHASES[self.phase],
                    episode_steps=self.steps, episode_wall_s=time.perf_counter()-self.episode_started)
        return observation, reward, True, False, info

    def _accumulate_reward(self, info):
        for component, value in info['reward_components'].items():
            self.reward_totals[component] = self.reward_totals.get(component, 0.)+value
        info['episode_reward_components'] = dict(self.reward_totals)

    def close(self):
        self.vision.close()
        self.renderer.close()
