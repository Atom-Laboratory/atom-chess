import copy

import numpy as np
import pytest
from stable_baselines3.common.env_checker import check_env

from atom_learning.environment import ReachEnv, reward_value
from atom_learning.experiments import evaluate
from atom_learning.model import UrdfModel, rotation_error


def test_fk_against_independent_equations(config):
    model = UrdfModel(config['model'], config['tip'])
    # Existing URDF: shoulder offset .04, elbow offset .22; Y-axis rotation.
    # These are regression references for the prototype, not measured hardware.
    for a, z, b in [(0, 0, 0), (0.4, .08, -.2), (-1, -.05, 1.2)]:
        pose = model.fk([a, z, b])
        np.testing.assert_allclose(pose[:3, 3], [.04+.22*np.cos(a), z, -.22*np.sin(a)], atol=1e-12)
        np.testing.assert_allclose(pose[:3, :3],
            [[np.cos(a+b), 0, np.sin(a+b)], [0, 1, 0], [-np.sin(a+b), 0, np.cos(a+b)]], atol=1e-12)


def test_ik_roundtrip_and_unsolved_target(config):
    model = UrdfModel(config['model'], config['tip'])
    rng = np.random.default_rng(82)
    for _ in range(30):
        q = model.center + rng.uniform(-.2, .2, model.dof) * model.span
        target = model.fk(q)
        solved = model.ik(target)
        assert solved is not None
        np.testing.assert_allclose(model.fk(solved), target, atol=1e-6)
    target = np.eye(4)
    target[0, 3] = 10
    assert model.ik(target) is None
    with pytest.raises(ValueError):
        model.ik(np.zeros((4, 4)))


def test_rotation_error_pi():
    np.testing.assert_allclose(np.linalg.norm(rotation_error(np.diag([1, -1, -1]), np.eye(3))), np.pi)


@pytest.mark.parametrize('value', [[np.nan, 0, 0], [0, 0], [3, 0, 0]])
def test_invalid_joint_states_rejected(config, value):
    model = UrdfModel(config['model'], config['tip'])
    with pytest.raises(ValueError):
        model.fk(value)


def test_gymnasium_contract(config):
    check_env(ReachEnv(config), warn=True)


def test_reset_seed_and_rollout_reproducibility(config):
    a, b = ReachEnv(config), ReachEnv(config)
    np.testing.assert_array_equal(a.reset(seed=22)[0], b.reset(seed=22)[0])
    for _ in range(10):
        x, y = a.step([.1, -.1, .2]), b.step([.1, -.1, .2])
        np.testing.assert_array_equal(x[0], y[0])
        assert x[1:] == y[1:]
    a.reset(seed=22)
    assert np.all(a.controller.action == 0) and a.steps == 0


def test_controller_bounds_velocity_and_slew(config):
    env = ReachEnv(config)
    env.reset(seed=3)
    before = env.controller.q.copy()
    result = env.controller.command(np.ones(env.model.dof))
    assert np.all(np.abs(result.velocity) <= env.controller.max_velocity)
    np.testing.assert_allclose(result.applied_action, config['action_slew_per_step'])
    np.testing.assert_allclose(result.position - before, result.velocity * config['dt'])


def test_success_and_no_step_after_termination(config):
    env = ReachEnv(config)
    q = env.model.center
    env.reset(options={'initial_q': q, 'goal_q': q})
    _, reward, terminated, truncated, info = env.step([0, 0, 0])
    assert terminated and not truncated and info['status'] == 'success' and reward > 0
    assert info['collisions'] is None
    with pytest.raises(RuntimeError):
        env.step([0, 0, 0])


def test_timeout_is_truncation(config):
    config['horizon'] = 1
    env = ReachEnv(config)
    env.reset(options={'initial_q': [0, 0, 0], 'goal_q': [.5, .1, 1]})
    _, _, terminated, truncated, info = env.step([0, 0, 0])
    assert not terminated and truncated and info['status'] == 'timeout'


@pytest.mark.parametrize('action', [[np.nan, 0, 0], [1.2, 0, 0], [0, 0]])
def test_invalid_action_stops_without_moving(config, action):
    env = ReachEnv(config)
    env.reset(seed=7)
    q = env.controller.q.copy()
    _, reward, terminated, truncated, info = env.step(action)
    np.testing.assert_array_equal(q, env.controller.q)
    assert terminated and not truncated and info['status'] == 'invalid_action'
    assert reward < 0 and env.controller.stopped


def test_limit_and_interruption(config):
    env = ReachEnv(config)
    env.reset(options={'initial_q': env.model.upper, 'goal_q': env.model.center})
    _, reward, terminated, _, info = env.step([1, 1, 1])
    assert terminated and info['limit_violations'] == 1 and reward < 0
    assert np.all(env.controller.q <= env.model.upper)
    env.reset(seed=4)
    env.stop()
    assert env.step([0, 0, 0])[4]['status'] == 'interrupted'


def test_reward_prefers_progress_and_penalizes_failure(config):
    w = config['reward']
    assert reward_value(.5, .4, 0, False, False, w) > reward_value(.5, .6, 0, False, False, w)
    assert reward_value(.5, .4, 1, False, False, w) < reward_value(.5, .4, 0, False, False, w)
    assert reward_value(0, 0, 0, True, True, w) == -w['failure']


def test_cartesian_planner_to_controller_task(config):
    env = ReachEnv(config)
    target = env.model.fk([.4, .08, .6])
    env.reset(options={'target_pose': target, 'initial_q': [0, 0, 0]})
    np.testing.assert_allclose(env.model.fk(env.goal), target, atol=1e-6)
    from atom_learning.environment import conventional_action
    for _ in range(config['horizon']):
        _, _, terminated, truncated, info = env.step(conventional_action(env))
        if terminated or truncated:
            break
    assert info['is_success']


def test_conventional_baseline_completes_heldout_targets(config):
    result = evaluate(config, 'conventional', range(100))
    assert result['summary']['success_rate'] == 1
    assert result['summary']['limit_violations'] == 0


def test_unsafe_config_rejected(config):
    for key, value in [('dt', 0), ('sampling_fraction', 1.5), ('velocity_fraction', 2)]:
        modified = copy.deepcopy(config)
        modified[key] = value
        with pytest.raises(ValueError):
            ReachEnv(modified)
