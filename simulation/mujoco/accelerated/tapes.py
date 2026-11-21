"""Independent GPU control-tape worlds with per-step physical diagnostics."""
import time

import mujoco
import numpy as np

from atom_mujoco.collision import SceneCollision
from batch import Limits,WarpBatch


def forbidden_pairs(sim,piece):
    model=sim.model;collision=SceneCollision(sim);selected=model.body(piece).id
    selected_geoms=[g for g in collision.environment if model.geom_bodyid[g]==selected]
    pads=[model.geom(f'finger_{i}_pad').id for i in (1,2)]
    others=[g for g in collision.environment if model.geom_bodyid[g]!=selected]
    supports=[g for g in others if model.geom(g).name=='board_frame' or model.geom(g).name.startswith('graveyard_support_')]
    allowed={frozenset((a,b)) for a in selected_geoms for b in (*pads,*supports)}
    pairs=collision.pairs+[(a,b) for a in selected_geoms for b in others]
    result=np.zeros(model.ngeom**2,dtype=np.int32)
    for a,b in pairs:
        if frozenset((a,b)) not in allowed:result[a*model.ngeom+b]=result[b*model.ngeom+a]=1
    return result,pads,selected


def evaluate_gpu(sim,piece,tapes,initial,max_gpu_mib):
    import warp as wp
    from cuda_rollout import apply_candidates,record_state,record_contacts,next_step
    worlds,steps,actuators=tapes.shape
    if not 1<=worlds<=64 or not 1<=steps<=20000 or actuators!=sim.model.nu or not np.isfinite(tapes).all():
        raise ValueError('Finite bounded control tapes required')
    gpu=WarpBatch(sim.model,Limits(worlds=worlds,max_worlds=64,max_gpu_mib=max_gpu_mib,nconmax=128,njmax=512))
    forbidden,pads,selected=forbidden_pairs(sim,piece);model=sim.model
    gpu.reset(initial);gpu.forward();gpu.step();gpu.health();gpu.reset(initial)
    with wp.ScopedDevice(gpu.device):
        tape=wp.array(tapes.astype(np.float32));cursor=wp.zeros(1,dtype=wp.int32)
        out_qpos=wp.empty((steps,worlds,model.nq),dtype=wp.float32);out_qvel=wp.empty((steps,worlds,model.nv),dtype=wp.float32)
        contacts=wp.zeros((steps,worlds,2),dtype=wp.int32);bad=wp.zeros((steps,worlds),dtype=wp.int32)
        flags=wp.zeros(worlds,dtype=wp.int32);bad_pairs=wp.array(forbidden)
        gpu.check_memory()
        def one():
            wp.launch(apply_candidates,dim=(worlds,model.nu),inputs=[tape,gpu.data.ctrl,cursor])
            gpu.mjw.step(gpu.gpu_model,gpu.data)
            wp.launch(record_state,dim=(worlds,max(model.nq,model.nv)),inputs=[gpu.data.qpos,gpu.data.qvel,
                out_qpos,out_qvel,gpu.data.overflow,flags,cursor,model.nq,model.nv])
            wp.launch(record_contacts,dim=gpu.data.naconmax,inputs=[gpu.data.contact.geom,gpu.data.contact.worldid,
                gpu.data.contact.dist,gpu.data.nacon,gpu.gpu_model.geom_bodyid,bad_pairs,*pads,selected,model.ngeom,contacts,bad,cursor])
            wp.launch(next_step,dim=1,inputs=[cursor])
        one();wp.synchronize_device(gpu.device);gpu.reset(initial);cursor.zero_();contacts.zero_();bad.zero_();flags.zero_()
        with wp.ScopedCapture(device=gpu.device) as capture:
            for _ in range(8):one()
        wp.synchronize_device(gpu.device);gpu.reset(initial);cursor.zero_();contacts.zero_();bad.zero_();flags.zero_()
        started=time.perf_counter()
        for _ in range(steps//8):wp.capture_launch(capture.graph)
        for _ in range(steps%8):one()
        wp.synchronize_device(gpu.device);wall=time.perf_counter()-started
        qpos,qvel=out_qpos.numpy(),out_qvel.numpy();contact=contacts.numpy();forbidden_contacts=bad.numpy();all_flags=flags.numpy()
    if np.any(all_flags):raise RuntimeError(f'Cumulative GPU flags: {all_flags.tolist()}')
    if not np.isfinite(qpos).all() or not np.isfinite(qvel).all():raise RuntimeError('Nonfinite GPU tape rollout')
    return dict(qpos=qpos,qvel=qvel,contacts=contact,forbidden=forbidden_contacts,
                wall_s=wall,health=gpu.health(),cumulative_flags=all_flags.tolist())


def evaluate_cpu(sim,piece,tape,initial):
    model=sim.model;data=mujoco.MjData(model)
    mujoco.mj_setState(model,data,initial,int(mujoco.mjtState.mjSTATE_INTEGRATION))
    forbidden,pads,selected=forbidden_pairs(sim,piece);qpos=[];qvel=[];contacts=[];bad=[]
    for command in tape:
        data.ctrl[:]=command;mujoco.mj_step(model,data)
        if np.any(data.warning.number):raise RuntimeError('Canonical CPU numerical warning')
        qpos.append(data.qpos.copy());qvel.append(data.qvel.copy());flags=[0,0];violation=False
        for contact in data.contact:
            a,b=map(int,contact.geom)
            if contact.dist>0:continue
            for index,pad in enumerate(pads):
                if a==pad and model.geom_bodyid[b]==selected or b==pad and model.geom_bodyid[a]==selected:flags[index]=1
            if forbidden[a*model.ngeom+b]:violation=True
        contacts.append(flags);bad.append(violation)
    return dict(qpos=np.asarray(qpos)[:,None,:],qvel=np.asarray(qvel)[:,None,:],
        contacts=np.asarray(contacts)[:,None,:],forbidden=np.asarray(bad)[:,None])
