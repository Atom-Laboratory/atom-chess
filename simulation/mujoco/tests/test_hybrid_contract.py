from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from atom_mujoco.hybrid_contract import (
    ApproachAdmission, LocalHandoff, LocalLimits, LocalObservations, LocalProposal, decode_local_action,
)
from atom_mujoco.supervision import Evidence, Execution, MoveTask, TaskLedger


@pytest.fixture
def limits():
    # Synthetic interface-test limits, not a physical workspace qualification.
    return LocalLimits((-2., -.1, -2., -.02, -.02, 0.), (2., .2, 4., 0., 0., 6.),
                       (.2, -.1, .02, 0., -.02), (.3, 0., .12, 6., 0.),
                       (.01, .01, .01, .1, .01), .02, 'synthetic-unit-test-only')


@pytest.fixture
def task():
    return MoveTask('move-1', 'pawn', 'e2', 'e4', 3, 10.)


def frame():
    return SimpleNamespace(sequence=1, captured_at_s=1., camera_id='side', reference_sha256='board',
        homography=np.eye(3), oriented=True, rectified_rgb=np.full((80, 80, 3), 120, dtype=np.uint8))


def observations(task, limits):
    return LocalObservations(task, limits, kind='pawn', color='white', camera_id='side',
                             reference_sha256='board', max_age_s=.5)


def observe(builder, rgb):
    return builder.build(rgb, command=[0., .1, -.5, -.01, -.01, 1.], previous_action=np.zeros(5),
                         visual_source_xy_m=[.25, -.05], phase='GRASPING', now_s=1.1)


def test_actor_inputs_independent_of_hidden_state(task, limits, sim):
    import mujoco

    first, second = frame(), frame()
    # Equal allowed camera/task inputs; radically different privileged state.
    first.hidden_simulator = {'piece_z': .02, 'contacts': [], 'reward': -100.}
    second.hidden_simulator = {'piece_z': 10., 'contacts': ['both'], 'reward': 1000.}
    a = observe(observations(task, limits), first)
    # Counterfactual: change the actual hidden physics while preserving the
    # same permitted camera/task/command inputs to the actor boundary.
    initial_qpos = sim.data.qpos.copy()
    sim.data.qpos[0] += .5
    sim.data.qvel[0] = 100.
    mujoco.mj_forward(sim.model, sim.data)
    assert not np.array_equal(initial_qpos, sim.data.qpos)
    b = observe(observations(task, limits), second)
    assert set(a) == {'image', 'task', 'commanded_joints', 'command_history', 'previous_action',
                      'perception_valid', 'visual_source_xy_m', 'object_context', 'phase'}
    for key in a:
        np.testing.assert_array_equal(a[key], b[key])
    assert a['image'].shape == (6, 96, 96)
    assert a['command_history'].shape == (12,)
    assert a['previous_action'].shape == (5,)


def test_observation_arrays_are_detached_and_immutable(task, limits):
    rgb = frame()
    result = observe(observations(task, limits), rgb)
    rgb.rectified_rgb[:] = 0
    assert result['image'].min() == 120
    for array in result.values():
        with pytest.raises(ValueError):
            array.setflags(write=True)
    with pytest.raises(TypeError):
        result['reward'] = np.ones(1)


@pytest.mark.parametrize('field,value,error', [
    ('camera_id', 'other', 'Matching oriented'), ('reference_sha256', 'other', 'Matching oriented'),
    ('oriented', False, 'Matching oriented'), ('captured_at_s', 0., 'Fresh camera'),
    ('captured_at_s', 2., 'Fresh camera'), ('homography', np.zeros((3, 3)), 'Matching oriented'),
])
def test_invalid_perception_does_not_advance_history(task, limits, field, value, error):
    builder, rgb = observations(task, limits), frame()
    setattr(rgb, field, value)
    with pytest.raises(ValueError, match=error):
        observe(builder, rgb)
    assert len(builder.history.images) == 0


def test_camera_replay_rejected(task, limits):
    builder = observations(task, limits)
    observe(builder, frame())
    with pytest.raises(ValueError, match='New camera sequence'):
        observe(builder, frame())


