import json
import os
from pathlib import Path
import time
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

import atom_mujoco.approach_handoff as handoff
import atom_mujoco.autonomous_env as autonomous
from atom_mujoco.autonomous_env import AutonomousManipulationEnv


@pytest.fixture
def inputs(monkeypatch):
    command = np.zeros(6)
    plan = dict(status='PLANNED', target_command=command.tolist(), target_tcp_m=[.25, .1, .08],
        source_xy_m=[.25, .1], camera_id='rgb', reference_sha256='reference',
        homography=np.eye(3).tolist(), derived_geometry=dict(clearance_m=.001))
    execution = dict(status='COMPLETED_SIMULATED_APPROACH', approach_complete=True,
        retreat_complete=False, motion_applied=True, reconciliation_required=False,
        tracking_tolerance=[.001]*6, fresh_frame_sequence=3,
        arrival=dict(position=[.0001]*6, tcp_m=[.25, .1, .0801], tcp_error_m=.0001))
    frame = SimpleNamespace(oriented=True, homography=np.eye(3), camera_id='rgb',
        reference_sha256='reference', sequence=4, captured_at_s=time.monotonic(),
        rectified_rgb=np.zeros((80, 80, 3), dtype=np.uint8))
    scene = SimpleNamespace(command=command, observe=Mock(return_value=frame),
        config=dict(source='e2', max_perception_age_s=10.), square_source=np.array([.25, .1, .02]),
        empty_reference=None, centered_reference=None, pitch=.035)
    planner = Mock()
    planner.return_value.plan.return_value = plan
    executor = Mock(return_value=execution)
    offsets = Mock(return_value={'e2': [0., 0.]})
    monkeypatch.setattr(handoff, 'ApproachPlanner', planner)
    monkeypatch.setattr(handoff, 'execute_approach', executor)
    monkeypatch.setattr(handoff, 'scene_square_offsets', offsets)
    return scene, frame, plan, execution, executor, offsets


def test_handoff_uses_executed_endpoint_and_new_frame(inputs):
    scene, frame, plan, _, executor, _ = inputs
    report = {}
    result, xy = handoff.approach_handoff(scene, report)
    executor.assert_called_once_with(scene, plan, retreat=False, observer=None)
    assert result is frame
    np.testing.assert_array_equal(xy, [.25, .1])
    assert report['endpoint']['joint_error'] == [.0001]*6
    assert report['validation']['live_sweep'] == 'ACCEPTED'


def test_rejected_plan_cannot_execute(inputs):
    scene, _, plan, _, executor, _ = inputs
    plan.update(status='REJECTED', reason='NO_VALID_CANDIDATE_IN_BOUNDED_FAMILY')
    report = {}
    with pytest.raises(RuntimeError, match=plan['reason']):
        handoff.approach_handoff(scene, report)
    assert report['stage'] == 'PLANNING'
    executor.assert_not_called()
    scene.observe.assert_not_called()


def test_handoff_requests_visual_screen_only_when_configured(inputs):
    scene, _, _, _, _, _ = inputs
    planner = handoff.ApproachPlanner.return_value
    handoff.approach_handoff(scene, {})
    planner.plan.assert_called_with(require_visible_target=False)
    scene.config['autonomous'] = {'require_visible_target': True}
    handoff.approach_handoff(scene, {})
    planner.plan.assert_called_with(require_visible_target=True)


def test_handoff_forwards_lateral_candidates_without_changing_piece_xy(inputs):
    scene, _, _, _, _, _ = inputs
    offsets = [[1., 0.], [-1., 0.]]
    scene.config['autonomous'] = dict(require_visible_target=True,
                                    approach_entry_offsets_squares=offsets)
    _, xy = handoff.approach_handoff(scene, {})
    handoff.ApproachPlanner.return_value.plan.assert_called_once_with(
        require_visible_target=True, entry_offsets_squares=offsets)
    np.testing.assert_array_equal(xy, [.25, .1])


def test_live_preflight_rejection_prevents_initial_observation(inputs):
    scene, _, _, execution, _, _ = inputs
    execution.update(status='REJECTED', approach_complete=False, motion_applied=False,
        preflight_failure={'phase': 'APPROACH'}, error='LIVE_SCENE_PREFLIGHT_REJECTED')
    report = {}
    with pytest.raises(RuntimeError, match='LIVE_SCENE_PREFLIGHT_REJECTED'):
        handoff.approach_handoff(scene, report)
    assert report['validation']['live_sweep'] == 'REJECTED'
    scene.observe.assert_not_called()


