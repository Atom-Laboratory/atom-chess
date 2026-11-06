"""Experimental pixel-only pawn lift curriculum. Rewards use simulation oracle."""
import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np

from .playground import Playground
from .collision import pregrasp_opening


class VisualGraspEnv(gym.Env):
    metadata = {'render_modes': ['rgb_array']}

    VERSION = 3

    def __init__(self, bundle, horizon=100, stage='lift', *, full_open_reset=True):
        super().__init__()
        if stage not in ('lift', 'grasp') or horizon <= 0:
            raise ValueError('Expected lift/grasp stage and positive horizon')
        self.stage = stage
        self.full_open_reset = full_open_reset
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
        self.on_transition = None
        self.camera_fixed = False

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
        stem = self.sim.model.geom('white_pawn_e2_stem').id
        self.grip_offset = float(self.sim.model.geom_pos[stem,2]-self.sim.model.geom_size[stem,1]/4)
        approach_height = 0.
        if self.stage == 'grasp':
            approach_height = .020 if self.full_open_reset else .008
        point = self.origin + [0, 0, self.grip_offset + approach_height]
        q = self.playground.solve(point)
        # Small arm perturbations; no piece pose is reset after settling.
        q[:3] += self.np_random.uniform(-1, 1, 3)*np.array([.003,.0005,.003])
        if self.stage == 'grasp' and self.full_open_reset:
            q[3:] = self.sim.upper[3:]
        else:
            q[3:] = pregrasp_opening(self.sim, 'white_pawn_e2')
        q = np.clip(q, self.sim.lower, self.sim.upper)
        self.initial = {p['name']: self.sim.data.body(p['name']).xpos.copy()
                        for p in self.sim.manifest['pieces']}
        self.sim.data.qpos[self.sim.qadr] = q
        self.sim.data.qvel[self.sim.vadr] = 0.
        self.sim.reference = q.copy()
        self.sim.target = q.copy()
        self.sim.data.ctrl[:] = q
        mujoco.mj_forward(self.sim.model,self.sim.data)
        for _ in range(20):
            self.playground.controller.step(q)
        if self.stage == 'lift':
            q[3:] = pregrasp_opening(self.sim, 'white_pawn_e2', side_gap_m=-.0005)
            for _ in range(100):
                self.playground.controller.step(q)
            if not self.playground.feedback.grip_contacts('white_pawn_e2'):
                raise RuntimeError('RESET_GRASP_FAILED: lift curriculum requires bilateral grip')
        if self.stage == 'grasp' and self.full_open_reset:
            if any(self.playground.feedback.pad_contacts('white_pawn_e2')):
                raise RuntimeError('RESET_GRASP_HAS_CONTACT')
        if self.bystander_displacement() > .008:
            raise RuntimeError('RESET_DISTURBED_BYSTANDER')
        self.target = q.copy()
        if not self.camera_fixed:
            self.camera.lookat[:] = self.origin + [0,0,.025]
            self.camera_fixed = True
        self.steps = self.success_dwell = 0
        self.finished = False
        self.previous_potential = self.potential(
            bool(self.playground.feedback.grip_contacts('white_pawn_e2')),
            float(self.sim.data.xpos[self.body,2]-self.origin[2]))
        obs = self.observation()
        info = {'reward_source':'simulation_oracle', 'stage':self.stage, 'reset_grip':self.stage=='lift',
                'held':bool(self.playground.feedback.grip_contacts('white_pawn_e2'))}
        if self.on_transition:
            self.on_transition(obs,info)
        return obs, info

    def distance(self):
        return float(np.linalg.norm(self.sim.data.site_xpos[self.site] -
                                    (self.sim.data.xpos[self.body]+[0,0,self.grip_offset])))

    def potential(self, held, lift):
        return -20*self.distance() + 40*max(0.,min(lift,.05))*held + float(held)

    def bystander_displacement(self):
        return max(float(np.linalg.norm(self.sim.data.body(name).xpos-position))
                   for name,position in self.initial.items() if name!='white_pawn_e2')

    def step(self, action):
        if self.finished:
            raise RuntimeError('Reset required')
        action = np.asarray(action)
        if action.shape != (4,) or not np.isfinite(action).all() or np.any(np.abs(action)>1):
            raise ValueError('Expected four finite normalized actions')
        delta = action*np.array([.008,.002,.008,.001])
        self.target[:3] += delta[:3]
        self.target[3:] += delta[3]
        self.target = np.clip(self.target,self.sim.lower,self.sim.upper)
        self.finished = True
        for _ in range(5):
            self.playground.controller.step(self.target)
        held = self.playground.feedback.grip_contacts('white_pawn_e2')
        lift = float(self.sim.data.xpos[self.body,2]-self.origin[2])
        displacement = self.bystander_displacement()
        disturbed = displacement > .008
        success = held and lift>.035
        self.success_dwell = self.success_dwell+1 if success else 0
        success = self.success_dwell >= 3
        potential = self.potential(held,lift)
        reward = potential-self.previous_potential - .01 - .002*float(np.square(action).sum())
        reward += 10*success - 5*disturbed
        self.previous_potential = potential
        self.steps += 1
        terminated = bool(success or disturbed or self.sim.data.xpos[self.body,2]<0)
        truncated = self.steps>=self.horizon
        self.finished = terminated or truncated
        info = dict(success=bool(success), disturbed=bool(disturbed), lift_m=lift,
                    held=bool(held), bystander_displacement_m=displacement,
                    reward_source='simulation_oracle', stage=self.stage)
        obs = self.observation()
        if self.on_transition:
            self.on_transition(obs,info)
        return obs,float(reward),terminated,truncated,info

    def close(self):
        self.renderer.close()
        self.playground.ledger.close()
