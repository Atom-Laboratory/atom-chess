"""Native integration checks; opt in with a prepared fixed-camera fixture."""
import copy
import json
import os
from pathlib import Path

import numpy as np
import pytest

from atom_mujoco.autonomous_env import AutonomousManipulationEnv


@pytest.fixture
def native_config():
    path = os.environ.get('ATOM_NATIVE_REACH_CONFIG')
    if not path:
        pytest.skip('Set ATOM_NATIVE_REACH_CONFIG to a prepared native_reach configuration')
    return json.loads(Path(path).read_text(encoding='utf-8'))


@pytest.mark.parametrize('change', ['objective', 'temporal', 'randomized', 'invisible'])
def test_native_reach_rejects_unqualified_profiles(native_config, change):
    cfg = copy.deepcopy(native_config)
    objective = 'reach'
    if change == 'objective':
        objective = 'lift'
    elif change == 'temporal':
        cfg['autonomous']['action_mode'] = 'temporal'
    elif change == 'randomized':
        cfg['autonomous']['start_radius_squares'] = [1.25, 2.]
    else:
        cfg['autonomous']['require_visible_target'] = False
    with pytest.raises(ValueError):
        AutonomousManipulationEnv(cfg, objective=objective)


def test_native_reach_executes_approach_and_keeps_hidden_state_out_of_actor(native_config, monkeypatch):
    env = AutonomousManipulationEnv(native_config, objective='reach', horizon=64)
    try:
        def forbidden_teleport():
            raise AssertionError('Planner-started episode must not randomize robot qpos')
        monkeypatch.setattr(env, '_randomize_start', forbidden_teleport)
        obs, _ = env.reset(seed=960000)
        assert env.VERSION == 8 and env.observation_space.contains(obs)
        report = env.last_handoff
        assert report['execution']['approach_complete']
        assert report['execution']['elapsed_sim_s'] > 0
        assert report['reach_only_initialized'] and not report['training_eligible']
        assert not report['manipulation_initialized']
        np.testing.assert_array_equal(env.command, report['endpoint']['issued_command'])
        assert not np.array_equal(env.command, report['initial_command'])
        assert not any(set(pair).intersection(env.control.pad_ids) for pair in env.control.allowed)
        frame = env.last_frame
        position, velocity = env.sim.data.qpos.copy(), env.sim.data.qvel.copy()
        env.history.clear()
        before = env._observation(frame)
        env.sim.data.qpos[:] += .1
        env.sim.data.qvel[:] -= .1
        env.history.clear()
        altered = env._observation(frame)
        for key in before:
            np.testing.assert_array_equal(before[key], altered[key])
        env.sim.data.qpos[:], env.sim.data.qvel[:] = position, velocity
        # A valid proposal still enters native validation, rather than bypassing it.
        _, _, _, _, info = env.step(np.zeros(3, dtype=np.float32))
        assert info['native_approach']['approach_complete']
        assert info['native_approach']['training_scope'] == 'contact_free_reach_only'
    finally:
        env.close()
