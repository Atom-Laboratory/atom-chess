from dataclasses import replace
import math

import pytest

from atom_mujoco.physical_state import (
    Location, Observation, PhysicalBoardState, Piece, Pose, Snapshot,
)
from atom_mujoco.supervision import Evidence, Execution, TaskLedger


def snapshot():
    # Synthetic state fixture, not calibrated scene geometry.
    squares = [f'{f}{r}' for r in '1278' for f in 'abcdefgh']
    return Snapshot(0, tuple(Piece(f'object-{i}', Pose((i*.04, 0., 0.), (1., 0., 0., 0.)),
                                  Location('board', square)) for i, square in enumerate(squares)),
                    frozenset({'slot-0', 'slot-1'}))


def moved(state, identity, location, pose=None):
    return replace(state, pieces=tuple(replace(p, location=location, pose=pose or p.pose)
                                       if p.identity == identity else p for p in state.pieces))


@pytest.fixture
def store():
    return PhysicalBoardState(snapshot(), position_tolerance_m=.001, angle_tolerance_rad=.01)


@pytest.fixture
def ledger(tmp_path):
    value = TaskLedger(tmp_path/'tasks.sqlite')
    yield value
    value.close()


def start(store, identifier='move-1', source='e2', target='e3'):
    task = store.request_move(source, target, operation_id=identifier,
                              expected_revision=store.confirmed.revision, timeout_s=60.)
    assert store.operations[identifier].status == 'pending'
    store.start(identifier)
    return task


def complete(task, ledger):
    execution = Execution(task, ledger, now_s=0., max_age_s=1., allow_oracle=True)
    for i, (source, signals) in enumerate(Execution.GATES.values(), 1):
        execution.advance(Evidence('simulation_oracle:'+source, float(i), i,
                                   frozenset(signals), task.expected_board_revision), now_s=float(i))
    assert execution.state == 'COMPLETED'
    return execution


def observe_target(store, task, execution, sequence=1):
    candidate = moved(store.confirmed, task.piece_id, Location('board', task.target_square),
                      Pose((.2, .3, .01), (1., 0., 0., 0.)))
    store.observe(Observation(task.task_id, sequence, execution.entered, candidate))
    return candidate


def test_square_resolution_and_verified_sequence(store, ledger):
    original = store.confirmed
    task = start(store)
    assert task.piece_id == original.occupancy['e2']
    assert len(original.occupancy) == 64
    assert store.confirmed is original
    held = moved(original, task.piece_id, Location('gripper'))
    store.observe(Observation(task.task_id, 0, 1., held))
    assert store.observation.snapshot.by_id[task.piece_id].location.kind == 'gripper'
    assert store.confirmed is original
    execution = complete(task, ledger)
    observe_target(store, task, execution)
    store.commit(task.task_id, execution, now_s=execution.entered)
    assert store.confirmed.occupancy['e2'] is None
    assert store.confirmed.occupancy['e3'] == task.piece_id
    assert store.confirmed.revision == 1
    assert store.operations[task.task_id].status == 'completed'
    task2 = start(store, 'move-2', 'e3', 'd4')
    assert task2.piece_id == task.piece_id
    execution2 = complete(task2, ledger)
    observe_target(store, task2, execution2, sequence=2)
    store.commit(task2.task_id, execution2, now_s=execution2.entered)
    assert store.confirmed.revision == 2
    assert store.confirmed.occupancy['d4'] == task.piece_id


@pytest.mark.parametrize('source,target,revision', [('e3','e4',0), ('e2','e7',0),
    ('e2','e2',0), ('E2','e3',0), ('i2','e3',0), ('e2','e3',1)])
def test_reject_invalid_requests_without_mutation(store, source, target, revision):
    original = store.confirmed
    with pytest.raises(ValueError):
        store.request_move(source, target, operation_id='bad', expected_revision=revision, timeout_s=60)
    assert store.confirmed is original
    assert not store.operations


