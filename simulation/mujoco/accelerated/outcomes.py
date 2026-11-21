"""Privileged physical outcome metrics, explicitly excluded from control targets."""
import numpy as np


def manipulation_outcomes(model,piece,qpos,qvel,contacts,forbidden,phase,initial_z,minimum_rise_m,
                          *,hold_s=1.,maximum_slip_m=.003):
    body=model.body(piece).id;joint=model.body_jntadr[body]
    qadr=model.jnt_qposadr[joint];vadr=model.jnt_dofadr[joint]
    phases=np.asarray(phase)
    if phases.ndim==1:phases=np.repeat(phases[:,None],qpos.shape[1],axis=1)
    if phases.shape!=qpos.shape[:2]:raise ValueError('One phase label per physics step and world required')
    initial_z=np.broadcast_to(initial_z,(qpos.shape[1],))
    records=[]
    for world in range(qpos.shape[1]):
        rise=qpos[:,world,qadr+2]-initial_z[world];hold=phases[:,world]=='LIFT_HOLD'
        quaternion=qpos[:,world,qadr+3:qadr+7]
        norm=(quaternion*quaternion).sum(axis=1)
        upright=np.arccos(np.clip(1-2*(quaternion[:,1]**2+quaternion[:,2]**2)/norm,-1.,1.))
        hold_rise=rise[hold]
        drop=np.maximum.accumulate(hold_rise)-hold_rise if hold_rise.size else np.array([])
        linear=np.linalg.norm(qvel[hold,world,vadr:vadr+3],axis=1)
        angular=np.linalg.norm(qvel[hold,world,vadr+3:vadr+6],axis=1)
        record=dict(world=world,hold_duration_sim_s=float(hold.sum()*model.opt.timestep),
            maximum_rise_m=float(rise.max()),minimum_held_rise_m=float(hold_rise.min()) if hold_rise.size else None,
            maximum_hold_slip_m=float(drop.max()) if drop.size else None,
            bilateral_hold=bool(hold.any() and np.all(contacts[hold,world])),
            maximum_hold_linear_speed_m_s=float(linear.max()) if linear.size else None,
            maximum_hold_angular_speed_rad_s=float(angular.max()) if angular.size else None,
            maximum_upright_angle_rad=float(upright.max()),forbidden_contact=bool(np.any(forbidden[:,world])))
        record['success']=bool(record['hold_duration_sim_s']>=hold_s and record['bilateral_hold']
            and record['minimum_held_rise_m']>=minimum_rise_m and record['maximum_hold_slip_m']<=maximum_slip_m
            and record['maximum_hold_linear_speed_m_s']<=.01 and record['maximum_hold_angular_speed_rad_s']<=.15
            and record['maximum_upright_angle_rad']<=.15 and not record['forbidden_contact'])
        records.append(record)
    return records