def test_local_decode_is_bounded_and_never_clips(limits):
    command = [0., .1, -.5, -.01, -.01, 1.]
    result = decode_local_action([1., -1., 1., 1., -1.], command, [.25, -.05, .06], limits)
    assert result['status'] == 'PROPOSED'
    assert result['category'] == 'REQUIRES_IK_AND_SWEPT_CHECK'
    assert result['endpoint'] == pytest.approx([.2502, -.0502, .0602, 1.002, -.0102])
    assert result['transformation'] == 'none'
    result = decode_local_action([2., 0., 0., 0., 0.], command, [.25, -.05, .06], limits)
    assert result['category'] == 'ACTION_BOUNDS'
    result = decode_local_action([1., 0., 0., 0., 0.], command, [.3, -.05, .06], limits)
    assert result['category'] == 'LOCAL_ENVELOPE_BOUNDS'


@pytest.mark.parametrize('action', [[0.]*7, [0.]*4, [float('nan')]*5, [float('inf')]*5])
def test_incompatible_or_nonfinite_policy_action_rejected(limits, action):
    result = decode_local_action(action, [0., .1, -.5, -.01, -.01, 1.], [.25, -.05, .06], limits)
    assert result['category'] == 'INVALID_INPUT'


@pytest.fixture
def execution(tmp_path, task):
    ledger = TaskLedger(tmp_path/'tasks.sqlite')
    execution = Execution(task, ledger, now_s=0., max_age_s=.5)
    for sequence, (source, signals) in enumerate([
        ('board', {'preconditions_valid'}), ('planner', {'plan_valid'}), ('robot', {'approach_settled'}),
    ]):
        execution.advance(Evidence(source, sequence*.1, sequence, frozenset(signals), 3), now_s=sequence*.1)
    assert execution.state == 'GRASPING'
    yield execution
    ledger.close()


def handoff(execution, limits):
    return LocalHandoff(execution, limits, model_identity='model', camera_id='side', reference_sha256='board')


def admission():
    # Assertions exercise interface gates, not evidence of a real safe workspace.
    return ApproachAdmission('move-1', 3, 'model', 'side', 'board', 'synthetic-unit-test-only',
                             .3, True, False, True, True)


@pytest.mark.parametrize('changes,reason', [
    ({'local_workspace_qualified': False, 'training_eligible': False}, 'LOCAL_WORKSPACE_NOT_QUALIFIED'),
    ({'retreated': True}, 'CURRENT_APPROACH_REQUIRED'),
    ({'approach_complete': False}, 'CURRENT_APPROACH_REQUIRED'),
    ({'task_id': 'other'}, 'TASK_OR_BOARD_MISMATCH'),
    ({'board_revision': 2}, 'TASK_OR_BOARD_MISMATCH'),
    ({'reference_sha256': 'other'}, 'QUALIFICATION_IDENTITY_MISMATCH'),
    ({'model_identity': 'other'}, 'QUALIFICATION_IDENTITY_MISMATCH'),
    ({'timestamp_s': -1.}, 'QUALIFICATION_STALE_OR_TIMED_OUT'),
])
def test_handoff_requires_current_qualified_workspace(execution, limits, changes, reason):
    gate = handoff(execution, limits)
    assert gate.authorize(replace(admission(), **changes), now_s=.3)['category'] == reason
    assert gate.owner == 'SUPERVISOR'
    assert execution.state == 'GRASPING'


