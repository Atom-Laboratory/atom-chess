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
    for opening in (.02, -.01, .02):
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
    assert any('collision' in str(contact) for contact in found)
    assert np.isfinite(state['position']).all()
    assert not sim.data.warning.number.any()
    sim.reset()
    assert sim.data.time == 0


def test_dynamic_pawn_contact_grasp_lift_release_and_reset(interactive):
    sim = interactive
    sim.reset([0, .0115, 0, 0, 0])
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
    goal[3:] = -.01
    for _ in range(100):
        sim.advance(goal)
    assert any('finger_' in str(contact) and 'white_pawn_a2' in str(contact)
               for contact in sim.contact_report())
    goal[1] += .08
    for _ in range(200):
        state = sim.advance(goal)
    assert sim.data.xpos[body, 2] > initial[2]+.06
    assert abs(state['position'][3]-state['position'][4]) < 1e-5
    goal[3:] = .02
    for _ in range(150):
        sim.advance(goal)
    assert abs(sim.data.xpos[body, 2]-initial[2]) < .002
    sim.reset()
    assert sim.data.time == 0
    assert np.linalg.norm(sim.data.xpos[body, :2]-initial[:2]) > .05
    np.testing.assert_array_equal(sim.data.qvel, 0)
    with pytest.raises(ValueError, match='equal targets'):
        sim.advance([0, .12, 0, -.01, .02])
