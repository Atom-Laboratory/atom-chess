import importlib.util
from pathlib import Path
import sys

import mujoco
import numpy as np
import pytest


path=Path(__file__).resolve().parents[1]/'batch.py'
spec=importlib.util.spec_from_file_location('atom_gpu_batch_contract',path)
batch=importlib.util.module_from_spec(spec);sys.modules[spec.name]=batch;spec.loader.exec_module(batch)


def test_cpu_full_state_and_selected_reset_do_not_leak_between_worlds():
    model=mujoco.MjModel.from_xml_string('''<mujoco><worldbody><body><joint type="slide"/>
      <geom size=".01" mass="1"/></body></worldbody><actuator><motor joint="0"/></actuator></mujoco>'''.replace('type="slide"','name="slide" type="slide"').replace('joint="0"','joint="slide"'))
    states=[mujoco.MjData(model) for _ in range(2)]
    for index,data in enumerate(states):
        data.time=index+.1;data.qpos[:]=index*.1;data.qvel[:]=index*.2
        data.ctrl[:]=index*.3;data.qacc_warmstart[:]=index*.4;data.qfrc_applied[:]=index*.5
    packed=batch.pack(model,states)
    value=batch.CpuBatch(model,batch.Limits(worlds=2));value.reset(packed)
    np.testing.assert_array_equal(value.state(),packed)
    value.step(np.array([[.1],[.2]]));before=value.state().copy()
    value.reset(packed,active=np.array([True,False]))
    np.testing.assert_array_equal(value.state()[0],packed[0])
    np.testing.assert_array_equal(value.state()[1],before[1])
    with pytest.raises(ValueError):value.reset(packed[:1])
    with pytest.raises(ValueError):value.reset(packed,active=[1,0])
    with pytest.raises(ValueError):value.step([[float('nan')],[0.]])


def test_limits_reject_oversized_requests_before_backend_allocation():
    with pytest.raises(ValueError):batch.Limits(worlds=65)
    with pytest.raises(ValueError):batch.Limits(worlds=True)
    with pytest.raises(ValueError):batch.Limits(max_gpu_mib=9000)
