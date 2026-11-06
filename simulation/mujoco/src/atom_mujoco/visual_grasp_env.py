"""Experimental pixel-only pawn lift curriculum. Rewards use simulation oracle."""
import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np

from .playground import Playground


class VisualGraspEnv(gym.Env):
    metadata = {'render_modes': ['rgb_array']}

    def __init__(self, bundle, horizon=100):
        super().__init__()
        self.playground = Playground(bundle, diagnostic_unchecked=True)
        self.sim = self.playground.sim
        self.horizon = horizon
        self.observation_space = spaces.Box(0, 255, (3, 96, 96), dtype=np.uint8)
        self.action_space = spaces.Box(-1., 1., (4,), dtype=np.float32)
        self.renderer = mujoco.Renderer(self.sim.model, height=96, width=96)
        self.camera = mujoco.MjvCamera()
        mujoco.mjv_defaultCamera(self.camera)
        self.camera.distance = .35
        self.camera.azimuth = 90
        self.camera.elevation = -60
        self.body = self.sim.model.body('white_pawn_e2').id
        self.site = self.sim.model.site('grasp_center').id
        self.finished = True

    def render(self):
        self.renderer.update_scene(self.sim.data, camera=self.camera)
        return self.renderer.render().copy()

    def observation(self):
        return self.render().transpose(2, 0, 1).copy()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.finished = True
        self.sim.reset()
        for _ in range(60):
            self.sim.advance(self.sim.target)
        self.origin = self.sim.data.xpos[self.body].copy()
        # Curriculum starts near the existing grasp height. This is reset-only staging.
        point = self.origin + [0, 0, .025]
        q = self.playground.solve(point)
        q[:3] += self.np_random.uniform(-1, 1, 3)*np.array([.025,.004,.025])
        q = np.clip(q, self.sim.lower, self.sim.upper)
        self.sim.reset(q)
        for _ in range(20):
            self.playground.controller.step(q)
        self.target = q.copy()
        self.camera.lookat[:] = self.origin + [0,0,.025]
        self.initial = {p['name']: self.sim.data.body(p['name']).xpos.copy()
                        for p in self.sim.manifest['pieces']}
        self.steps = self.success_dwell = 0
        self.finished = False
        self.previous_distance = self.distance()
        return self.observation(), {'reward_source':'simulation_oracle'}

    def distance(self):
        return float(np.linalg.norm(self.sim.data.site_xpos[self.site] -
                                    (self.sim.data.xpos[self.body]+[0,0,.012])))

    def step(self, action):
        if self.finished:
            raise RuntimeError('Reset required')
        action = np.asarray(action)
        if action.shape != (4,) or not np.isfinite(action).all() or np.any(np.abs(action)>1):
            raise ValueError('Expected four finite normalized actions')
        delta = action*np.array([.015,.002,.015,.0015])
        self.target[:3] += delta[:3]
        self.target[3:] += delta[3]
        self.target = np.clip(self.target,self.sim.lower,self.sim.upper)
        self.finished = True
        for _ in range(5):
            self.playground.controller.step(self.target)
        distance = self.distance()
        held = self.playground.feedback.grip_contacts('white_pawn_e2')
        lift = float(self.sim.data.xpos[self.body,2]-self.origin[2])
        disturbed = any(np.linalg.norm(self.sim.data.body(name).xpos-position)>.008
                        for name,position in self.initial.items() if name!='white_pawn_e2')
        success = held and lift>.035
        self.success_dwell = self.success_dwell+1 if success else 0
        success = self.success_dwell >= 3
        reward = (self.previous_distance-distance)*20 - .01 - .002*float(np.square(action).sum())
        reward += .1*held + 2*max(0.,min(lift,.05))
        reward += 10*success - 5*disturbed
        self.previous_distance = distance
        self.steps += 1
        terminated = bool(success or disturbed or self.sim.data.xpos[self.body,2]<0)
        truncated = self.steps>=self.horizon
        self.finished = terminated or truncated
        return self.observation(),float(reward),terminated,truncated,dict(
            success=bool(success), disturbed=bool(disturbed), lift_m=lift,
            reward_source='simulation_oracle')

    def close(self):
        self.renderer.close()
        self.playground.ledger.close()
