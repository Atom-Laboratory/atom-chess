import pytest

from atom_mujoco.supervision import Evidence, Execution, MoveTask, TaskLedger


def task():
    return MoveTask('one', 'pawn', 'e2', 'e4', 42, 30.)


def test_success_requires_all_ordered_gates_and_independent_board(tmp_path):
    ledger = TaskLedger(tmp_path/'ledger.db')
    execution = Execution(task(), ledger, now_s=0, max_age_s=.5)
    sequence = 0
    while execution.state != 'COMPLETED':
        source, signals = execution.GATES[execution.state]
        sequence += 1
        now = sequence*.1
        previous = execution.state
        execution.advance(Evidence('controller', now, sequence, frozenset({'done'}), 42), now_s=now)
        assert execution.state == previous
        execution.advance(Evidence(source, now, sequence+100, frozenset(signals), 42), now_s=now)
        assert execution.state != previous
    assert ledger.accept(task())[0] == 'COMPLETED'
    ledger.close()


def test_stale_oracle_future_and_revision_conflict(tmp_path):
    ledger = TaskLedger(tmp_path/'ledger.db')
    execution = Execution(task(), ledger, now_s=1, max_age_s=.5)
    for source, timestamp in [('board', 0.), ('board', 3.), ('simulation_oracle:board', 1.)]:
        execution.advance(Evidence(source, timestamp, 1, frozenset({'preconditions_valid'}), 42), now_s=1.)
        assert execution.state == 'VALIDATING'
    assert execution.advance(Evidence('board', 1., 2, frozenset({'preconditions_valid'}), 99), now_s=1.) == 'FAILED'
    ledger.close()


def test_duplicates_restart_cancel_and_timeout(tmp_path):
    path = tmp_path/'ledger.db'
    ledger = TaskLedger(path)
    first = Execution(task(), ledger, now_s=0, max_age_s=1)
    duplicate = Execution(task(), ledger, now_s=0, max_age_s=1)
    assert not duplicate.reconciled
    with pytest.raises(ValueError, match='conflict'):
        ledger.accept(MoveTask('one', 'pawn', 'e2', 'e3', 42, 30.))
    assert first.abort('cancelled') == first.abort('cancelled') == 'ABORTED'
    ledger.close()
    ledger = TaskLedger(path)
    assert Execution(task(), ledger, now_s=0, max_age_s=1).state == 'ABORTED'
    another = MoveTask('two', 'pawn', 'e2', 'e4', 42, 1.)
    timed = Execution(another, ledger, now_s=0, max_age_s=1)
    assert timed.advance(None, now_s=1.) == 'ABORTED'
    ledger.close()
