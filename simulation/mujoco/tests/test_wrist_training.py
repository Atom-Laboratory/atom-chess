"""Wrist IK and camera action regression checks."""
import os
from pathlib import Path

import mujoco
import numpy as np
import pytest

from atom_mujoco.backend import Simulation
from atom_mujoco.model import build_bundle
from atom_mujoco.camera_only_env import CameraOnlyEnv


@pytest.mark.skipif(not os.environ.get('ATOM_WRIST_CONFIG'), reason='Requires wrist camera fixture')
def test_wrist_action_and_offset_aware_native_ik():
    import json

    config = json.loads(Path(os.environ['ATOM_WRIST_CONFIG']).read_text())
    env = CameraOnlyEnv(config)
    try:
        assert env.action_space.shape == (5,)
        assert env.observation_space['commanded_joints'].shape == (6,)
        for angle in np.linspace(0, 2*np.pi, 5):
            env.sim.reset([.2, .1, -.5, 0., 0., angle])
            xyz = env.sim.data.site('grasp_center').xpos.copy()
            solved = env.motion.solve(xyz, 0., wrist=angle)
            env.sim.reset(solved)
            np.testing.assert_allclose(env.sim.data.site('grasp_center').xpos, xyz, atol=1e-6)
            assert solved[-1] == angle
        env.reset(seed=7)
        before = env.command[-1]
        action = np.array([0., 0., 0., 0., .8], dtype=np.float32)
        observation, reward, terminated, truncated, info = env.step(action)
        assert env.command[-1] > before
        assert env.observation_space.contains(observation)
        with pytest.raises(ValueError, match='bounded revolution'):
            env.motion.solve(xyz, 0., wrist=2*np.pi+.01)
    finally:
        env.close()


def test_full_gripper_hulls_follow_wrist_and_finger_bodies(tmp_path):
    source = Path(__file__).resolve().parents[2]/'src/urdf/atom.urdf.xacro'
    bundle = tmp_path/'full'
    build_bundle(source, bundle, interactive=True, wrist=True, full_gripper_collision=True)
    sim = Simulation(bundle)
    hulls = [g for g in range(sim.model.ngeom)
             if (sim.model.geom(g).name or '').endswith('_collision_hull')]
    assert len(hulls) == sim.manifest['scene']['gripper_collision_hulls'] == 66
    bodies = {sim.model.body(int(sim.model.geom_bodyid[g])).name for g in hulls}
    assert bodies == {'gripper_wrist', 'gripper_hand1_moving', 'gripper_hand2_moving'}
    assert all(sim.model.geom_contype[g] == 1 for g in hulls)
    assert all(sim.model.geom_conaffinity[g] & 4 for g in hulls)
    assert all(sim.model.geom_group[g] == 3 for g in hulls)


def test_neighbor_evidence_detects_image_change_and_reference_mismatch():
    from types import SimpleNamespace
    from atom_mujoco.neighbor_vision import NeighborEvidence

    image = np.zeros((800, 800, 3), dtype=np.uint8)
    frame = SimpleNamespace(oriented=True, homography=np.eye(3),
                            reference_sha256='reference', camera_id='fixed',
                            rectified_rgb=image)
    evidence = NeighborEvidence(frame, ['c4'])
    assert evidence.observe(frame) == {'c4': 0.}
    changed = image.copy()
    changed[408:492, 208:292] = 255
    frame.rectified_rgb = changed
    assert evidence.observe(frame)['c4'] > evidence.limit
    frame.reference_sha256 = 'different'
    assert evidence.observe(frame) is None


@pytest.mark.skipif(not os.environ.get('ATOM_NEIGHBOR_CONFIG'), reason='Requires full-gripper neighbor fixture')
def test_neighbor_failure_overrides_successful_target_camera_evidence(monkeypatch):
    env = CameraOnlyEnv(os.environ['ATOM_NEIGHBOR_CONFIG'])
    try:
        env.reset(seed=7)
        monkeypatch.setattr(env.neighbors, 'observe', lambda frame: {'c4': .2})
        for _ in range(env.horizon):
            _, _, done, truncated, info = env.step(np.zeros(5, dtype=np.float32))
            if done or truncated:
                break
        assert info['visual_state'] == 'TARGET_TEMPORALLY_PRESENT_CANDIDATE'
        assert not info['success']
        assert info['failure'] == 'NEIGHBOR_VISUAL_CHANGE'
        assert info['reward_components']['neighbor_disturbance'] < 0
    finally:
        env.close()