@pytest.mark.parametrize('change,category', [
    ('tracking', 'APPROACH_ENDPOINT_TRACKING_MISMATCH'),
    ('stale_sequence', 'FRESH_MATCHING_ARRIVAL_FRAME_REQUIRED'),
    ('reference', 'FRESH_MATCHING_ARRIVAL_FRAME_REQUIRED'),
    ('homography', 'ARRIVAL_BOARD_REFERENCE_CHANGED'),
    ('missing_target', 'ARRIVAL_TARGET_NOT_VISUALLY_LOCALIZED'),
    ('moved_target', 'ARRIVAL_TARGET_ESTIMATE_CHANGED'),
])
def test_unverified_arrival_is_rejected(inputs, change, category):
    scene, frame, _, execution, _, offsets = inputs
    if change == 'tracking':
        execution['arrival']['position'][0] = .02
    elif change == 'stale_sequence':
        frame.sequence = execution['fresh_frame_sequence']
    elif change == 'reference':
        frame.reference_sha256 = 'different-reference'
    elif change == 'homography':
        frame.homography[0, 2] = 10.
    elif change == 'missing_target':
        offsets.return_value = {}
    else:
        offsets.return_value = {'e2': [.01, 0.]}
    with pytest.raises(RuntimeError, match=category):
        handoff.approach_handoff(scene, {})


def test_reset_initializes_from_command_and_camera_after_execution(monkeypatch):
    env = AutonomousManipulationEnv.__new__(AutonomousManipulationEnv)
    frame = SimpleNamespace(sequence=3)
    env.native_approach, env.VERSION = True, 7
    env.action_space = SimpleNamespace(shape=(7,))
    env.objective, env.horizon = 'lift', 8
    env.approach_observer = None
    env.base = SimpleNamespace(config=dict(piece='white_pawn_e2', source='e2'),
        source=np.array([.25, .1, .02]), command=np.zeros(6), last_camera_frame=frame,
        reset=Mock(), task_target='e4', displacement_penalty_per_mm=1., selected={'kind': 'pawn'},
        sim=SimpleNamespace(data=SimpleNamespace(qpos=np.ones(6)), qadr=np.arange(6)))
    env.history = Mock()
    env.feedback = Mock(initial_distance=.035, reach_threshold=.0175)
    env._randomize_start = Mock()
    observation = dict(perception_valid=np.ones(1))
    env._observation = Mock(return_value=observation)
    arrival = SimpleNamespace(sequence=4)

    def execute(scene, report, *, observer):
        assert env.finished and report['initial_command'] == [0.]*6
        scene.command = np.full(6, .5)
        scene.last_camera_frame = arrival
        return arrival, np.array([.251, .1])

    monkeypatch.setattr(autonomous, 'approach_handoff', execute)
    actual, info = env.reset(seed=7)
    assert actual is observation and info['handoff_status'] == 'INITIALIZED'
    env._observation.assert_called_once_with(arrival)
    env._randomize_start.assert_not_called()
    env.feedback.reset.assert_called_once()
    np.testing.assert_array_equal(env.command, [.5]*6)
    np.testing.assert_array_equal(env.source_xy, [.251, .1])
    assert not env.last_handoff['training_eligible']
    with pytest.raises(RuntimeError, match='LOCAL_WORKSPACE_NOT_QUALIFIED'):
        env.step(np.zeros(7))


@pytest.mark.skipif(not os.environ.get('ATOM_HANDOFF_CONFIG'), reason='Requires a native temporal fixture')
def test_native_reset_keeps_actor_independent_of_hidden_physics():
    config = json.loads(Path(os.environ['ATOM_HANDOFF_CONFIG']).read_text(encoding='utf-8'))
    config.setdefault('autonomous', {})['start_mode'] = 'native_approach'
    env = AutonomousManipulationEnv(config)
    try:
        try:
            observation, info = env.reset(seed=7)
        except RuntimeError as error:
            # Known full-board arrival occlusion. No observation was admitted.
            assert str(error) == 'ARRIVAL_TARGET_NOT_VISUALLY_LOCALIZED'
            assert env.last_handoff['reconciliation_required']
            with pytest.raises(RuntimeError, match='Reset required'):
                env.step(np.zeros(7, dtype=np.float32))
            # Exercise the encoder in isolation with the same RGB and permitted
            # issued command. This diagnostic does not admit the failed reset.
            env.command = env.base.command.copy()
            env.last_frame = env.base.last_camera_frame
        else:
            assert info['handoff_status'] == 'INITIALIZED'
            assert env.observation_space.contains(observation)
            with pytest.raises(RuntimeError, match='LOCAL_WORKSPACE_NOT_QUALIFIED'):
                env.step(np.zeros(7, dtype=np.float32))
        report = env.last_handoff
        assert env.VERSION == 7
        assert not report['training_eligible']
        assert report['execution']['elapsed_sim_s'] > 0
        assert report['arrival_perception']['sequence'] == env.last_frame.sequence
        assert np.linalg.norm(np.array(report['initial_command'])-env.command) > 0
        np.testing.assert_array_equal(env.command, report['endpoint']['issued_command'])
        np.testing.assert_array_equal(env.sim.data.qpos[env.sim.qadr], report['endpoint']['measured_position'])
        env.previous_action = np.zeros(7, dtype=np.float32)
        env.history.clear()
        initial = env._observation(env.last_frame)
        env.sim.data.qpos[:] += .1
        env.sim.data.qvel[:] -= .1
        env.history.clear()
        altered = env._observation(env.last_frame)
        for key in initial:
            np.testing.assert_array_equal(initial[key], altered[key])
    finally:
        env.close()
