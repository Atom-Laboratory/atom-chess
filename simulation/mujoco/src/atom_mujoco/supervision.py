"""Transport-independent task verification. No motor transport or board mutation."""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import sqlite3


STATES = ('VALIDATING', 'PLANNING', 'APPROACHING', 'GRASPING', 'VERIFYING_GRASP',
          'LIFTING', 'TRANSPORTING', 'PLACING', 'VERIFYING_PLACEMENT',
          'RELEASING', 'VERIFYING_RELEASE', 'COMPLETED')
TERMINAL = {'COMPLETED', 'FAILED', 'ABORTED'}


@dataclass(frozen=True)
class MoveTask:
    task_id: str
    piece_id: str
    source_square: str
    target_square: str
    expected_board_revision: int
    timeout_s: float

    def validate(self):
        if not self.task_id or not self.piece_id:
            raise ValueError('Identifiers are required')
        for square in (self.source_square, self.target_square):
            if len(square) != 2 or square[0] not in 'abcdefgh' or square[1] not in '12345678':
                raise ValueError('Invalid square')
        if self.source_square == self.target_square:
            raise ValueError('Source and destination must differ')
        if not math.isfinite(self.timeout_s) or self.timeout_s <= 0:
            raise ValueError('Positive finite timeout required')
        if type(self.expected_board_revision) is not int or self.expected_board_revision < 0:
            raise ValueError('Invalid board revision')


@dataclass(frozen=True)
class Evidence:
    source: str
    timestamp_s: float
    sequence: int
    signals: frozenset[str]
    board_revision: int


class TaskLedger:
    """Durable duplicate protection. In-progress work is never automatically replayed."""
    def __init__(self, path):
        self.connection = sqlite3.connect(Path(path))
        self.connection.execute('CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, digest TEXT, state TEXT, detail TEXT)')
        self.connection.commit()

    def accept(self, task):
        task.validate()
        digest = hashlib.sha256(json.dumps(asdict(task), sort_keys=True).encode()).hexdigest()
        with self.connection:
            self.connection.execute('INSERT OR IGNORE INTO tasks VALUES (?, ?, ?, ?)',
                                    (task.task_id, digest, 'VALIDATING', 'accepted'))
        row = self.connection.execute('SELECT digest,state,detail FROM tasks WHERE id=?', (task.task_id,)).fetchone()
        if row[0] != digest:
            raise ValueError('Task ID payload conflict')
        return row[1:]

    def update(self, task_id, state, detail):
        with self.connection:
            self.connection.execute('UPDATE tasks SET state=?,detail=? WHERE id=?', (state, detail, task_id))

    def close(self):
        self.connection.close()

    def claim(self, task_id):
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE tasks SET detail='running: reconciliation required on restart' WHERE id=? AND detail='accepted'",
                (task_id,))
        return cursor.rowcount == 1


class Execution:
    """Explicit evidence gates; calling advance does not execute a robot command.

    Signal names are assertions supplied by adapters. This class verifies source,
    freshness and ordering, not the truth of arbitrary caller-provided assertions.
    """
    GATES = {
        'VALIDATING': ('board', {'preconditions_valid'}),
        'PLANNING': ('planner', {'plan_valid'}),
        'APPROACHING': ('robot', {'approach_settled'}),
        'GRASPING': ('controller', {'close_acknowledged'}),
        'VERIFYING_GRASP': ('grip', {'contact', 'piece_stable'}),
        'LIFTING': ('robot', {'lift_confirmed', 'grip_stable'}),
        'TRANSPORTING': ('robot', {'destination_reached', 'grip_stable'}),
        'PLACING': ('robot', {'placement_settled'}),
        'VERIFYING_PLACEMENT': ('grip', {'supported', 'aligned'}),
        'RELEASING': ('controller', {'open_acknowledged'}),
        'VERIFYING_RELEASE': ('board', {'released', 'whole_board_matches'}),
    }

    def __init__(self, task, ledger, *, now_s, max_age_s, allow_oracle=False):
        if not math.isfinite(now_s) or not math.isfinite(max_age_s) or max_age_s <= 0:
            raise ValueError('Invalid clock/freshness configuration')
        self.task, self.ledger = task, ledger
        self.state, self.detail = ledger.accept(task)
        self.started = self.entered = self.last_time = now_s
        self.max_age = max_age_s
        self.allow_oracle = allow_oracle
        self.sequences = {}
        self.reconciled = self.detail == 'accepted' and ledger.claim(task.task_id)
        # Persist immediately: another process/restart must not replay dispatch.

    def abort(self, reason):
        if self.state not in TERMINAL:
            self.state, self.detail = 'ABORTED', reason
            self.ledger.update(self.task.task_id, self.state, reason)
        return self.state

    def fault(self, reason):
        if self.state not in TERMINAL:
            # No verified recovery strategy/stop transport exists yet.
            self.state, self.detail = 'FAILED', 'intervention_required: '+reason
            self.ledger.update(self.task.task_id, self.state, self.detail)
        return self.state

    def advance(self, evidence, *, now_s):
        if self.state in TERMINAL:
            return self.state
        if not math.isfinite(now_s) or now_s < self.last_time:
            return self.abort('invalid_clock')
        self.last_time = now_s
        if now_s-self.started >= self.task.timeout_s:
            return self.abort('timeout')
        if not self.reconciled:
            return self.fault('restart_requires_physical_reconciliation')
        if not isinstance(evidence, Evidence):
            return self.fault('invalid_evidence')
        source, required = self.GATES[self.state]
        oracle = evidence.source == 'simulation_oracle:'+source
        if evidence.source != source and not (self.allow_oracle and oracle):
            return self.state
        if (not math.isfinite(evidence.timestamp_s) or evidence.timestamp_s < self.entered
                or not 0 <= now_s-evidence.timestamp_s <= self.max_age):
            return self.state
        if type(evidence.sequence) is not int or evidence.sequence <= self.sequences.get(evidence.source, -1):
            return self.state
        if evidence.board_revision != self.task.expected_board_revision:
            return self.fault('board_revision_conflict')
        self.sequences[evidence.source] = evidence.sequence
        if not required <= evidence.signals:
            return self.state
        self.state = STATES[STATES.index(self.state)+1]
        self.entered = now_s
        self.detail = 'verified_transition'
        self.ledger.update(self.task.task_id, self.state, self.detail)
        return self.state
