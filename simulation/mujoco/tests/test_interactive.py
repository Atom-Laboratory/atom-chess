from pathlib import Path

import mujoco
import numpy as np
import pytest

from atom_mujoco.backend import Simulation
from atom_mujoco.controls import jog, clean_view_options


def test_robot_shortcuts_cannot_leave_diagnostic_balloons_enabled():
    options = mujoco.MjvOption()
    # Native shortcuts run in addition to our key callback.
    options.flags[:] = 1
    options.geomgroup[:] = 1
    clean_view_options(options)
    for flag in (mujoco.mjtVisFlag.mjVIS_AUTOCONNECT,
                 mujoco.mjtVisFlag.mjVIS_CONTACTPOINT,
                 mujoco.mjtVisFlag.mjVIS_CONTACTFORCE,
                 mujoco.mjtVisFlag.mjVIS_INERTIA):
        assert not options.flags[flag]
    assert not options.geomgroup[3]
    assert options.flags[mujoco.mjtVisFlag.mjVIS_STATIC]
from atom_mujoco.model import build_bundle


def test_finger_travel_matches_mesh_faces_and_keeps_contact_alignment(interactive):
    import importlib.util
    path = Path(__file__).resolve().parents[1]/'examples/inspect_gripper_geometry/run.py'
    spec = importlib.util.spec_from_file_location('geometry_inspection', path)
    inspection = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inspection)
    evidence = inspection.inspect(Path(__file__).resolve().parents[2]/'src/meshes')
    sim = interactive
    axis = sim.model.jnt_axis[sim.model.joint('finger_1').id]
    for record in evidence['parts']:
        np.testing.assert_allclose(axis, record['rail_axis'], atol=1e-4)
    # Old global-Z motion deviated by ~37 degrees from these mesh-derived rails.
    assert abs(axis[0]) > .6 and abs(axis[2]) > .79
    for arm in ([0, .12, 0], [.4, .12, -.8]):
        positions = []
        rotations = []
        for opening in (0, sim.lower[3]):
            sim.reset([*arm, opening, opening])
            positions.append([sim.data.geom_xpos[sim.model.geom(f'finger_{i}_pad').id].copy() for i in (1, 2)])
            rotations.append([sim.data.geom_xmat[sim.model.geom(f'finger_{i}_pad').id].copy() for i in (1, 2)])
        np.testing.assert_allclose(np.mean(positions[0], axis=0), np.mean(positions[1], axis=0), atol=1e-12)
        np.testing.assert_allclose(rotations[0], rotations[1], atol=1e-12)
        rotation = sim.data.xmat[sim.model.body('arm2_link').id].reshape(3,3)
        for index, sign in enumerate((1, -1)):
            travel = rotation.T@(positions[1][index]-positions[0][index])
            np.testing.assert_allclose(travel, sim.lower[3]*sign*axis, atol=1e-12)


@pytest.fixture
def interactive(tmp_path):
    source = Path(__file__).resolve().parents[2]/'src/urdf/atom.urdf.xacro'
    build_bundle(source, tmp_path/'interactive', interactive=True)
    return Simulation(tmp_path/'interactive')


def test_bidirectional_controls_and_clamping():
    lo, hi = np.array([-2., -.1, -2.]), np.array([2., .2, 4.])
    start = np.array([0., .1, 0.])
    for i in range(3):
        forward = jog(start, lo, hi, i, 1)
        assert forward[i] > start[i]
        np.testing.assert_allclose(jog(forward, lo, hi, i, -1), start)
        assert jog(hi, lo, hi, i, 1)[i] == hi[i]
        assert jog(lo, lo, hi, i, -1)[i] == lo[i]


def test_gravity_fingers_and_return(interactive):
    sim = interactive
    assert sim.model.nu == 5
    assert sim.model.nq == 5+32*7
    np.testing.assert_allclose(sim.model.opt.gravity, [0,0,-9.81])
    assert not sim.model.opt.disableflags & mujoco.mjtDisableBit.mjDSBL_CONTACT
    for opening in (sim.upper[3], sim.lower[3], sim.upper[3]):
        goal = sim.target.copy()
        goal[3:] = opening
        for _ in range(150):
            state = sim.advance(goal)
        np.testing.assert_allclose(state['position'][3:], opening, atol=.0002)
        assert np.max(state['joint_limit_excess']) < .001
    # Remove actuator support to verify gravity actually changes the vertical state.
    sim.reset()
    before = sim.data.qpos[1]
    sim.model.actuator_gainprm[:] = 0
    sim.model.actuator_biasprm[:] = 0
    for _ in range(50):
        mujoco.mj_step(sim.model, sim.data)
    assert sim.data.qpos[1] < before-.001


