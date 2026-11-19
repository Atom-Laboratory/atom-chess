import copy

import numpy as np
import pytest
from stable_baselines3 import SAC

from atom_learning.environment import ReachEnv
from atom_learning.experiments import NumpyActor, export_actor


def test_export_matches_actor_and_rejects_wrong_model(config, tmp_path):
    env = ReachEnv(config)
    model = SAC('MlpPolicy', env, seed=5, device='cpu', policy_kwargs={'net_arch': [16, 16]})
    output = tmp_path / 'actor.npz'
    export_actor(model, output, config, env.model.sha256)
    actor = NumpyActor(output, config, env.model.sha256)
    for seed in range(10):
        obs, _ = env.reset(seed=seed)
        expected, _ = model.predict(obs, deterministic=True)
        actual, _ = actor.predict(obs)
        np.testing.assert_allclose(actual, expected, atol=2e-7)
    with pytest.raises(ValueError):
        NumpyActor(output, config, 'wrong-hash')
    changed = copy.deepcopy(config)
    changed['dt'] *= 2
    with pytest.raises(ValueError):
        NumpyActor(output, changed, env.model.sha256)


def test_training_replay_checkpoint_can_resume(config, tmp_path):
    env = ReachEnv(config)
    model = SAC('MlpPolicy', env, seed=12, device='cpu', learning_starts=8,
                buffer_size=128, batch_size=8, policy_kwargs={'net_arch': [16, 16]})
    model.learn(24)
    model.save(tmp_path / 'model')
    model.save_replay_buffer(tmp_path / 'replay.pkl')
    resumed = SAC.load(tmp_path / 'model', env=ReachEnv(config), device='cpu')
    resumed.load_replay_buffer(tmp_path / 'replay.pkl')
    assert resumed.replay_buffer.size() == 24
    before = [p.detach().clone() for p in resumed.actor.parameters()]
    resumed.learn(16, reset_num_timesteps=False)
    assert resumed.num_timesteps == 40
    assert any(not np.array_equal(a.numpy(), b.detach().numpy())
               for a, b in zip(before, resumed.actor.parameters()))
