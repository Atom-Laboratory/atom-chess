"""Integration qualification for RGB-only task reward."""
import os

import numpy as np
import pytest

from atom_mujoco.camera_only_env import CameraOnlyEnv


@pytest.mark.skipif(not os.environ.get('ATOM_CAMERA_ONLY_CONFIG'),
                    reason='Requires an explicit generated camera fixture and native libraries')
def test_rgb_only_transfer_does_not_read_privileged_task_reward(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Privileged task feedback accessed')

    monkeypatch.setattr('atom_mujoco.camera_reward.RewardEvaluator.read', forbidden)
    env = CameraOnlyEnv(os.environ['ATOM_CAMERA_ONLY_CONFIG'])
    try:
        env.reset(seed=7)
        for _ in range(env.horizon):
            observation, reward, terminated, truncated, info = env.step(
                np.zeros(env.action_space.shape, dtype=np.float32))
            assert env.observation_space.contains(observation)
            assert np.isfinite(reward)
            if terminated or truncated:
                break
        assert info['success'], info
        assert info['visual_confirmed']
        assert info['reward_source'] == 'rgb_only'
        assert info['grasp'] is None
        assert info['collisions'] is None
    finally:
        env.close()