def test_robot_environment_contacts_are_reported(interactive):
    sim = interactive
    goal = sim.target.copy()
    goal[1] = -.1
    found = []
    for _ in range(200):
        state = sim.advance(goal)
        found.extend(state['contacts'])
    assert found, 'Lowering the robot must produce environment contacts'
    robot_colliders = {sim.model.geom(i).name for i in range(sim.model.ngeom)
                       if 'collision' in (sim.model.geom(i).name or '')
                       or (sim.model.geom(i).name or '').startswith('finger_')}
    assert any((contact['geom1'] in robot_colliders) !=
               (contact['geom2'] in robot_colliders) for contact in found)
    assert np.isfinite(state['position']).all()
    assert not sim.data.warning.number.any()
    sim.reset()
    assert sim.data.time == 0


def test_dynamic_pawn_contact_grasp_lift_release_and_reset(interactive):
    sim = interactive
    sim.reset([0, .020, 0, 0, 0])
    # Explicit isolated fixture: relocate other pieces and place a pawn under
    # the fingers. No pose edits occur after the experiment starts below.
    for i, piece in enumerate(sim.manifest['pieces']):
        body = sim.model.body(piece['name']).id
        address = sim.model.jnt_qposadr[sim.model.body_jntadr[body]]
        sim.data.qpos[address:address+3] = [2+i*.04, 2, .001]
    body = sim.model.body('white_pawn_a2').id
    address = sim.model.jnt_qposadr[sim.model.body_jntadr[body]]
    sim.data.qpos[address:address+3] = [.373, -.0905, .0182]
    mujoco.mj_forward(sim.model, sim.data)
    goal = sim.target.copy()
    for _ in range(100):
        sim.advance(goal)
    initial = sim.data.xpos[body].copy()
    goal[3:] = sim.lower[3:]
    for _ in range(100):
        sim.advance(goal)
    assert any('finger_' in str(contact) and 'white_pawn_a2' in str(contact)
               for contact in sim.contact_report())
    goal[1] += .08
    for _ in range(200):
        state = sim.advance(goal)
    assert sim.data.xpos[body, 2] > initial[2]+.06
    assert abs(state['position'][3]-state['position'][4]) < 1e-5
    goal[3:] = sim.upper[3:]
    for _ in range(150):
        sim.advance(goal)
    assert abs(sim.data.xpos[body, 2]-initial[2]) < .002
    sim.reset()
    assert sim.data.time == 0
    assert np.linalg.norm(sim.data.xpos[body, :2]-initial[:2]) > .05
    np.testing.assert_array_equal(sim.data.qvel, 0)
    with pytest.raises(ValueError, match='equal targets'):
        sim.advance([0, .12, 0, -.01, 0])


def test_bounded_wrist_rotates_both_pads_and_preserves_gripper_opening(tmp_path):
    from atom_mujoco.model import build_bundle

    source = Path(__file__).resolve().parents[2]/'src/urdf/atom.urdf.xacro'
    output = tmp_path/'wrist'
    build_bundle(source, output, interactive=True, wrist=True)
    sim = Simulation(output)
    assert sim.names[-3:] == ['finger_1', 'finger_2', 'wrist_joint']
    joint = sim.model.joint('wrist_joint')
    assert joint.limited
    np.testing.assert_allclose(joint.range, [0, 2*np.pi])
    home = sim.target.copy()
    names = ['finger_1_pad', 'finger_2_pad']
    initial = np.array([sim.data.geom(name).xpos.copy() for name in names])
    pivot = sim.data.xanchor[joint.id].copy()
    np.testing.assert_allclose(sim.data.xaxis[joint.id], [0, 0, 1], atol=1e-12)
    turn = home.copy()
    turn[-1] = np.pi/2
    sim.reset(turn)
    quarter_turn = np.array([sim.data.geom(name).xpos.copy() for name in names])
    rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    np.testing.assert_allclose(quarter_turn, pivot+(initial-pivot)@rotation.T, atol=1e-12)
    sim.reset(home)
    for angle in (sim.upper[-1], sim.lower[-1]):
        turn[-1] = angle
        for _ in range(180):
            state = sim.advance(turn)
        assert state['position'][-1] == pytest.approx(angle, abs=.002)
        np.testing.assert_allclose(state['position'][3:5], home[3:5], atol=.0002)
    turn[-1] = sim.upper[-1]+.01
    with pytest.raises(ValueError, match='outside'):
        sim.advance(turn)
