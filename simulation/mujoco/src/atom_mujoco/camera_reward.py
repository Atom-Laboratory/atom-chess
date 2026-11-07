"""Privileged simulation evaluation, kept outside actor features."""
from dataclasses import dataclass
import numpy as np
from .scene_feedback import SceneFeedback


@dataclass(frozen=True)
class PhysicalTruth:
    position: np.ndarray
    velocity: np.ndarray
    upright_angle: float
    tcp: np.ndarray
    bilateral_grip: bool
    released: bool


class RewardEvaluator:
    def __init__(self, sim, piece, target, support_z, piece_height, placement_radius, weights):
        self.sim, self.piece, self.target = sim, piece, np.array(target)
        self.support_z, self.piece_height = support_z, piece_height
        self.radius, self.weights = placement_radius, weights
        self.feedback = SceneFeedback(sim)
        self.body = sim.model.body(piece).id
        self.dof = sim.model.jnt_dofadr[sim.model.body_jntadr[self.body]]
        self.events = set()
        self.stable = 0

    def read(self):
        sim = self.sim
        rotation = sim.data.xmat[self.body].reshape(3, 3)
        return PhysicalTruth(
            sim.data.xpos[self.body].copy(), sim.data.qvel[self.dof:self.dof+6].copy(),
            float(np.arccos(np.clip(rotation[2, 2], -1, 1))),
            sim.data.site('grasp_center').xpos.copy(),
            bool(self.feedback.grip_contacts(self.piece)), bool(self.feedback.released(self.piece)))

    def reset(self, grasp_offset):
        self.events.clear()
        self.stable = 0
        self.origin = self.read().position.copy()
        self.grasp_offset = grasp_offset
        self.previous_potential = self._potential(self.read())

    def _potential(self, truth):
        distance = np.linalg.norm(truth.tcp-(truth.position+[0, 0, self.grasp_offset]))
        return -min(float(distance/self.piece_height), 5.)

    def evaluate(self, phase, action, *, phase_complete=False, failure=None, unexpected=()):
        truth = self.read()
        potential = self._potential(truth)
        components = dict(approach=self.weights['approach']*(potential-self.previous_potential),
                          time=self.weights['time'],
                          action=self.weights['action']*float(np.square(action).sum()))
        self.previous_potential = potential
        lifted = truth.position[2] > self.origin[2]+self.piece_height
        placed = (np.linalg.norm(truth.position[:2]-self.target[:2]) <= self.radius
                  and abs(truth.position[2]-self.support_z) <= self.feedback.limits.support_height_error_m
                  and truth.upright_angle <= self.feedback.limits.upright_angle_rad)
        stable = (np.linalg.norm(truth.velocity[:3]) <= self.feedback.limits.linear_speed_m_s
                  and np.linalg.norm(truth.velocity[3:]) <= self.feedback.limits.angular_speed_rad_s)
        self.stable = self.stable+1 if placed and stable and truth.released else 0
        events = dict(grasp=truth.bilateral_grip, lift=truth.bilateral_grip and lifted,
                      transport=truth.bilateral_grip and lifted and
                      np.linalg.norm(truth.position[:2]-self.target[:2]) <= self.radius,
                      placement=placed and truth.released)
        for event, happened in events.items():
            if happened and event not in self.events:
                self.events.add(event)
                components[event] = self.weights[event]
        success = (phase == 'RETRACT' and phase_complete and self.stable >= 5
                   and {'grasp', 'lift', 'transport'} <= self.events)
        if unexpected:
            failure = 'COLLISION'
        if truth.position[2] < self.support_z-self.feedback.limits.support_height_error_m:
            failure = 'PIECE_LOST'
        if phase_complete and phase == 'GRASP_PIECE' and not truth.bilateral_grip:
            failure = 'GRASP_FAILED'
        if phase in ('LIFT_PIECE', 'APPROACH_TARGET') and 'grasp' in self.events and not truth.bilateral_grip:
            failure = 'GRIP_LOST'
        if phase_complete and phase == 'RETRACT' and not success:
            failure = 'PLACEMENT_FAILED'
        if failure:
            components['failure'] = self.weights['failure']
            success = False
        elif success:
            components['success'] = self.weights['success']
        return float(sum(components.values())), dict(
            success=bool(success), failure=failure, grasp='grasp' in self.events,
            lift='lift' in self.events, placement=bool(placed and truth.released),
            collisions=len(unexpected), reward_components=components,
            reward_source='simulation_oracle', placement_error_m=float(
                np.linalg.norm(truth.position[:2]-self.target[:2])),
            stable_release_frames=self.stable)
