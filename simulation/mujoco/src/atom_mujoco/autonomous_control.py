"""Temporal action decoding and simulated collision supervision."""
from dataclasses import dataclass

import mujoco
import numpy as np

from .collision import SweptChecker


def interpolate_command(start, end, index, intervals):
    """Keep floating-point interpolation inside its already validated endpoints."""
    fraction = index/intervals
    goal = (1.-fraction)*start+fraction*end
    return np.clip(goal, np.minimum(start, end), np.maximum(start, end))


@dataclass(frozen=True)
class MotionChoice:
    xyz_m: tuple
    wrist_rad: float
    opening_m: float
    elbow_down: bool
    intervals: int
    duration_s: float


class AutonomousControl:
    def __init__(self, base):
        self.base = base
        self.sim = sim = base.sim
        self.model = model = sim.model
        self.scratch = mujoco.MjData(model)
        self.site = model.site('grasp_center').id
        lengths = base.motion.geometry[:2]/1000
        planar = lengths.sum()*sim.speed[0]+lengths[1]*sim.speed[2]
        self.rates = np.array([planar, planar, sim.speed[1], sim.speed[-1], sim.speed[3]])
        self.max_intervals = base.dwell
        # Maximum Cartesian exploration spans one square per longest action.
        # Joint velocity limits and the independent sweep still apply.
        pitch = sim.manifest['scene']['square_size_m']
        self.rates[:3] = np.minimum(self.rates[:3], pitch/(self.max_intervals*sim.dt))
        selected = model.body(base.config['piece']).id
        self.selected = selected
        geoms = [g for g in base.collision.environment if model.geom_bodyid[g] == selected]
        others = [g for g in base.collision.environment if model.geom_bodyid[g] != selected]
        self.pairs = base.collision.pairs+[(a, b) for a in geoms for b in others]
        pads = [model.geom(f'finger_{index}_pad').id for index in (1, 2)]
        supports = [g for g in others if (model.geom(g).name == 'board_frame'
                    or model.geom(g).name.startswith('graveyard_support_'))]
        self.allowed = [(a, b) for a in geoms for b in (*pads, *supports)]
        self.checked_pairs = {frozenset(pair) for pair in self.pairs}
        self.allowed_pairs = {frozenset(pair) for pair in self.allowed}
        self.pad_ids = pads
        self.checker = SweptChecker(model, sim.data.qpos, sim.joint_ids, self.pairs)

    def commanded_tcp(self, command):
        self.scratch.qpos[:] = self.model.qpos0
        self.scratch.qpos[self.sim.qadr] = command
        mujoco.mj_forward(self.model, self.scratch)
        return self.scratch.site_xpos[self.site].copy()

    def decode(self, action, command):
        action = np.asarray(action, dtype=float)
        if action.shape != (7,) or not np.isfinite(action).all() or np.any(abs(action) > 1):
            raise ValueError('Expected seven finite normalized controls')
        intervals = 1+int(np.floor((action[6]+1)*.5*(self.max_intervals-1)+.5))
        duration = intervals*self.sim.dt
        xyz = self.commanded_tcp(command)+action[:3]*self.rates[:3]*duration
        wrist = np.clip(command[-1]+action[3]*self.rates[3]*duration,
                        self.sim.lower[-1], self.sim.upper[-1])
        opening = np.clip(command[3]+action[4]*self.rates[4]*duration,
                          self.sim.lower[3], self.sim.upper[3])
        elbow_down = (self.commanded_elbow_down(command) if abs(action[5]) < .5
                      else action[5] > 0)
        return MotionChoice(tuple(map(float, xyz)), float(wrist), float(opening),
                            bool(elbow_down), intervals, duration)

    def commanded_elbow_down(self, command):
        # Match the effective elbow angle used by native IK with a wrist offset.
        self.scratch.qpos[:] = self.model.qpos0
        self.scratch.qpos[self.sim.qadr] = 0.
        self.scratch.qpos[self.sim.qadr[-1]] = command[-1]
        mujoco.mj_forward(self.model, self.scratch)
        elbow = self.scratch.xanchor[self.sim.joint_ids[2]]
        offset = self.scratch.site_xpos[self.site]-elbow
        return command[2]+np.arctan2(offset[1], offset[0]) <= 0

    def validate(self, choice, command, *, project=False):
        sim = self.sim
        origin = self.commanded_tcp(command) if project else np.asarray(choice.xyz_m)
        displacement = np.asarray(choice.xyz_m)-origin
        for scale in ((1., .5, .25, .125, .0625) if project else (1.,)):
            xyz = origin+scale*displacement
            wrist = command[-1]+scale*(choice.wrist_rad-command[-1])
            opening = command[3]+scale*(choice.opening_m-command[3])
            try:
                end = sim.validate(self.base.motion.solve(
                    xyz, opening, wrist=wrist, elbow_down=choice.elbow_down))
            except ValueError as error:
                rejection = dict(status='IK_OR_LIMIT_REJECTED', reason=str(error))
                continue
            travel = np.max(abs(end-command)/sim.speed)
            if travel <= choice.duration_s+1e-8:
                break
            rejection = dict(status='VELOCITY_REJECTED', required_duration_s=float(travel))
        else:
            return None, rejection

        return self.sweep(end, scale)

    def sweep(self, end, scale):
        sim, model = self.sim, self.model
        checker = self.checker
        checker.initial[:] = sim.data.qpos
        checker.samples = 0
        # Bilateral hold is safety-only evidence. It determines the conservative
        # carried-object envelope and never enters the actor observation.
        held = all(any(contact.dist <= 0 and (
            contact.geom1 == pad and model.geom_bodyid[contact.geom2] == self.selected
            or contact.geom2 == pad and model.geom_bodyid[contact.geom1] == self.selected)
            for contact in sim.data.contact) for pad in self.pad_ids)
        configure = None
        coefficients = None
        if held:
            address = model.jnt_qposadr[model.body_jntadr[self.selected]]
            rotation = sim.data.site_xmat[self.site].reshape(3, 3)
            offset = rotation.T@(sim.data.xpos[self.selected]-sim.data.site_xpos[self.site])
            relative = rotation.T@sim.data.xmat[self.selected].reshape(3, 3)

            def configure(data):
                rot = data.site_xmat[self.site].reshape(3, 3)
                data.qpos[address:address+3] = data.site_xpos[self.site]+rot@offset
                mujoco.mju_mat2Quat(data.qpos[address+3:address+7], (rot@relative).reshape(-1))

            coefficients = checker.coefficients.copy()
            for geom in range(model.ngeom):
                if model.geom_bodyid[geom] == self.selected:
                    coefficients[geom] = np.max(coefficients[self.base.collision.robot], axis=0)
                    for index, joint in enumerate(sim.joint_ids):
                        if model.jnt_type[joint] == mujoco.mjtJoint.mjJNT_HINGE:
                            coefficients[geom, index] += 2*(np.linalg.norm(offset)+model.geom_rbound[geom])
        start = sim.data.qpos[sim.qadr].copy()
        failure = checker.interval(start, end, allowed=self.allowed,
                                   configure=configure, extra_coefficients=coefficients,
                                   prune_spheres=True)
        if failure:
            return None, dict(status='SWEEP_REJECTED', failure=failure, samples=checker.samples)
        return end, dict(status='ACCEPTED', samples=checker.samples, command_scale=scale,
                         joint_target=end.tolist(),
                         scope='nominal joint-linear sweep with simulated scene and rigid held-object approximation')

    def unexpected_contact(self):
        for contact in self.sim.data.contact:
            pair = frozenset((int(contact.geom1), int(contact.geom2)))
            if contact.dist <= 0 and pair in self.checked_pairs and pair not in self.allowed_pairs:
                return dict(geoms=[self.model.geom(int(geom)).name for geom in (contact.geom1, contact.geom2)],
                            distance_m=float(contact.dist))
        return None