def test_lease_follows_existing_execution_and_rejects_replay(execution, limits):
    gate = handoff(execution, limits)
    result = gate.authorize(admission(), now_s=.3)
    assert result['status'] == 'LEASE_GRANTED' and gate.owner == 'RL'
    proposal = LocalProposal('move-1', result['lease_id'], 1, 'GRASPING', np.zeros(5))
    kwargs = dict(command=[0., .1, -.5, -.01, -.01, 1.], commanded_tcp_m=[.25, -.05, .06],
                  camera_id='side', reference_sha256='board', now_s=.31)
    assert gate.propose(proposal, **kwargs)['status'] == 'PROPOSED'
    assert gate.propose(proposal, **kwargs)['category'] == 'PROPOSAL_REPLAY'
    # Only the existing global evidence machine advances the operation.
    execution.advance(Evidence('controller', .32, 1, frozenset({'close_acknowledged'}), 3), now_s=.32)
    assert execution.state == 'VERIFYING_GRASP' and gate.owner == 'SUPERVISOR'
    kwargs['now_s'] = .33
    assert gate.propose(replace(proposal, sequence=2), **kwargs)['category'] == 'POLICY_NOT_OWNER'
    execution.advance(Evidence('grip', .34, 1, frozenset({'contact', 'piece_stable'}), 3), now_s=.34)
    assert execution.state == 'LIFTING' and gate.owner == 'RL'
    kwargs['now_s'] = .35
    assert gate.propose(replace(proposal, sequence=2, phase='LIFTING'), **kwargs)['status'] == 'PROPOSED'
    execution.advance(Evidence('robot', .36, 3, frozenset({'lift_confirmed', 'grip_stable'}), 3), now_s=.36)
    assert execution.state == 'TRANSPORTING' and gate.owner == 'PLANNER'


@pytest.mark.parametrize('oracle,expected', [(True, 'CAMERA_ONLY_EVIDENCE_REQUIRED'), (False, 'LEASE_GRANTED')])
def test_oracle_enabled_execution_cannot_get_camera_lease(execution, limits, oracle, expected):
    execution.allow_oracle = oracle
    result = handoff(execution, limits).authorize(admission(), now_s=.3)
    assert result.get('category', result['status']) == expected


def test_reference_change_revokes_ownership(execution, limits):
    gate = handoff(execution, limits)
    gate.authorize(admission(), now_s=.3)
    result = gate.propose(LocalProposal('move-1', 1, 1, 'GRASPING', [0.]*5), command=[0.]*6,
        commanded_tcp_m=[0.]*3, camera_id='other', reference_sha256='board', now_s=.31)
    assert result['status'] == 'REVOKED' and gate.owner == 'SUPERVISOR'


def test_limits_are_immutable_and_reject_unbounded_setup(limits):
    with pytest.raises(ValueError, match='Positive finite'):
        replace(limits, control_dt_s=0.)
    with pytest.raises(ValueError, match='Coupled finger limits'):
        replace(limits, command_lower=(-2., -.1, -2., -.02, -.01, 0.))
    with pytest.raises(ValueError, match='Local wrist/opening'):
        replace(limits, local_upper=(.3, 0., .12, 7., 0.))


@pytest.mark.parametrize('changes,category', [
    ({'lease_id': 2}, 'PROPOSAL_CONTEXT_MISMATCH'),
    ({'task_id': 'other'}, 'PROPOSAL_CONTEXT_MISMATCH'),
    ({'phase': 'TRANSPORTING'}, 'PROPOSAL_CONTEXT_MISMATCH'),
    ({'sequence': True}, 'PROPOSAL_REPLAY'),
])
def test_proposal_cannot_change_lease_task_or_phase(execution, limits, changes, category):
    gate = handoff(execution, limits)
    gate.authorize(admission(), now_s=.3)
    proposal = replace(LocalProposal('move-1', 1, 1, 'GRASPING', [0.]*5), **changes)
    result = gate.propose(proposal, command=[0., .1, -.5, -.01, -.01, 1.],
        commanded_tcp_m=[.25, -.05, .06], camera_id='side', reference_sha256='board', now_s=.31)
    assert result['category'] == category


@pytest.mark.parametrize('clock', [.29, 11., float('nan')])
def test_clock_or_timeout_revokes_lease(execution, limits, clock):
    gate = handoff(execution, limits)
    gate.authorize(admission(), now_s=.3)
    result = gate.propose(LocalProposal('move-1', 1, 1, 'GRASPING', [0.]*5), command=[0.]*6,
        commanded_tcp_m=[0.]*3, camera_id='side', reference_sha256='board', now_s=clock)
    assert result['category'] == 'CLOCK_OR_TASK_TIMEOUT' and gate.owner == 'SUPERVISOR'
