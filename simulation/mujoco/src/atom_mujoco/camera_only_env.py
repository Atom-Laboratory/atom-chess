"""Experimental RGB-reward residual environment without privileged task feedback."""
import time

import mujoco
import numpy as np

from .camera_manipulation_env import CameraManipulationEnv
from .native_motion import ACTOR_PHASES
from .camera_policy import PHASES
from .visual_verification import VisualVerification


class CameraOnlyEnv(CameraManipulationEnv):
    VERSION = 2

    def __init__(self, configuration):
        self.current_target = None
        super().__init__(configuration)
        # The inherited planner derives nominal poses from static model geometry.
        # Privileged task evaluation is never invoked in this environment.
        self.reward_evaluator = None
        self.targets = self.config.get('task_targets', [self.config['target']])
        if (not isinstance(self.targets, list) or not self.targets
                or len(set(self.targets)) != len(self.targets)
                or any(not isinstance(s, str) or len(s) != 2
                       or s[0] not in 'abcdefgh' or s[1] not in '12345678'
                       or s == self.config['source'] for s in self.targets)):
            raise ValueError('Expected distinct destination squares')
        if 'task_targets' in self.config:
            self.VERSION = 3

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
        self.command = self.sim.validate(self.config['initial_command']).copy()
        self.sim.reset(self.command)
        for _ in range(60):
            self.controller.step(self.command)
        # Synthetic empty-board calibration is isolated from the live episode.
        scratch = mujoco.MjData(self.sim.model)
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
        self.previous_action = np.zeros(4, dtype=np.float32)
        self.visual.reset()
        self.reward_totals = {}
        self.episode_started = time.perf_counter()
        observation, info = self._observation()
        if info['perception_failure']:
            raise RuntimeError('RESET_PERCEPTION_FAILED')
        if self.last_camera_frame.candidates[self.visual.source] != self.visual.color:
            raise RuntimeError('SOURCE_PIECE_NOT_CONFIRMED_BY_CAMERA')
        self.finished = False
        return observation, dict(info, verification='rgb_candidates_only', target=self.task_target)

    def step(self, action):
        if self.finished:
            raise RuntimeError('Reset required')
        action = np.asarray(action, dtype=np.float32)
        if action.shape != (4,) or not np.isfinite(action).all() or np.any(abs(action)>1):
            raise ValueError('Expected four normalized residual actions')
        pose = self.poses[self.phase, :3]+action[:3]*self.residual_bounds[:3]
        opening = float(np.clip(self.openings[self.phase]+action[3]*self.residual_bounds[3],
                                self.sim.lower[3], self.sim.upper[3]))
        desired = (np.array(self.config['initial_command'], dtype=float) if self.inspect_destination
                   else self.motion.solve(pose, opening))
        maximum = self.sim.speed*self.sim.dt*self.repeat
        self.command += np.clip(desired-self.command, -maximum, maximum)
        self.previous_action = action.copy()
        for _ in range(self.repeat):
            self.controller.step(self.command)
        self.steps += 1
        self.dwell_count = self.dwell_count+1 if np.allclose(
            self.command, desired, atol=1e-8, rtol=0) else 0
        phase_complete = self.dwell_count >= self.dwell
        observation, visual = self._observation()
        confirmed = visual['visual_state'] == 'TARGET_TEMPORALLY_PRESENT_CANDIDATE'
        success = bool(self.inspect_destination and phase_complete and confirmed)
        failure = 'PERCEPTION_FAILED' if visual['perception_failure'] else None
        truncated = self.steps >= self.horizon and not success and not failure
        if truncated:
            failure = 'TIME_LIMIT'
        components = dict(time=-.01, action=-.001*float(np.square(action).sum()))
        if success:
            components['visual_success'] = 10.
        if failure:
            components['failure'] = -5.
        info = dict(visual, success=success, failure=failure, grasp=None, lift=None,
                    placement=success, collisions=None, reward_source='rgb_only', target=self.task_target,
                    visual_confirmed=success, reward_components=components,
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
