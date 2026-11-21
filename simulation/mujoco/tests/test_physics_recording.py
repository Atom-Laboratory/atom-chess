from pathlib import Path
import hashlib

import mujoco
import numpy as np
import pytest

from atom_mujoco.backend import Simulation
from atom_mujoco.model import build_bundle
from atom_mujoco.physics_recording import PhysicsRecording


def test_recording_does_not_change_dynamics_and_each_transition_replays_exactly(tmp_path):
    module=Path(__file__).resolve().parents[1]
    build_bundle(module.parent/'src/urdf/atom.urdf.xacro',tmp_path/'bundle',interactive=True,wrist=True)
    baseline,recorded=Simulation(tmp_path/'bundle'),Simulation(tmp_path/'bundle')
    command=np.array([-1.5,.12,-1.5,0.,0.,1.25]);baseline.reset(command);recorded.reset(command)
    recorder=PhysicsRecording(recorded,max_transitions=2*recorded.substeps)
    recorded.step_observer=recorder
    for _ in range(2):baseline.advance(command);recorded.advance(command)
    np.testing.assert_array_equal(recorded.data.qpos,baseline.data.qpos)
    np.testing.assert_array_equal(recorded.data.qvel,baseline.data.qvel)
    for before,after in zip(recorder.before,recorder.after):
        data=mujoco.MjData(recorded.model)
        mujoco.mj_setState(recorded.model,data,before,recorder.signature)
        mujoco.mj_step(recorded.model,data)
        actual=np.empty(recorder.width);mujoco.mj_getState(recorded.model,data,actual,recorder.signature)
        np.testing.assert_array_equal(actual,after)
    path=tmp_path/'record.npz';manifest=recorder.save(path)
    assert manifest['transitions']==2*recorded.substeps
    assert manifest['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):recorder.save(path)
    with pytest.raises(RuntimeError,match='budget exhausted'):recorded.advance(command)


@pytest.mark.parametrize('change',[{'rise_m':.031},{'vertical_slip_m':.004},
    {'bilateral_contact':False},{'settled':False}])
def test_lifted_hold_requires_all_predeclared_conditions(change):
    import importlib.util
    path=Path(__file__).resolve().parents[1]/'examples/qualify_hybrid_approach/local_diagnostic.py'
    spec=importlib.util.spec_from_file_location('lift_hold_criteria',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    valid=dict(rise_m=.044,vertical_slip_m=.001,bilateral_contact=True,settled=True)
    assert module.lifted_hold_valid(valid,.032,.003)
    assert not module.lifted_hold_valid(dict(valid,**change),.032,.003)
