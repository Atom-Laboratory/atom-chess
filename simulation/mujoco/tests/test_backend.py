import math
from pathlib import Path
import shutil

import mujoco
import numpy as np
import pytest

from atom_mujoco.backend import Simulation
from atom_mujoco.cli import demonstration
from atom_mujoco.model import build_bundle, origin
from atom_mujoco.model import SCENE
import xml.etree.ElementTree as ET


def test_compiled_model_fk_matches_independent_urdf_equations(sim):
    rng = np.random.default_rng(19)
    for _ in range(30):
        a, z, b = rng.uniform(sim.lower, sim.upper)
        state = sim.reset([a, z, b])
        expected = [.04+.22*math.cos(a), z, -.22*math.sin(a)]
        rotation = np.array(SCENE['urdf_to_scene_rotation'])
        np.testing.assert_allclose(state['arm2_position'], rotation@expected+SCENE['urdf_to_scene_translation_m'], atol=1e-12)
        angle = a+b
        expected_rotation = [[math.cos(angle), 0, math.sin(angle)], [0, 1, 0],
                             [-math.sin(angle), 0, math.cos(angle)]]
        np.testing.assert_allclose(state['arm2_rotation'], rotation@expected_rotation, atol=1e-12)
    assert sim.model.nq == sim.model.nv == sim.model.nu == 3
    assert sim.model.opt.gravity.tolist() == [0., 0., 0.]
    assert sim.model.opt.disableflags & mujoco.mjtDisableBit.mjDSBL_CONTACT


def test_urdf_rpy_is_fixed_axis():
    element = ET.fromstring('<visual><origin xyz="1 2 3" rpy=".2 -.4 .6"/></visual>')
    q = np.array([float(x) for x in origin(element)['quat'].split()])
    rotation = np.zeros(9)
    mujoco.mju_quat2Mat(rotation, q)
    r, p, y = .2, -.4, .6
    rx = [[1,0,0],[0,math.cos(r),-math.sin(r)],[0,math.sin(r),math.cos(r)]]
    ry = [[math.cos(p),0,math.sin(p)],[0,1,0],[-math.sin(p),0,math.cos(p)]]
    rz = [[math.cos(y),-math.sin(y),0],[math.sin(y),math.cos(y),0],[0,0,1]]
    np.testing.assert_allclose(rotation.reshape(3,3), np.array(rz)@ry@rx, atol=1e-12)


def test_real_physics_conventional_control_converges(sim):
    result = demonstration(sim, 4.)
    assert result['finite']
    assert max(result['final_error']) < .001
    assert max(result['max_joint_limit_excess']) < 1e-5
    assert sim.data.time == pytest.approx(4.)
    assert any(np.linalg.norm(s['velocity']) > .01 for s in result['trajectory'])
    assert any(np.linalg.norm(s['actuator_force']) > .01 for s in result['trajectory'])


@pytest.mark.parametrize('target', [[1], [float('nan'), 0, 0], [0,float('inf'),0], [99,0,0]])
def test_invalid_input_does_not_advance_or_mutate(sim, target):
    before = sim.observe()
    with pytest.raises(ValueError):
        sim.advance(target)
    assert sim.data.time == before['time_s']
    np.testing.assert_array_equal(sim.data.qpos, before['position'])
    np.testing.assert_array_equal(sim.target, before['target'])


def test_reset_reproducibility_and_independent_observations(sim):
    first = sim.reset(seed=23, randomize=True)
    trajectory = [sim.advance([.2, .05, -.3])['position'] for _ in range(40)]
    second = sim.reset(seed=23, randomize=True)
    np.testing.assert_array_equal(first['position'], second['position'])
    for expected in trajectory:
        np.testing.assert_array_equal(sim.advance([.2,.05,-.3])['position'], expected)
    second['position'][:] = 99
    assert not (sim.data.qpos == 99).any()
    sim.reset()
    np.testing.assert_array_equal(sim.data.qvel, [0,0,0])
    assert sim.data.time == 0


def test_reference_slew_limit_and_limit_targets(sim):
    before = sim.reference.copy()
    sim.advance(sim.upper)
    assert np.all(abs(sim.reference-before) <= sim.speed*sim.dt+1e-12)
    for _ in range(500):
        state = sim.advance(sim.upper)
    assert np.isfinite(state['position']).all()
    assert max(state['joint_limit_excess']) < .005
    assert state['contacts'] is None


def test_portable_bundle_hashes_and_no_overwrite(bundle, tmp_path):
    moved = tmp_path/'copied'
    shutil.copytree(bundle, moved)
    assert Simulation(moved).model.nu == 3
    (moved/'model.xml').write_text('<mujoco/>')
    with pytest.raises(ValueError, match='integrity'):
        Simulation(moved)
    urdf = Path(__file__).resolve().parents[2]/'src/urdf/atom.urdf.xacro'
    with pytest.raises(FileExistsError):
        build_bundle(urdf, bundle)


def test_upright_scene_board_and_gripper_follow_arm(sim):
    m, d = sim.model, sim.data
    mount = m.body('robot_mount').id
    # Local +Y of the source assembly is vertical in the scene.
    np.testing.assert_allclose(d.xmat[mount].reshape(3,3)@[0,1,0], [0,0,1], atol=1e-12)
    square_ids = [m.geom('square_'+file+str(rank)).id for file in 'abcdefgh' for rank in range(1,9)]
    assert len(set(square_ids)) == 64
    board_before = d.geom_xpos[square_ids].copy()
    arm_id = m.body('arm2_link').id
    gripper_ids = [m.geom(part+'_visual').id for part in ('gripper_back','gripper_hand1','gripper_hand2')]
    assert all(m.geom_bodyid[index] == arm_id for index in gripper_ids)
    local_before = [(d.xmat[arm_id].reshape(3,3).T@(d.geom_xpos[index]-d.xpos[arm_id])) for index in gripper_ids]
    sim.reset([.4,.1,.8])
    np.testing.assert_array_equal(d.geom_xpos[square_ids], board_before)
    for index, expected in zip(gripper_ids, local_before):
        np.testing.assert_allclose(d.xmat[arm_id].reshape(3,3).T@(d.geom_xpos[index]-d.xpos[arm_id]), expected, atol=1e-12)
    assert all(m.geom_contype[index] == m.geom_conaffinity[index] == 0 for index in square_ids+gripper_ids)


def test_starting_pieces_match_named_square_centers(sim):
    pieces = sim.manifest['pieces']
    assert len(pieces) == len({p['initial_square'] for p in pieces}) == 32
    for color in ('white', 'black'):
        selected = [p for p in pieces if p['color'] == color]
        assert len(selected) == 16
        assert sum(p['kind'] == 'pawn' for p in selected) == 8
        assert sum(p['kind'] == 'king' for p in selected) == 1
    for piece in pieces:
        body = sim.model.body(piece['name']).id
        site = sim.model.site('square_center_'+piece['initial_square']).id
        np.testing.assert_allclose(sim.data.xpos[body][:2], sim.data.site_xpos[site][:2], atol=1e-12)
        assert sim.model.body_jntnum[body] == 0
