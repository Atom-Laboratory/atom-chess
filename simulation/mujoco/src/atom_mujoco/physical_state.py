"""Confirmed physical state; no chess rules, geometry inference or actuator IO."""
from dataclasses import dataclass, replace
import math
from types import MappingProxyType

from .supervision import Execution, MoveTask


SQUARES = tuple(f'{file}{rank}' for rank in '12345678' for file in 'abcdefgh')


def endpoint(value):
    if value in SQUARES:
        return Location('board', value)
    if isinstance(value, str) and value.startswith('graveyard:') and value[10:]:
        return Location('graveyard', value[10:])
    raise ValueError('Invalid transfer endpoint')


@dataclass(frozen=True)
class TransferTask(MoveTask):
    """P005-compatible physical task, with typed endpoint string encoding."""
    def validate(self):
        # Reuse identity/revision/timeout validation without pretending slots are squares.
        replace(MoveTask(self.task_id, self.piece_id, 'a1', 'a2',
                         self.expected_board_revision, self.timeout_s)).validate()
        if endpoint(self.source_square) == endpoint(self.target_square):
            raise ValueError('Transfer endpoints must differ')


@dataclass(frozen=True)
class Pose:
    """World-frame metres and unit quaternion in wxyz order."""
    position: tuple[float, float, float]
    orientation: tuple[float, float, float, float]

    def __post_init__(self):
        object.__setattr__(self, 'position', tuple(self.position))
        object.__setattr__(self, 'orientation', tuple(self.orientation))
        if (len(self.position) != 3 or len(self.orientation) != 4
                or not all(math.isfinite(v) for v in self.position + self.orientation)
                or not math.isclose(sum(v*v for v in self.orientation), 1., abs_tol=1e-6)):
            raise ValueError('Finite position and unit wxyz quaternion required')


@dataclass(frozen=True)
class Location:
    kind: str
    slot: str = ''

    def __post_init__(self):
        if not ((self.kind == 'board' and self.slot in SQUARES)
                or (self.kind == 'graveyard' and bool(self.slot))
                or (self.kind == 'gripper' and self.slot == '')):
            raise ValueError('Invalid physical location')


@dataclass(frozen=True)
class Piece:
    identity: str
    pose: Pose
    location: Location

    def __post_init__(self):
        if not self.identity or not isinstance(self.pose, Pose) or not isinstance(self.location, Location):
            raise ValueError('Identity, pose and location required')


@dataclass(frozen=True)
class Snapshot:
    revision: int
    pieces: tuple[Piece, ...]
    graveyard_slots: frozenset[str] = frozenset()

    def __post_init__(self):
        object.__setattr__(self, 'pieces', tuple(self.pieces))
        object.__setattr__(self, 'graveyard_slots', frozenset(self.graveyard_slots))
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError('Nonnegative integer revision required')
        if (len(self.pieces) != 32 or not all(isinstance(p, Piece) for p in self.pieces)
                or len({p.identity for p in self.pieces}) != 32):
            raise ValueError('Exactly 32 distinct physical pieces required')
        if any(not isinstance(s, str) or not s for s in self.graveyard_slots):
            raise ValueError('Invalid Graveyard slot')
        locations = [p.location for p in self.pieces]
        if len(set(locations)) != len(locations):
            raise ValueError('Multiple pieces occupy one location')
        if any(loc.kind == 'graveyard' and loc.slot not in self.graveyard_slots for loc in locations):
            raise ValueError('Unknown Graveyard slot')

    @property
    def occupancy(self):
        squares = dict.fromkeys(SQUARES)
        squares.update({p.location.slot: p.identity for p in self.pieces if p.location.kind == 'board'})
        return MappingProxyType(squares)

    @property
    def by_id(self):
        return MappingProxyType({p.identity: p for p in self.pieces})


@dataclass(frozen=True)
class Observation:
    operation_id: str
    sequence: int
    timestamp_s: float
    snapshot: Snapshot


@dataclass(frozen=True)
class Operation:
    task: MoveTask
    status: str = 'pending'
    detail: str = ''


