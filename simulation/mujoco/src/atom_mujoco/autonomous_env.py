"""Free temporal control with camera observations and independent supervision."""
from dataclasses import asdict
import time

import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np

from .autonomous_control import AutonomousControl, interpolate_command
from .autonomous_feedback import ManipulationFeedback
from .autonomous_observation import VisualHistory
from .autonomous_scene import AutonomousScene
from .board_piece_localization import square_offsets


class AutonomousManipulationEnv(gym.Env):
    VERSION = 3
    OBJECTIVES = ('reach', 'grasp', 'lift')

    def __init__(self, configuration, *, objective='lift', horizon=128):
        super().__init__()
        if objective not in self.OBJECTIVES or type(horizon) is not int or horizon <= 0:
            raise ValueError('Expected reach, grasp or lift and a positive decision horizon')
        self.objective, self.horizon = objective, horizon
        self.base = AutonomousScene(configuration)
        try:
            if (not self.base.motion.has_wrist or not self.base.localize_source_rgb
                    or not self.base.supervise):
                raise ValueError('Autonomous prototype requires wrist, RGB localization and contact supervision')
            self.control = AutonomousControl(self.base)
            self.feedback = ManipulationFeedback(self.base)
            sim = self.base.sim
            self.action_space = spaces.Box(-1., 1., (7,), dtype=np.float32)
            self.observation_space = spaces.Dict(
                image=spaces.Box(0, 255, (6, 96, 96), dtype=np.uint8),
                task=spaces.Box(0., 1., (4,), dtype=np.float32),
                commanded_joints=spaces.Box(-1., 1., (len(sim.names),), dtype=np.float32),
                command_history=spaces.Box(-1., 1., (2*len(sim.names),), dtype=np.float32),
                visual_target=spaces.Box(-1., 1., (5,), dtype=np.float32),
                object_context=spaces.Box(0., 1., (8,), dtype=np.float32),
                previous_action=self.action_space,
                perception_valid=spaces.Box(0., 1., (1,), dtype=np.float32),
                goal=spaces.Box(0., 1., (3,), dtype=np.float32))
            self.history = VisualHistory()
            self.finished = True
            self.observer = None
        except Exception:
            self.base.close()
            raise

    @property
    def sim(self):
        return self.base.sim

    def _observation(self, frame=None):
        if frame is None:
            frame = self.base.observe()
        self.last_frame = frame
        age = time.monotonic()-frame.captured_at_s
        if age > self.base.config.get('max_perception_age_s', 1.):
            raise RuntimeError(f'CAMERA_FRAME_STALE: {age:.3f}s')
        offsets = square_offsets(self.base.empty_reference, self.base.centered_reference, frame,
                                 [self.base.config['source']], self.base.pitch)
        visible = self.base.config['source'] in offsets
        if visible:
            self.source_xy = self.base.square_source[:2]+offsets[self.base.config['source']]
            self.source_frame = frame.sequence
        predicted = self.control.commanded_tcp(self.command)
        # Host FK is an estimate from issued commands. No measured robot pose enters here.
        relative = np.array([*(self.source_xy-predicted[:2]), predicted[2]-self.base.surface_z])
        command = 2*(self.command-self.sim.lower)/(self.sim.upper-self.sim.lower)-1
        observation = self.history.observe(frame, command, self.previous_action,
                                           self.base.config['source'], self.base.task_target)
        observation['visual_target'] = np.array([
            *np.clip(relative/(8*self.base.pitch), -1., 1.), float(visible),
            min(1., (frame.sequence-self.source_frame)/32)], dtype=np.float32)
        kinds = ('pawn', 'knight', 'bishop', 'rook', 'queen', 'king')
        context = np.zeros(8, dtype=np.float32)
        context[kinds.index(self.base.selected['kind'])] = 1
        context[6+(self.base.selected['color'] == 'black')] = 1
        observation['object_context'] = context
        observation['goal'] = np.eye(3, dtype=np.float32)[self.OBJECTIVES.index(self.objective)]
        if not self.observation_space.contains(observation):
            raise RuntimeError('Autonomous observation violates its schema')
        return observation

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.base.reset(seed=seed, options=options)
        if not self.base.displacement_penalty_per_mm:
            self.base.contact_guard.start_displacement(self.sim.data)
        self.command = self.base.command.copy()
        self.source_xy = self.base.source[:2].copy()
        self.source_frame = self.base.last_camera_frame.sequence
        self._randomize_start()
        self.previous_action = np.zeros(7, dtype=np.float32)
        self.history.clear()
        self.feedback.reset()
        self.steps, self.episode_return = 0, 0.
        self.totals = {}
        self.finished = False
        observation = self._observation(self.base.last_camera_frame)
        self.perception_valid = bool(observation['perception_valid'][0])
        self.last_info = dict(phase='FREE_MOTION', objective=self.objective,
                              target=self.base.task_target, episode_steps=0, success=False,
                              reward_components={}, validation=dict(status='RESET'),
                              target_piece=self.base.config['piece'], object_kind=self.base.selected['kind'],
                              pad_distance_m=self.feedback.initial_distance,
                              best_pad_distance_m=self.feedback.initial_distance,
                              reach_threshold_m=self.feedback.reach_threshold,
                              reward_source='simulation_supervised_camera_actor')
        return observation, self.last_info.copy()

    def _randomize_start(self):
        region = self.base.config.get('autonomous', {}).get('start_radius_squares')
        if region is None:
            return
        region = np.asarray(region, dtype=float)
        if region.shape != (2,) or not np.isfinite(region).all() or not 0 < region[0] < region[1] <= 16:
            raise ValueError('Start radius requires two ordered positive bounds in board squares')
        model, data = self.sim.model, self.sim.data
        snapshot = data.qpos.copy(), data.qvel.copy(), data.time
        for _ in range(128):
            direction = self.np_random.normal(size=3)
            direction[2] = abs(direction[2])
            direction /= np.linalg.norm(direction)
            position = np.array([*self.source_xy, self.base.surface_z])
            position += direction*self.np_random.uniform(*region)*self.base.pitch
            wrist = self.np_random.uniform(self.sim.lower[-1], self.sim.upper[-1])
            try:
                command = self.sim.validate(self.base.motion.solve(position, 0., wrist=wrist,
                                           elbow_down=bool(self.np_random.integers(2))))
            except ValueError:
                continue
            data.qpos[:], data.qvel[:], data.time = snapshot
            data.qpos[self.sim.qadr] = command
            data.qvel[self.sim.vadr] = 0.
            data.ctrl[:] = command
            self.sim.reference = command.copy()
            self.sim.target = command.copy()
            mujoco.mj_forward(model, data)
            if self.control.sweep(command, 1.)[0] is None:
                continue
            self.base.contact_guard.reset()
            self.base.contact_guard.start_displacement(data)
            safe = True
            for _ in range(10):
                self.base.controller.step(command)
                self.base.contact_guard.observe(data)
                if (self.control.unexpected_contact() or self.base.contact_guard.topple_event
                        or self.base.contact_guard.event):
                    safe = False
                    break
            if not safe or max(self.base.contact_guard.displacements_mm().values(), default=0.) > .25:
                continue
            self.feedback.reset()
            if self.feedback.initial_distance <= self.feedback.reach_threshold:
                continue
            self.command = self.base.command = command.copy()
            self.base.last_camera_frame = self.base.observe()
            if not self.base.last_camera_frame.oriented:
                continue
            self.base.contact_guard.reset()
            self.base.contact_guard.start_displacement(data)
            return
        raise RuntimeError('NO_SAFE_RANDOMIZED_START: inspect the configured distribution and model')

    def step(self, action):
        started = time.perf_counter()
        if self.finished:
            raise RuntimeError('Reset required')
        choice = self.control.decode(action, self.command)
        self.pending_action = dict(action=np.asarray(action).tolist(), choice=asdict(choice),
                                   start_command=self.command.tolist())
        self.previous_action = np.asarray(action, dtype=np.float32).copy()
        failure = None
        contact = None
        path = []
        guard = self.base.contact_guard
        guard.begin_step()
        if not self.perception_valid:
            end = None
            validation = dict(status='PERCEPTION_REJECTED')
            failure = 'PERCEPTION_LOST'
        else:
            if self.observer is not None:
                self.observer(dict(choice=asdict(choice), phase='VALIDATING',
                                   validation=dict(status='PENDING'), executed_path=[]))
            end, validation = self.control.validate(choice, self.command, project=True)
        validated = time.perf_counter()

        disturbed = False

        def stop():
            nonlocal contact, disturbed
            guard.observe(self.sim.data)
            contact = self.control.unexpected_contact()
            disturbed = bool(np.any(guard.peaks_mm > .25))
            return bool(contact or guard.event or guard.topple_event or disturbed)

        if end is not None:
            self.pending_action['end_command'] = end.tolist()
            start = self.command.copy()
            for index in range(1, choice.intervals+1):
                goal = interpolate_command(start, end, index, choice.intervals)
                self.pending_action['executing_command'] = goal.tolist()
                self.pending_action['interval_index'] = index
                self.base.controller.step(goal, stop_when=stop)
                self.command = goal.copy()
                # This trace is simulator evidence, never an actor feature.
                path.append(self.sim.data.site_xpos[self.control.site].tolist())
                if self.observer is not None:
                    self.observer(dict(choice=asdict(choice), validation=validation,
                                       phase='EXECUTING', executed_path=path))
                if contact or guard.event or guard.topple_event:
                    failure = 'PIECE_TOPPLED' if guard.topple_event else 'CONTACT_REQUIRES_RECONCILIATION'
                    break
                if disturbed:
                    failure = 'DISTURBED_SCENE_REQUIRES_RECONCILIATION'
                    break
        # The policy's next choice needs a current image, including after a rejected attempt.
        executed = time.perf_counter()
        observation = self._observation()
        perceived = time.perf_counter()
        self.perception_valid = bool(observation['perception_valid'][0])
        if not self.perception_valid:
            failure = failure or 'PERCEPTION_LOST'
        if max(guard.displacements_mm().values(), default=0.) > .25:
            failure = failure or 'DISTURBED_SCENE_REQUIRES_RECONCILIATION'
        components, physical = self.feedback.evaluate(action, validation, self.objective, failure)
        self.steps += 1
        truncated = self.steps >= self.horizon and not (failure or physical['success'])
        if truncated:
            components['timeout'] = -5.
        for name, value in components.items():
            self.totals[name] = self.totals.get(name, 0.)+value
        reward = sum(components.values())
        self.episode_return += reward
        self.finished = bool(failure or physical['success'] or truncated)
        self.last_info = dict(physical, phase='FREE_MOTION', failure=failure or ('TIME_LIMIT' if truncated else None),
                              objective=self.objective, target=self.base.task_target,
                              target_piece=self.base.config['piece'], object_kind=self.base.selected['kind'],
                              validation=validation, choice=asdict(choice),
                              applied=bool(path), executed_path=path,
                              reward_components=components, episode_reward_components=self.totals.copy(),
                              episode_return=self.episode_return, episode_steps=self.steps,
                              topple_event=guard.topple_event, forbidden_contact=guard.event,
                              unexpected_contact=contact,
                              reward_source='simulation_supervised_camera_actor',
                              timings_s=dict(validation=validated-started, physics=executed-validated,
                                             perception=perceived-executed, feedback=time.perf_counter()-perceived,
                                             total=time.perf_counter()-started),
                              recovery='preflight_retry_available' if end is None and not failure else None)
        if self.observer is not None:
            self.observer(self.last_info)
        return observation, float(reward), bool(failure or physical['success']), bool(truncated), self.last_info.copy()

    def close(self):
        self.base.close()
