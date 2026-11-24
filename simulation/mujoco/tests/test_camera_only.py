"""Integration qualification for RGB-only task reward."""
import os

import numpy as np
import pytest

from atom_mujoco.camera_only_env import CameraOnlyEnv


@pytest.mark.skipif(not os.environ.get('ATOM_CAMERA_FEN_CONFIG'),
                    reason='Requires the full-board camera/FEN fixture')
def test_rgb_fen_reset_plans_from_pixels_with_oracle_blocked(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Privileged task feedback accessed')

    monkeypatch.setattr('atom_mujoco.camera_reward.RewardEvaluator.read', forbidden)
    env = CameraOnlyEnv(os.environ['ATOM_CAMERA_FEN_CONFIG'])
    try:
        observation, info = env.reset(seed=7)
        offset = info['observed_offsets_m']['e2']
        assert len(env.occupied) == 32
        assert np.linalg.norm(offset) > 0
        np.testing.assert_allclose(env.source[:2], env._square_position('e2')[:2]+offset)
        np.testing.assert_allclose(env.poses[0, :2], env.source[:2])
        assert set(observation) == {'image', 'task', 'previous_action', 'commanded_joints',
                                    'phase', 'perception_valid'}
        observation, reward, _, _, info = env.step(np.zeros(env.action_space.shape, dtype=np.float32))
        assert env.observation_space.contains(observation)
        assert np.isfinite(reward)
        assert info['reward_source'] == 'rgb_plus_simulated_piece_supervision'
    finally:
        env.close()


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

@pytest.mark.skipif(not os.environ.get('ATOM_CAMERA_ONLY_CONFIG'),
                    reason='Requires the generated camera fixture')
def test_curriculum_target_matches_actor_and_visual_verifier(monkeypatch):
    import json
    from pathlib import Path

    config = json.loads(Path(os.environ['ATOM_CAMERA_ONLY_CONFIG']).read_text())
    config['task_targets'] = ['d5', 'f3']

    def forbidden(*args, **kwargs):
        raise AssertionError('Privileged task feedback accessed')

    monkeypatch.setattr('atom_mujoco.camera_reward.RewardEvaluator.read', forbidden)
    env = CameraOnlyEnv(config)
    try:
        assert env.VERSION == 3
        for target in config['task_targets']:
            observation, _ = env.reset(seed=7, options={'target': target})
            expected = np.array([ord(target[0])-97, 8-int(target[1])])/7
            np.testing.assert_allclose(observation['task'][2:], expected)
            assert env.visual.target == (8-int(target[1]), ord(target[0])-97)
            assert env.config['target'] == config['target']
            for _ in range(env.horizon):
                observation, reward, terminated, truncated, info = env.step(
                    np.zeros(4, dtype=np.float32))
                if terminated or truncated:
                    break
            assert info['success'], info
            assert info['target'] == target
        with pytest.raises(ValueError, match='configured curriculum'):
            env.reset(options={'target': 'a8'})
    finally:
        env.close()