def test_busy_duplicate_and_failure_block(store):
    original = store.confirmed
    task = start(store)
    with pytest.raises(ValueError, match='Busy'):
        start(store, 'other')
    store.fail(task.task_id, 'lost grip; stop requested, not confirmed')
    assert store.confirmed is original
    assert store.reconciliation_required
    assert store.operations[task.task_id].status == 'failed'
    with pytest.raises(ValueError, match='reconciliation'):
        start(store, 'next')


@pytest.mark.parametrize('fault', ['incomplete', 'wrong_task', 'stale', 'future',
    'wrong_target', 'other_pose', 'other_orientation', 'inventory', 'missing'])
def test_commit_requires_matching_feedback_and_full_state(store, ledger, fault):
    original = store.confirmed
    task = start(store)
    execution = complete(task, ledger)
    candidate = observe_target(store, task, execution)
    timestamp = execution.entered
    if fault == 'incomplete':
        execution.state = 'RELEASING'
    elif fault == 'wrong_task':
        execution.task = replace(task, task_id='unrelated')
    elif fault == 'stale':
        timestamp -= 2
    elif fault == 'future':
        timestamp += 1
    elif fault == 'wrong_target':
        candidate = original
    elif fault in ('other_pose', 'other_orientation'):
        other = candidate.pieces[0]
        pose = (Pose((1., 2., 3.), other.pose.orientation) if fault == 'other_pose'
                else Pose(other.pose.position, (0., 1., 0., 0.)))
        candidate = moved(candidate, other.identity, other.location, pose)
    elif fault == 'inventory':
        candidate = replace(candidate, pieces=(replace(candidate.pieces[0], identity='new'),)+candidate.pieces[1:])
    elif fault == 'missing':
        store._observation = None
    if fault != 'missing':
        store.observe(Observation(task.task_id, 2, timestamp, candidate))
    with pytest.raises(ValueError):
        store.commit(task.task_id, execution, now_s=execution.entered)
    assert store.confirmed is original
    assert store.reconciliation_required


def test_observation_order_and_revision(store):
    task = start(store)
    observation = Observation(task.task_id, 1, 0., store.confirmed)
    store.observe(observation)
    for invalid in (observation, replace(observation, sequence=2, operation_id='other'),
                    replace(observation, sequence=2, snapshot=replace(store.confirmed, revision=1))):
        with pytest.raises(ValueError):
            store.observe(invalid)
    assert store.observation is observation


def test_snapshot_inventory_graveyard_and_immutability():
    original = snapshot()
    captured = moved(original, 'object-0', Location('graveyard', 'slot-0'))
    assert captured.occupancy['a1'] is None
    assert captured.by_id['object-0'].location.slot == 'slot-0'
    with pytest.raises(TypeError):
        captured.occupancy['a1'] = 'object-0'
    for invalid in (
        lambda: replace(original, pieces=original.pieces[:-1]),
        lambda: replace(original, pieces=(original.pieces[1],)+original.pieces[1:]),
        lambda: moved(original, 'object-0', Location('board', 'b1')),
        lambda: moved(original, 'object-0', Location('graveyard', 'unknown')),
        lambda: moved(moved(original, 'object-0', Location('gripper')), 'object-1', Location('gripper')),
        lambda: Pose((math.nan, 0, 0), (1, 0, 0, 0)),
        lambda: Pose((0, 0, 0), (2, 0, 0, 0)),
    ):
        with pytest.raises(ValueError):
            invalid()


def test_graveyard_and_quaternion_sign_preserved(store, ledger):
    initial = moved(store.confirmed, 'object-0', Location('graveyard', 'slot-0'))
    store = PhysicalBoardState(initial, position_tolerance_m=.001, angle_tolerance_rad=.01)
    task = start(store)
    execution = complete(task, ledger)
    candidate = observe_target(store, task, execution)
    other = candidate.by_id['object-0']
    candidate = moved(candidate, other.identity, other.location,
                      Pose(other.pose.position, (-1., 0., 0., 0.)))
    store.observe(Observation(task.task_id, 2, execution.entered, candidate))
    store.commit(task.task_id, execution, now_s=execution.entered)
    assert store.confirmed.by_id['object-0'].location.kind == 'graveyard'
    with pytest.raises(ValueError, match='already used'):
        start(store)
