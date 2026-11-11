"""M3 host/policy boundary. No physics, IK, actuation or reward access."""
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

from .autonomous_observation import VisualHistory
from .supervision import Execution, MoveTask


CONTRACT_VERSION = 1
LOCAL_PHASES = ('GRASPING', 'LIFTING')
ACTION_AXES = ('tcp_x_m', 'tcp_y_m', 'tcp_z_m', 'wrist_rad', 'finger_travel_m')


def vector(value, count, name):
    result = np.asarray(value, dtype=float)
    if result.shape != (count,) or not np.isfinite(result).all():
        raise ValueError(f'{name}: expected {count} finite values')
    return tuple(float(item) for item in result)


@dataclass(frozen=True)
class LocalLimits:
    """Host-supplied static limits, with separate workspace qualification evidence."""
    command_lower: tuple
    command_upper: tuple
    local_lower: tuple
    local_upper: tuple
    rates: tuple
    control_dt_s: float
    workspace_evidence_id: str

    def __post_init__(self):
        for name, count in (('command_lower', 6), ('command_upper', 6),
                            ('local_lower', 5), ('local_upper', 5), ('rates', 5)):
            object.__setattr__(self, name, vector(getattr(self, name), count, name))
        if (np.any(np.array(self.command_lower) >= self.command_upper)
                or np.any(np.array(self.local_lower) >= self.local_upper)
                or np.any(np.array(self.rates) <= 0)):
            raise ValueError('Strictly ordered limits and positive rates required')
        if not np.isfinite(self.control_dt_s) or self.control_dt_s <= 0:
            raise ValueError('Positive finite control interval required')
        if not isinstance(self.workspace_evidence_id, str) or not self.workspace_evidence_id.strip():
            raise ValueError('Workspace evidence identity required')
        # A single opening coordinate must be valid for both coupled fingers.
        if self.command_lower[3] != self.command_lower[4] or self.command_upper[3] != self.command_upper[4]:
            raise ValueError('Coupled finger limits must match')
        if (self.local_lower[3] < self.command_lower[5] or self.local_upper[3] > self.command_upper[5]
                or self.local_lower[4] < self.command_lower[3] or self.local_upper[4] > self.command_upper[3]):
            raise ValueError('Local wrist/opening envelope exceeds actuator limits')

    def command(self, command):
        value = np.asarray(vector(command, 6, 'command'))
        if np.any(value < self.command_lower) or np.any(value > self.command_upper):
            raise ValueError('Command exceeds static limits')
        if not np.isclose(value[3], value[4], atol=1e-10, rtol=0):
            raise ValueError('Coupled finger targets must match')
        return value


