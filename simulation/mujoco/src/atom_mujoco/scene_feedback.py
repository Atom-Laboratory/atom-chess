"""MuJoCo oracle adapter. Thresholds describe experimental verification only."""
from dataclasses import dataclass
import math

import numpy as np

from .physical_state import Location, Piece, Pose, Snapshot, SQUARES


@dataclass(frozen=True)
class FeedbackLimits:
    square_radius_m: float = .012
    support_height_error_m: float = .004
    upright_angle_rad: float = .15
    linear_speed_m_s: float = .01
    angular_speed_rad_s: float = .15
    bystander_position_m: float = .003
    bystander_angle_rad: float = .15


class SceneFeedback:
    def __init__(self, sim, limits=None):
        self.sim = sim
        self.limits = limits or FeedbackLimits()

    def snapshot(self, revision, *, held_id=None):
        sim, limits = self.sim, self.limits
        sites = {s: sim.data.site_xpos[sim.model.site('square_center_'+s).id] for s in SQUARES}
        # Interactive board collider, not decorative square surfaces, supports pieces.
        board = sim.model.geom('board_frame').id
        surface = sim.data.geom_xpos[board, 2] + sim.model.geom_size[board, 2]
        pieces = []
        for record in sim.manifest['pieces']:
            identity = record['name']
            body = sim.model.body(identity).id
            position = sim.data.xpos[body]
            pose = Pose(tuple(position), tuple(sim.data.xquat[body]))
            if identity == held_id:
                location = Location('gripper')
            else:
                matches = [s for s, center in sites.items()
                           if np.linalg.norm(position[:2]-center[:2]) <= limits.square_radius_m]
                if len(matches) != 1:
                    raise ValueError(f'AMBIGUOUS_LOCATION: {identity}')
                dof = sim.model.jnt_dofadr[sim.model.body_jntadr[body]]
                velocity = sim.data.qvel[dof:dof+6]
                upright = math.acos(float(np.clip(sim.data.xmat[body].reshape(3,3)[2,2], -1, 1)))
                if (abs(position[2]-surface) > limits.support_height_error_m
                        or upright > limits.upright_angle_rad
                        or np.linalg.norm(velocity[:3]) > limits.linear_speed_m_s
                        or np.linalg.norm(velocity[3:]) > limits.angular_speed_rad_s):
                    raise ValueError(f'UNSETTLED_OR_UNSUPPORTED: {identity}')
                location = Location('board', matches[0])
            pieces.append(Piece(identity, pose, location))
        return Snapshot(revision, tuple(pieces))

    def grip_contacts(self, identity):
        sim = self.sim
        body = sim.model.body(identity).id
        pads = [sim.model.geom(f'finger_{i}_pad').id for i in (1, 2)]
        return all(any((c.geom1 == pad and sim.model.geom_bodyid[c.geom2] == body)
                       or (c.geom2 == pad and sim.model.geom_bodyid[c.geom1] == body)
                       for c in sim.data.contact) for pad in pads)

    def settled(self, identity):
        sim = self.sim
        body = sim.model.body(identity).id
        dof = sim.model.jnt_dofadr[sim.model.body_jntadr[body]]
        velocity = sim.data.qvel[dof:dof+6]
        return (np.linalg.norm(velocity[:3]) <= self.limits.linear_speed_m_s
                and np.linalg.norm(velocity[3:]) <= self.limits.angular_speed_rad_s)

    def released(self, identity):
        sim = self.sim
        body = sim.model.body(identity).id
        pads = {sim.model.geom(f'finger_{i}_pad').id for i in (1, 2)}
        return not any((c.geom1 in pads and sim.model.geom_bodyid[c.geom2] == body)
                       or (c.geom2 in pads and sim.model.geom_bodyid[c.geom1] == body)
                       for c in sim.data.contact)