class PhysicalBoardState:
    """Single-owner store. Adapters must serialize access and supply measured evidence.

    Failure blocks dispatch; it neither rolls back physics nor confirms a stop.
    Initialization must receive an externally verified full scene snapshot.
    """
    def __init__(self, snapshot, *, position_tolerance_m, angle_tolerance_rad):
        if not isinstance(snapshot, Snapshot):
            raise ValueError('Snapshot required')
        if (not math.isfinite(position_tolerance_m) or position_tolerance_m < 0
                or not math.isfinite(angle_tolerance_rad) or not 0 <= angle_tolerance_rad <= math.pi):
            raise ValueError('Explicit finite pose tolerances required')
        self._confirmed = snapshot
        self._operations = {}
        self._active = None
        self._blocked = False
        self._observation = None
        self._sequence = -1
        self._position_tolerance = position_tolerance_m
        self._angle_tolerance = angle_tolerance_rad

    @property
    def confirmed(self):
        return self._confirmed

    @property
    def operations(self):
        return MappingProxyType(self._operations)

    @property
    def observation(self):
        return self._observation

    @property
    def reconciliation_required(self):
        return self._blocked

    def request_move(self, source, target, *, operation_id, expected_revision, timeout_s):
        if source not in SQUARES or target not in SQUARES:
            raise ValueError('Canonical board squares required')
        return self.request_transfer(source, target, operation_id=operation_id,
                                     expected_revision=expected_revision, timeout_s=timeout_s)

    def request_transfer(self, source, target, *, operation_id, expected_revision, timeout_s):
        if self._blocked or self._active is not None:
            raise ValueError('Busy or reconciliation required')
        if operation_id in self._operations:
            raise ValueError('Operation ID already used; automatic replay prohibited')
        if type(expected_revision) is not int or expected_revision != self.confirmed.revision:
            raise ValueError('Physical revision conflict')
        source_location, target_location = endpoint(source), endpoint(target)
        if source_location == target_location:
            raise ValueError('Distinct source and target required')
        for location in (source_location, target_location):
            if location.kind == 'graveyard' and location.slot not in self.confirmed.graveyard_slots:
                raise ValueError('Unknown Graveyard slot')
        occupied = {p.location: p.identity for p in self.confirmed.pieces}
        identity = occupied.get(source_location)
        if identity is None or target_location in occupied:
            raise ValueError('Source empty or destination occupied; removal must precede transfer')
        if any(p.location.kind == 'gripper' for p in self.confirmed.pieces):
            raise ValueError('Gripper occupied; reconciliation required')
        task = TransferTask(operation_id, identity, source, target, expected_revision, timeout_s)
        task.validate()
        self._operations[operation_id] = Operation(task)
        self._active = operation_id
        return task

    def start(self, operation_id):
        operation = self._require(operation_id, 'pending')
        self._operations[operation_id] = replace(operation, status='executing')
        return operation.task

    def _require(self, operation_id, status):
        operation = self._operations.get(operation_id)
        if self._active != operation_id or operation is None or operation.status != status:
            raise ValueError('Operation is not in the required state')
        return operation

    def fail(self, operation_id, reason, *, reconciliation_required=True):
        if self._active != operation_id:
            raise ValueError('Operation is not active')
        self._operations[operation_id] = replace(self._operations[operation_id], status='failed', detail=reason)
        self._active = None
        self._blocked = self._blocked or reconciliation_required

    def invalidate(self):
        """External/manual manipulation makes the last confirmed state uncertain."""
        if self._active is not None:
            raise ValueError('An operation owns the physical state')
        self._blocked = True

    def observe(self, observation):
        self._require(observation.operation_id, 'executing')
        if (type(observation.sequence) is not int or observation.sequence <= self._sequence
                or not math.isfinite(observation.timestamp_s)
                or not isinstance(observation.snapshot, Snapshot)
                or observation.snapshot.revision != self.confirmed.revision):
            raise ValueError('Invalid, stale or conflicting observation')
        self._observation = observation
        self._sequence = observation.sequence

    def commit(self, operation_id, execution, *, now_s):
        operation = self._require(operation_id, 'executing')
        try:
            if (not isinstance(execution, Execution) or execution.task != operation.task
                    or execution.state != 'COMPLETED' or not execution.reconciled):
                raise ValueError('Matching completed supervised execution required')
            observation = self.observation
            if (observation is None or observation.operation_id != operation_id
                    or not math.isfinite(now_s) or now_s < execution.last_time
                    or observation.timestamp_s < execution.entered
                    or not 0 <= now_s-observation.timestamp_s <= execution.max_age):
                raise ValueError('Fresh post-release full observation required')
            self.verify_candidate(operation_id, observation.snapshot)
            self._confirmed = replace(observation.snapshot, revision=self.confirmed.revision+1)
            self._operations[operation_id] = replace(operation, status='completed')
            self._active = None
            return self.confirmed
        except ValueError as error:
            self.fail(operation_id, str(error))
            raise

    def verify_candidate(self, operation_id, candidate):
        """Check full-board evidence before asserting P005 whole_board_matches."""
        operation = self._require(operation_id, 'executing')
        previous = self.confirmed
        if (candidate.revision != previous.revision or candidate.by_id.keys() != previous.by_id.keys()
                or candidate.graveyard_slots != previous.graveyard_slots):
            raise ValueError('Physical inventory or revision changed')
        for identity, before in previous.by_id.items():
            after = candidate.by_id[identity]
            if identity == operation.task.piece_id:
                if after.location != endpoint(operation.task.target_square):
                    raise ValueError('Transferred piece not at destination')
            else:
                dot = abs(sum(a*b for a, b in zip(before.pose.orientation, after.pose.orientation)))
                angle = 2*math.acos(min(1., dot))
                if (after.location != before.location
                        or math.dist(before.pose.position, after.pose.position) > self._position_tolerance
                        or angle > self._angle_tolerance):
                    raise ValueError('Unaffected piece changed location or pose')
