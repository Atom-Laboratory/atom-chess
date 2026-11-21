import importlib.util
from pathlib import Path

import mujoco
import numpy as np


spec=importlib.util.spec_from_file_location('physical_outcomes',Path(__file__).resolve().parents[1]/'outcomes.py')
outcomes=importlib.util.module_from_spec(spec);spec.loader.exec_module(outcomes)


def test_held_height_reward_alone_does_not_override_contact_topple_or_slip_failure():
    model=mujoco.MjModel.from_xml_string('<mujoco><option timestep=".01"/><worldbody><body name="piece"><freejoint/><geom size=".01" mass=".02"/></body></worldbody></mujoco>')
    positions=np.zeros((100,3,7));positions[:,:,2]=.05;positions[:,:,3]=1.
    velocity=np.zeros((100,3,6));contact=np.ones((100,3,2),dtype=int);bad=np.zeros((100,3),dtype=int)
    phase=np.array(['LIFT_HOLD']*100)
    contact[50,1,1]=0;bad[70,2]=1
    result=outcomes.manipulation_outcomes(model,'piece',positions,velocity,contact,bad,phase,0.,.032)
    assert [r['success'] for r in result]==[True,False,False]
    positions[-1,0,2]=.04  # Still high, but 10 mm slip violates the 3 mm condition.
    assert not outcomes.manipulation_outcomes(model,'piece',positions,velocity,contact,bad,phase,0.,.032)[0]['success']