class LocalObservations:
    """Allowed inputs only; an output copy has no handles to a live scene."""
    def __init__(self, task, limits, *, kind, color, camera_id, reference_sha256, max_age_s):
        if not isinstance(task, MoveTask):
            raise ValueError('Existing MoveTask required')
        if not isinstance(limits, LocalLimits):
            raise ValueError('Validated LocalLimits required')
        task.validate()
        kinds = ('pawn', 'knight', 'bishop', 'rook', 'queen', 'king')
        if kind not in kinds or color not in ('white', 'black'):
            raise ValueError('Logical piece kind/color required')
        if not camera_id or not reference_sha256 or not np.isfinite(max_age_s) or max_age_s <= 0:
            raise ValueError('Camera identity, reference and positive maximum age required')
        self.task, self.limits = task, limits
        self.camera_id, self.reference = camera_id, reference_sha256
        self.max_age = max_age_s
        self.history = VisualHistory()
        self.sequence = -1
        self.context = np.zeros(8, dtype=np.float32)
        self.context[kinds.index(kind)] = 1.
        self.context[6+(color == 'black')] = 1.

    def build(self, frame, *, command, previous_action, visual_source_xy_m, phase, now_s):
        if phase not in LOCAL_PHASES:
            raise ValueError('Expected GRASPING or LIFTING observation phase')
        if (not np.isfinite([now_s, frame.captured_at_s]).all()
                or not 0 <= now_s-frame.captured_at_s <= self.max_age):
            raise ValueError('Fresh camera frame required')
        if (not frame.oriented or frame.camera_id != self.camera_id
                or frame.reference_sha256 != self.reference or frame.homography is None
                or np.asarray(frame.homography).shape != (3, 3)
                or not np.isfinite(frame.homography).all()
                or abs(np.linalg.det(frame.homography)) == 0):
            raise ValueError('Matching oriented camera reference required')
        if type(frame.sequence) is not int or frame.sequence <= self.sequence:
            raise ValueError('New camera sequence required')
        rgb = frame.rectified_rgb
        if (not isinstance(rgb, np.ndarray) or rgb.dtype != np.uint8 or rgb.ndim != 3
                or rgb.shape[2] != 3 or min(rgb.shape[:2]) < 27):
            raise ValueError('Rectified uint8 RGB required')
        issued = self.limits.command(command)
        previous = np.asarray(vector(previous_action, 5, 'previous action'))
        if np.any(abs(previous) > 1):
            raise ValueError('Previous action exceeds normalized bounds')
        source = np.asarray(vector(visual_source_xy_m, 2, 'visual source'), dtype=np.float32)
        if not np.isfinite(source).all():
            raise ValueError('Visual source exceeds float32 representation')
        normalized = 2*(issued-self.limits.command_lower)/(np.array(self.limits.command_upper)-self.limits.command_lower)-1
        observation = self.history.observe(frame, normalized, previous, self.task.source_square, self.task.target_square)
        observation.update(visual_source_xy_m=source, object_context=self.context.copy(),
                           phase=np.eye(2, dtype=np.float32)[LOCAL_PHASES.index(phase)])
        self.sequence = frame.sequence
        # Byte backing prevents a caller from re-enabling the NumPy write flag.
        return MappingProxyType({key: np.frombuffer(value.tobytes(), dtype=value.dtype).reshape(value.shape)
                                 for key, value in observation.items()})


@dataclass(frozen=True)
class ApproachAdmission:
    """Assertions from future qualification adapters; not proof of their truth."""
    task_id: str
    board_revision: int
    model_identity: str
    camera_id: str
    reference_sha256: str
    workspace_evidence_id: str
    timestamp_s: float
    approach_complete: bool
    retreated: bool
    local_workspace_qualified: bool
    training_eligible: bool


@dataclass(frozen=True)
class LocalProposal:
    task_id: str
    lease_id: int
    sequence: int
    phase: str
    action: tuple

    def __post_init__(self):
        # Detach mutable policy output; numerical validation is a structured decision.
        object.__setattr__(self, 'action', tuple(self.action))


def decode_local_action(action, command, commanded_tcp_m, limits):
    """Only a bounded proposal. A PROPOSED result has not passed IK/collisions."""
    try:
        value = np.asarray(vector(action, 5, 'action'))
        issued = limits.command(command)
        tcp = vector(commanded_tcp_m, 3, 'commanded TCP')
    except (ValueError, TypeError) as error:
        return dict(status='REJECTED', category='INVALID_INPUT', detail=str(error))
    if np.any(abs(value) > 1):
        return dict(status='REJECTED', category='ACTION_BOUNDS')
    start = np.array([*tcp, issued[-1], issued[3]])
    endpoint = start+value*np.asarray(limits.rates)*limits.control_dt_s
    if np.any(start < limits.local_lower) or np.any(start > limits.local_upper):
        return dict(status='REJECTED', category='START_OUTSIDE_LOCAL_ENVELOPE')
    if np.any(endpoint < limits.local_lower) or np.any(endpoint > limits.local_upper):
        return dict(status='REJECTED', category='LOCAL_ENVELOPE_BOUNDS', endpoint=endpoint.tolist())
    return dict(status='PROPOSED', category='REQUIRES_IK_AND_SWEPT_CHECK',
                start=start.tolist(), endpoint=endpoint.tolist(), duration_s=limits.control_dt_s,
                transformation='none', contract_version=CONTRACT_VERSION)


