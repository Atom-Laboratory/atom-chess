"""P038 real planner/native vision/physics regression and actor isolation."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import mujoco
import numpy as np
import pytest

from atom_mujoco.camera_manipulation_env import CameraManipulationEnv
from atom_mujoco.camera_reward import PhysicalTruth
from atom_mujoco.visual_verification import VisualVerification


@pytest.fixture
def env():
    path = os.environ.get('P038_CONFIG')
    if not path:
        pytest.skip('Prepare a P038 fixture and set P038_CONFIG')
    instance = CameraManipulationEnv(path)
    try:
        instance.reset(seed=7)
        yield instance
    finally:
        instance.close()


def test_nominal_cpp_trajectory_maps_to_actual_robot(env):
    assert len(env.nominal) == 8
    assert env.preflight['valid'] and env.preflight['samples'] > 0
    scratch = mujoco.MjData(env.sim.model)
    for pose, command in zip(env.poses, env.nominal):
        scratch.qpos[:] = env.sim.data.qpos
        scratch.qpos[env.sim.qadr] = command
        mujoco.mj_forward(env.sim.model, scratch)
        np.testing.assert_allclose(scratch.site('grasp_center').xpos, pose[:3], atol=1e-6)


def test_complete_zero_residual_transfer(env):
    total = 0.
    phases = []
    for _ in range(env.horizon):
        observation, reward, terminated, truncated, info = env.step(np.zeros(4, dtype=np.float32))
        assert env.observation_space.contains(observation)
        total += reward
        phases.append(info['phase'])
        if terminated or truncated:
            break
    assert info['success'] and info['grasp'] and info['placement']
    assert info['phase'] == 'RETRACT' and info['collisions'] == 0
    assert len(set(phases)) == 8
    assert not info['visual_confirmed']
    assert sum(info['episode_reward_components'].values()) == pytest.approx(total)
    assert env.dwell_count >= env.dwell
    with pytest.raises(RuntimeError, match='Reset required'):
        env.step(np.zeros(4))


def test_actor_isolation_with_two_different_simulator_states(env):
    other = CameraManipulationEnv(env.config)
    try:
        other.reset(seed=7)
        rgb = env.render()
        body = other.sim.model.body(other.config['piece']).id
        address = other.sim.model.jnt_qposadr[other.sim.model.body_jntadr[body]]
        other.sim.data.qpos[address:address+3] += [.04, -.03, .05]
        other.sim.data.qvel[:] = .01
        mujoco.mj_forward(other.sim.model, other.sim.data)
        first, _ = env._observation(rgb)
        second, _ = other._observation(rgb.copy())
        assert set(first) == {'image', 'task', 'previous_action', 'commanded_joints', 'phase', 'perception_valid'}
        assert env.reward_evaluator.read().position.tolist() != other.reward_evaluator.read().position.tolist()
        for name in first:
            assert first[name].tobytes() == second[name].tobytes()
            assert first[name].dtype != object
    finally:
        other.close()


def test_invalid_action_and_supervisor_rejection_never_execute(env, monkeypatch):
    before = env.sim.data.qpos.copy()
    _, _, terminated, _, info = env.step(np.array([2, 0, 0, 0], dtype=np.float32))
    assert terminated and info['failure'] == 'INVALID_ACTION'
    np.testing.assert_array_equal(before, env.sim.data.qpos)
    env.reset(seed=7)
    before = env.sim.data.qpos.copy()
    monkeypatch.setattr(env, '_supervise', lambda start, end: {'status': 'collision'})
    def forbidden(*args):
        raise AssertionError('Rejected action reached actuator execution')
    monkeypatch.setattr(env.controller, 'step', forbidden)
    _, _, terminated, _, info = env.step(np.zeros(4))
    assert terminated and info['failure'] == 'UNSAFE_RESIDUAL'
    np.testing.assert_array_equal(before, env.sim.data.qpos)


def test_perception_failure_is_masked_terminal(env, monkeypatch):
    monkeypatch.setattr(env, 'render', lambda: np.zeros((1440, 1920, 3), dtype=np.uint8))
    observation, reward, terminated, _, info = env.step(np.zeros(4))
    assert terminated and not info['success']
    assert info['failure'] == 'PERCEPTION_FAILED'
    assert observation['perception_valid'][0] == 0
    assert not observation['image'].any()


def test_placement_without_grasp_and_lift_cannot_succeed(env, monkeypatch):
    evaluator = env.reward_evaluator
    truth = PhysicalTruth(
        np.array([*env.destination[:2], env.support_z]), np.zeros(6), 0,
        np.array([0, 0, .2]), False, True)
    evaluator.events.clear()
    monkeypatch.setattr(evaluator, 'read', lambda: truth)
    placement_rewards = []
    for _ in range(8):
        _, info = evaluator.evaluate('RETRACT', np.zeros(4), phase_complete=True)
        assert not info['success']
        placement_rewards.append(info['reward_components'].get('placement', 0))
    assert sum(placement_rewards) == env.config['reward_weights']['placement']


def test_visual_candidate_sequence_never_fabricates_transport():
    verification = VisualVerification('e4', 'e5', 'white')
    grid = np.zeros((8, 8), dtype=np.int32)
    grid[3, 4] = 1
    for sequence in range(1, 4):
        state = verification.update(SimpleNamespace(
            sequence=sequence, homography=np.eye(3), oriented=True, candidates=grid))
    assert state == 'TARGET_TEMPORALLY_PRESENT_CANDIDATE'
    lost = verification.update(SimpleNamespace(sequence=4, homography=None, oriented=False))
    assert lost == 'UNKNOWN'
    with pytest.raises(ValueError):
        verification.update(SimpleNamespace(sequence=4, homography=None, oriented=False))
