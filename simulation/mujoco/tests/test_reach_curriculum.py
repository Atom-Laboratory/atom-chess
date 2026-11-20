from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from atom_mujoco.autonomous_env import AutonomousManipulationEnv
from atom_mujoco.autonomous_control import MotionChoice


def profile():
    env = AutonomousManipulationEnv.__new__(AutonomousManipulationEnv)
    env.xyz_only, env.xyz_scale = True, .25
    env.workspace_squares = 2.5
    env.command = np.array([.1, .1, -.5, 0., 0., 0.])
    env.source_xy = np.array([.25, -.05])
    env.base = SimpleNamespace(surface_z=.018, pitch=.035)
    env.control = Mock()
    return env


def test_xyz_actions_freeze_other_controls_and_duration():
    env = profile()
    env._decode_action([1., -.5, .25])
    expanded, command = env.control.decode.call_args.args
    np.testing.assert_array_equal(expanded, [.25, -.125, .0625, 0., 0., 0., -1.])
    np.testing.assert_array_equal(command, env.command)
    for action in ([0.]*7, [float('nan')]*3, [2., 0., 0.]):
        with pytest.raises(ValueError, match='three finite'):
            env._decode_action(action)


def test_workspace_exit_rejected_before_ik_and_no_silent_projection():
    env = profile()
    far = MotionChoice((.5, -.05, .06), 0., 0., True, 1, .02)
    end, status = env._validate_choice(far)
    assert end is None and status['status'] == 'LOCAL_WORKSPACE_REJECTED'
    env.control.validate.assert_not_called()
    near = MotionChoice((.25, -.05, .06), 0., 0., True, 1, .02)
    env.control.validate.return_value = (env.command, {'status':'ACCEPTED'})
    env._validate_choice(near)
    assert env.control.validate.call_args.kwargs['project'] is False


def test_legacy_decode_and_projection_remain_separate():
    env = profile()
    env.xyz_only = False
    action = [0.]*7
    env._decode_action(action)
    assert env.control.decode.call_args.args[0] is action
    env.control.validate.return_value = (env.command, {'status':'ACCEPTED'})
    choice = MotionChoice((.5, 0., .1), 0., 0., True, 1, .02)
    env._validate_choice(choice)
    assert env.control.validate.call_args.kwargs['project'] is True


def test_reference_uses_camera_xy_and_commanded_fk_only():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[1]/'training/autonomous-manipulation/reference_reach.py'
    spec = importlib.util.spec_from_file_location('reference_reach', path)
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    env = profile()
    env.base.piece_height = .032
    env.base.sim = SimpleNamespace(dt=.02)  # No model/body-state access is available.
    env.control.rates = np.array([.1, .1, .1, .1, .01])
    env.control.commanded_tcp.return_value = np.array([.24, -.04, .06])
    action = reference.reference_action(env)
    np.testing.assert_array_equal(action, [1., -1., -1.])


def test_planner_reach_bounds_are_centered_on_static_piece_top():
    env = profile()
    env.native_reach = True
    env.base.piece_height = .04
    env.control.validate.return_value = (env.command, {'status': 'ACCEPTED'})
    # This endpoint is inside the top-centered bound but outside a board-centered one.
    endpoint = MotionChoice((.25, -.05, .12), 0., 0., True, 1, .02)
    assert env._validate_choice(endpoint)[1]['status'] == 'ACCEPTED'
    assert env.control.validate.call_args.kwargs['project'] is False


@pytest.mark.parametrize('success,expected_exit', [(True, 0), (False, 1)])
def test_reference_cli_does_not_qualify_failed_episodes(tmp_path, monkeypatch, success, expected_exit):
    import importlib.util
    import json
    import sys
    from pathlib import Path
    path = Path(__file__).resolve().parents[1]/'training/autonomous-manipulation/reference_reach.py'
    spec = importlib.util.spec_from_file_location('reference_cli', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scene = SimpleNamespace(horizon=1, native_reach=False, last_handoff=None,
        reset=Mock(), close=Mock(), sim=SimpleNamespace(manifest={'model_sha256': 'model'}),
        step=Mock(return_value=({}, 0., success, not success,
                                dict(success=success, pad_distance_m=.01))))
    monkeypatch.setattr(module, 'AutonomousManipulationEnv', lambda *args, **kwargs: scene)
    monkeypatch.setattr(module, 'reference_action', lambda env: np.zeros(3))
    config = tmp_path/'environment.json'
    config.write_text('{}')
    output = tmp_path/'result'
    monkeypatch.setattr(sys, 'argv', ['reference_reach.py', '--config', str(config),
                                   '--output', str(output), '--episodes', '1'])
    assert module.main() == expected_exit
    assert json.loads((output/'report.json').read_text())['success_rate'] == float(success)
    scene.close.assert_called_once()
