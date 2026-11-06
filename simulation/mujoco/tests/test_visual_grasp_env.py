import importlib.util
from pathlib import Path
import numpy as np
import pytest

pytestmark = pytest.mark.skipif(importlib.util.find_spec('gymnasium') is None,
                                reason='Install the rl extra')


def test_visual_environment_pixels_limits_and_bad_actions():
    from atom_mujoco.visual_grasp_env import VisualGraspEnv
    bundle = Path(__file__).resolve().parents[1]/'runs/playground-fingertip-only-v1'
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
