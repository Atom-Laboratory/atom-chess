import importlib.util
from pathlib import Path
import numpy as np
import pytest

pytestmark = pytest.mark.skipif(importlib.util.find_spec('gymnasium') is None,
                                reason='Install the rl extra')


def test_visual_environment_pixels_limits_and_bad_actions():
    from atom_mujoco.visual_grasp_env import VisualGraspEnv
    bundle = Path(__file__).resolve().parents[1]/'assets/bundles/playground-fingertip-only-v1'
    if not bundle.exists():
        pytest.skip('Build fingertip-only fixture')
    env = VisualGraspEnv(bundle,horizon=2)
    try:
        obs,_ = env.reset(seed=11)
        assert obs.shape == (3,96,96) and obs.dtype == np.uint8
        before = env.sim.data.qpos.copy()
        for action in ([np.nan,0,0,0], [2,0,0,0], [0,0]):
            with pytest.raises(ValueError):
                env.step(action)
            np.testing.assert_array_equal(env.sim.data.qpos,before)
        _,reward,terminated,truncated,info = env.step(np.zeros(4))
        assert np.isfinite(reward)
        assert info['reward_source']=='simulation_oracle'
        _,_,_,truncated,_ = env.step(np.zeros(4))
        assert truncated
        with pytest.raises(RuntimeError):
            env.step(np.zeros(4))
        second,_ = env.reset(seed=11)
        np.testing.assert_array_equal(obs,second)
    finally:
        env.close()


def test_lift_curriculum_is_solvable_and_camera_stays_fixed():
    from atom_mujoco.visual_grasp_env import VisualGraspEnv
    bundle = Path(__file__).resolve().parents[1]/'assets/bundles/playground-fingertip-only-v1'
    if not bundle.exists():
        pytest.skip('Build fingertip-only fixture')
    env = VisualGraspEnv(bundle, horizon=60, stage='lift')
    try:
        for seed in (7, 11, 10000):
            obs, info = env.reset(seed=seed)
            assert info['reset_grip']
            assert env.playground.feedback.grip_contacts('white_pawn_e2')
            camera = env.camera.lookat.copy()
            received = []
            env.on_transition = lambda pixels, state: received.append(pixels.copy())
            for _ in range(60):
                obs, _, done, truncated, info = env.step(np.array([0.,1.,0.,0.]))
                if done or truncated:
                    break
            assert info['success'], info
            assert not info['disturbed']
            np.testing.assert_array_equal(received[-1],obs)
            np.testing.assert_array_equal(camera,env.camera.lookat)
            env.on_transition = None
    finally:
        env.close()


def test_grasp_curriculum_does_not_start_with_scripted_grip():
    from atom_mujoco.visual_grasp_env import VisualGraspEnv
    bundle = Path(__file__).resolve().parents[1]/'assets/bundles/playground-fingertip-only-v1'
    if not bundle.exists():
        pytest.skip('Build fingertip-only fixture')
    env = VisualGraspEnv(bundle,stage='grasp')
    try:
        _,info = env.reset(seed=7)
        assert not info['reset_grip']
        np.testing.assert_allclose(env.sim.observe()['position'][3:], env.sim.upper[3:], atol=.0002)
        assert not any(env.playground.feedback.pad_contacts('white_pawn_e2'))
        assert not env.playground.feedback.grip_contacts('white_pawn_e2')
        assert env.bystander_displacement() < .008
    finally:
        env.close()
