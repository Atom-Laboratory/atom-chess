"""MuJoCo oracle adapter. Thresholds describe experimental verification only."""
from dataclasses import dataclass
import math
from types import MappingProxyType

import numpy as np
import mujoco

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


@dataclass(frozen=True)
class FeedbackObservation:
    operation_id: str
    sequence: int
    timestamp_s: float
    snapshot: Snapshot
    frames: object
    joints: object
    gripper: object


class SceneFeedback:
    def __init__(self, sim, limits=None):
        self.sim = sim
        self.limits = limits or FeedbackLimits()
        self._sequence = 0

    def snapshot(self, revision):
        sim, limits = self.sim, self.limits
        sites = {s: sim.data.site_xpos[sim.model.site('square_center_'+s).id] for s in SQUARES}
        # Interactive board collider, not decorative square surfaces, supports pieces.
        board = sim.model.geom('board_frame').id
        surface = sim.data.geom_xpos[board, 2] + sim.model.geom_size[board, 2]
        surfaces = {s: surface for s in SQUARES}
        graveyard = sim.manifest['scene'].get('graveyard_slots', {})
        for slot in graveyard:
            key = 'graveyard:'+slot
            sites[key] = sim.data.site_xpos[sim.model.site('graveyard_center_'+slot).id]
            surfaces[key] = sites[key][2]
        pieces = []
        for record in sim.manifest['pieces']:
            identity = record['name']
            body = sim.model.body(identity).id
            position = sim.data.xpos[body]
            pose = Pose(tuple(position), tuple(sim.data.xquat[body]))
            contacts = self.pad_contacts(identity)
            if contacts == (True, True) and self.settled(identity):
                location = Location('gripper')
            elif any(contacts):
                raise ValueError(f'PARTIAL_OR_MOVING_GRASP: {identity}')
            else:
                matches = [s for s, center in sites.items()
                           if np.linalg.norm(position[:2]-center[:2]) <= limits.square_radius_m]
                if len(matches) != 1:
                    raise ValueError(f'AMBIGUOUS_LOCATION: {identity}')
                dof = sim.model.jnt_dofadr[sim.model.body_jntadr[body]]
                velocity = sim.data.qvel[dof:dof+6]
                upright = math.acos(float(np.clip(sim.data.xmat[body].reshape(3,3)[2,2], -1, 1)))
                if (abs(position[2]-surfaces[matches[0]]) > limits.support_height_error_m
                        or upright > limits.upright_angle_rad
                        or np.linalg.norm(velocity[:3]) > limits.linear_speed_m_s
                        or np.linalg.norm(velocity[3:]) > limits.angular_speed_rad_s):
                    raise ValueError(f'UNSETTLED_OR_UNSUPPORTED: {identity}')
                location = (Location('graveyard', matches[0][10:]) if matches[0].startswith('graveyard:')
                            else Location('board', matches[0]))
            pieces.append(Piece(identity, pose, location))
        count = 2 if sim.manifest.get('fixture_kind') == 'two_piece_capture' else 32
        snapshot = Snapshot(revision, tuple(pieces), frozenset(graveyard), count)
        return snapshot

    def observation(self, operation_id, revision):
        """Bind an immutable full snapshot and robot/tool telemetry to one operation."""
        if not isinstance(operation_id, str) or not operation_id:
            raise ValueError('Operation identity required')
        snapshot = self.snapshot(revision)
        timestamp = float(self.sim.data.time)
        if not math.isfinite(timestamp):
            raise ValueError('Finite observation timestamp required')
        sim = self.sim
        if any(p.location.kind == 'gripper' for p in snapshot.pieces) and not self.grip_contacts(
                next(p.identity for p in snapshot.pieces if p.location.kind == 'gripper')):
            raise ValueError('HELD_STATE_UNVERIFIED')
        frames = {}
        for name in ('arm2_frame', 'grasp_center'):
            site = sim.model.site(name).id
            frames[name] = Pose(tuple(sim.data.site_xpos[site]), tuple(self._site_quaternion(site)))
        joints = MappingProxyType({name: float(sim.data.qpos[address])
                                   for name,address in zip(sim.names,sim.qadr)})
        gripper = MappingProxyType(dict(opening=tuple(float(v) for v in sim.data.qpos[sim.qadr[3:5]]),
                                         held_identity=next((p.identity for p in snapshot.pieces
                                                             if p.location.kind == 'gripper'), None)))
        self._sequence += 1
        return FeedbackObservation(operation_id, self._sequence, timestamp, snapshot,
                                   MappingProxyType(frames), joints, gripper)

    def _site_quaternion(self, site):
        quat = np.empty(4)
        mujoco.mju_mat2Quat(quat, self.sim.data.site_xmat[site])
        return quat

    def endpoint_position(self, endpoint):
        name = 'graveyard_center_'+endpoint[10:] if endpoint.startswith('graveyard:') else 'square_center_'+endpoint
        return self.sim.data.site_xpos[self.sim.model.site(name).id].copy()

    def pad_contacts(self, identity):
        sim = self.sim
        body = sim.model.body(identity).id
        pads = [sim.model.geom(f'finger_{i}_pad').id for i in (1, 2)]
        return tuple(any((c.geom1 == pad and sim.model.geom_bodyid[c.geom2] == body)
                       or (c.geom2 == pad and sim.model.geom_bodyid[c.geom1] == body)
                       for c in sim.data.contact) for pad in pads)

    def grip_contacts(self, identity):
        return all(self.pad_contacts(identity))

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
