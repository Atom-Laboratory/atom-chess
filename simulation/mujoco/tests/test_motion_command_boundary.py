from pathlib import Path

import mujoco
import numpy as np
import pytest

from atom_mujoco.backend import Simulation
from atom_mujoco.model import build_bundle
from atom_mujoco.motion_controller import MotionController


def test_static_feedforward_never_consumes_live_robot_piece_velocity_or_bias(tmp_path):
    module=Path(__file__).resolve().parents[1]
    build_bundle(module.parent/'src/urdf/atom.urdf.xacro',tmp_path/'bundle',interactive=True,wrist=True)
    sim=Simulation(tmp_path/'bundle');controller=MotionController(sim)
    desired=np.array([-1.5,.12,-1.5,0.,0.,1.25])
    expected=controller.command(desired)
    assert np.all(expected>=sim.lower) and np.all(expected<=sim.upper)
    assert expected[1]>desired[1]  # Existing gravity compensation still exists.
    sim.data.qpos[:]+=.1;sim.data.qvel[:]=1.;sim.data.qfrc_bias[:]=1e5
    np.testing.assert_array_equal(controller.command(desired),expected)
    sim.data=None  # Constructing a command does not even require live MjData.
    np.testing.assert_array_equal(controller.command(desired),expected)
    sim.model.actuator_gainprm[0,0]=0
    with pytest.raises(ValueError,match='Positive arm servo'):controller.command(desired)