class LocalHandoff:
    """Lease ownership over existing Execution phases; never advances global state."""
    def __init__(self, execution, limits, *, model_identity, camera_id, reference_sha256):
        if not isinstance(execution, Execution) or not isinstance(limits, LocalLimits):
            raise ValueError('Existing Execution and validated LocalLimits required')
        if not model_identity or not camera_id or not reference_sha256:
            raise ValueError('Model and camera/reference identities required')
        self.execution, self.limits = execution, limits
        self.model_identity, self.camera_id, self.reference = model_identity, camera_id, reference_sha256
        self.lease_id = 0
        self.active = False
        self.last_sequence = -1
        self.last_time = execution.last_time

    @property
    def owner(self):
        state = self.execution.state
        if state in LOCAL_PHASES:
            return 'RL' if self.active else 'SUPERVISOR'
        if state in ('PLANNING', 'APPROACHING', 'TRANSPORTING', 'PLACING', 'RELEASING'):
            return 'PLANNER'
        return 'SUPERVISOR'

    def authorize(self, admission, *, now_s):
        execution = self.execution
        reason = None
        if self.active:
            reason = 'LEASE_ALREADY_ACTIVE'
        elif not isinstance(admission, ApproachAdmission):
            reason = 'QUALIFICATION_REQUIRED'
        elif execution.allow_oracle:
            reason = 'CAMERA_ONLY_EVIDENCE_REQUIRED'
        elif execution.state != 'GRASPING':
            reason = 'PHASE_NOT_AUTHORIZED'
        elif (admission.task_id != execution.task.task_id or type(admission.board_revision) is not int
                or admission.board_revision != execution.task.expected_board_revision):
            reason = 'TASK_OR_BOARD_MISMATCH'
        elif (admission.model_identity != self.model_identity or admission.camera_id != self.camera_id
                or admission.reference_sha256 != self.reference
                or admission.workspace_evidence_id != self.limits.workspace_evidence_id):
            reason = 'QUALIFICATION_IDENTITY_MISMATCH'
        elif (not np.isfinite([now_s, admission.timestamp_s]).all()
                or not 0 <= now_s-admission.timestamp_s <= execution.max_age
                or now_s < max(self.last_time, execution.last_time)
                or now_s-execution.started >= execution.task.timeout_s):
            reason = 'QUALIFICATION_STALE_OR_TIMED_OUT'
        elif admission.approach_complete is not True or admission.retreated is not False:
            reason = 'CURRENT_APPROACH_REQUIRED'
        elif admission.local_workspace_qualified is not True or admission.training_eligible is not True:
            reason = 'LOCAL_WORKSPACE_NOT_QUALIFIED'
        if reason:
            return dict(status='REJECTED', category=reason)
        self.lease_id += 1
        self.active, self.last_sequence = True, -1
        self.last_time = now_s
        return dict(status='LEASE_GRANTED', lease_id=self.lease_id, contract_version=CONTRACT_VERSION)

    def revoke(self, reason):
        self.active = False
        return dict(status='REVOKED', category=reason)

    def propose(self, proposal, *, command, commanded_tcp_m, camera_id, reference_sha256, now_s):
        execution = self.execution
        if (not np.isfinite(now_s) or now_s < max(self.last_time, execution.last_time)
                or now_s-execution.started >= execution.task.timeout_s):
            return self.revoke('CLOCK_OR_TASK_TIMEOUT')
        self.last_time = now_s
        if camera_id != self.camera_id or reference_sha256 != self.reference:
            return self.revoke('PERCEPTION_REFERENCE_CHANGED')
        if not self.active or self.owner != 'RL':
            return dict(status='REJECTED', category='POLICY_NOT_OWNER')
        if not isinstance(proposal, LocalProposal):
            return dict(status='REJECTED', category='PROPOSAL_REQUIRED')
        if (proposal.task_id != execution.task.task_id or type(proposal.lease_id) is not int
                or proposal.lease_id != self.lease_id or proposal.phase != execution.state):
            return dict(status='REJECTED', category='PROPOSAL_CONTEXT_MISMATCH')
        if type(proposal.sequence) is not int or proposal.sequence <= self.last_sequence:
            return dict(status='REJECTED', category='PROPOSAL_REPLAY')
        self.last_sequence = proposal.sequence
        return decode_local_action(proposal.action, command, commanded_tcp_m, self.limits)
