"""Exact canonical transition replay and bounded full recorded-control GPU replay."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback

import mujoco
import numpy as np

from atom_mujoco.backend import Simulation
from atom_mujoco.collision import SceneCollision
from batch import Limits,WarpBatch,SIGNATURE,pack


def load_recording(path,model,expected_model_hash,max_steps):
    metadata=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=metadata['sha256']:raise ValueError('Recording SHA-256 mismatch')
    if metadata['model_sha256']!=expected_model_hash or metadata.get('unfinished_transition'):
        raise ValueError('Matching complete model recording required')
    with np.load(path,allow_pickle=False) as data:
        before,after,phase=data['before'],data['after'],data['phase']
        if int(data['signature'])!=SIGNATURE:raise ValueError('Complete integration signature required')
    shape=(len(before),mujoco.mj_stateSize(model,SIGNATURE))
    if (not 1<=len(before)<=max_steps or before.shape!=shape or after.shape!=shape
            or len(phase)!=len(before) or not np.isfinite(before).all() or not np.isfinite(after).all()):
        raise ValueError('Finite bounded matching transition arrays required')
    return before,after,phase,metadata


def worker(args):
    import warp as wp
    from cuda_rollout import apply_tape,record_state,record_contacts,next_step
    config=json.loads(args.config.read_text(encoding='utf-8-sig'));sim=Simulation(config['bundle']);model=sim.model
    before,after,phase,metadata=load_recording(args.transitions,model,sim.manifest['model_sha256'],args.max_steps)
    steps=len(before);scratch=mujoco.MjData(model);controls=np.empty((steps,model.nu))
    expected_qpos=np.empty((steps,model.nq));expected_qvel=np.empty((steps,model.nv))
    exact_errors=[];cpu_contacts_peak=0;cpu_constraints_peak=0
    for index in range(steps):
        mujoco.mj_setState(model,scratch,before[index],SIGNATURE);controls[index]=scratch.ctrl
        mujoco.mj_step(model,scratch)
        actual=pack(model,[scratch])[0]
        error=float(np.max(abs(actual-after[index])));exact_errors.append(error)
        cpu_contacts_peak=max(cpu_contacts_peak,scratch.ncon);cpu_constraints_peak=max(cpu_constraints_peak,scratch.nefc)
        mujoco.mj_setState(model,scratch,after[index],SIGNATURE)
        expected_qpos[index],expected_qvel[index]=scratch.qpos,scratch.qvel
    if any(error!=0. for error in exact_errors):raise RuntimeError(f'Canonical transition replay not bit-identical: {max(exact_errors)}')
    # Verify a continuous command tape, separately from independent one-step replay.
    mujoco.mj_setState(model,scratch,before[0],SIGNATURE);cpu_rollout_error=0.
    for index in range(steps):
        scratch.ctrl[:]=controls[index];mujoco.mj_step(model,scratch)
        cpu_rollout_error=max(cpu_rollout_error,float(np.max(abs(scratch.qpos-expected_qpos[index]))))
    if cpu_rollout_error>1e-10:raise RuntimeError(f'Unrecorded external state change in tape: {cpu_rollout_error}')
    limits=Limits(worlds=args.worlds,max_worlds=64,max_gpu_mib=args.max_gpu_mib,
        nconmax=max(64,2*cpu_contacts_peak),njmax=max(256,2*cpu_constraints_peak))
    gpu=WarpBatch(model,limits);initial=np.repeat(before[:1],args.worlds,axis=0)
    gpu.reset(initial);gpu.forward();gpu.step();gpu.health();gpu.reset(initial)
    collision=SceneCollision(sim);selected=model.body(config['piece']).id
    pieces=[g for g in collision.environment if model.geom_bodyid[g]==selected]
    pads=[model.geom(f'finger_{i}_pad').id for i in (1,2)]
    others=[g for g in collision.environment if model.geom_bodyid[g]!=selected]
    supports=[g for g in others if model.geom(g).name=='board_frame' or model.geom(g).name.startswith('graveyard_support_')]
    allowed={frozenset((a,b)) for a in pieces for b in (*pads,*supports)}
    pairs=collision.pairs+[(a,b) for a in pieces for b in others]
    forbidden_pairs=np.zeros(model.ngeom**2,dtype=np.int32)
    for a,b in pairs:
        if frozenset((a,b)) not in allowed:forbidden_pairs[a*model.ngeom+b]=forbidden_pairs[b*model.ngeom+a]=1
    with wp.ScopedDevice(gpu.device):
        tape=wp.array(controls.astype(np.float32));cursor=wp.zeros(1,dtype=wp.int32)
        out_qpos=wp.empty((steps,args.worlds,model.nq),dtype=wp.float32)
        out_qvel=wp.empty((steps,args.worlds,model.nv),dtype=wp.float32)
        contacts=wp.zeros((steps,args.worlds,2),dtype=wp.int32);forbidden=wp.zeros((steps,args.worlds),dtype=wp.int32)
        flags=wp.zeros(args.worlds,dtype=wp.int32);bad_pairs=wp.array(forbidden_pairs)
        def one():
            wp.launch(apply_tape,dim=(args.worlds,model.nu),inputs=[tape,gpu.data.ctrl,cursor])
            gpu.mjw.step(gpu.gpu_model,gpu.data)
            wp.launch(record_state,dim=(args.worlds,max(model.nq,model.nv)),inputs=[gpu.data.qpos,gpu.data.qvel,
                out_qpos,out_qvel,gpu.data.overflow,flags,cursor,model.nq,model.nv])
            wp.launch(record_contacts,dim=gpu.data.naconmax,inputs=[gpu.data.contact.geom,gpu.data.contact.worldid,
                gpu.data.contact.dist,gpu.data.nacon,gpu.gpu_model.geom_bodyid,bad_pairs,*pads,selected,model.ngeom,
                contacts,forbidden,cursor])
            wp.launch(next_step,dim=1,inputs=[cursor])
        # Warm up kernels without advancing the dataset cursor used for measurement.
        one();wp.synchronize_device(gpu.device);gpu.reset(initial);cursor.zero_();contacts.zero_();forbidden.zero_();flags.zero_()
        with wp.ScopedCapture(device=gpu.device) as capture:
            for _ in range(8):one()
        wp.synchronize_device(gpu.device)
        # Capture may execute work; reset every tape/output accumulator explicitly.
        gpu.reset(initial);cursor.zero_();contacts.zero_();forbidden.zero_();flags.zero_()
        started=time.perf_counter()
        for _ in range(steps//8):wp.capture_launch(capture.graph)
        for _ in range(steps%8):one()
        wp.synchronize_device(gpu.device);rollout_wall=time.perf_counter()-started
        qpos,qvel=out_qpos.numpy(),out_qvel.numpy();contact_array=contacts.numpy();bad=forbidden.numpy();all_flags=flags.numpy()
    if np.any(all_flags):raise RuntimeError(f'Cumulative GPU overflow/convergence flags: {all_flags.tolist()}')
    health=gpu.health()
    if not np.isfinite(qpos).all() or not np.isfinite(qvel).all():raise RuntimeError('Nonfinite GPU trajectory')
    body_joint=int(model.body_jntadr[selected]);piece_address=int(model.jnt_qposadr[body_joint])
    mujoco.mj_setState(model,scratch,before[0],SIGNATURE)
    initial_piece_z=float(scratch.qpos[piece_address+2])
    hold_mask=phase=='LIFT_HOLD';rise=qpos[:,:,piece_address+2]-initial_piece_z
    hold_rise=rise[hold_mask];hold_contacts=contact_array[hold_mask]
    from atom_mujoco.autonomous_scene import collision_height
    height=collision_height(model,config['piece'])
    from outcomes import manipulation_outcomes
    outcomes=manipulation_outcomes(model,config['piece'],qpos,qvel,contact_array,bad,phase,initial_piece_z,height)
    held=all(outcome['success'] for outcome in outcomes)
    max_slip=float(np.max(np.maximum.accumulate(hold_rise,axis=0)-hold_rise)) if hold_rise.size else None
    qpos_error=np.max(abs(qpos-expected_qpos[:,None,:]),axis=(0,2))
    qvel_error=np.max(abs(qvel-expected_qvel[:,None,:]),axis=(0,2))
    passed=bool(np.all(qpos_error<=1e-3) and np.all(qvel_error<=.05) and held
        and max_slip<=.003 and not np.any(bad))
    np.savez_compressed(args.output/'gpu-trajectory.npz',qpos=qpos,qvel=qvel,contacts=contact_array,
        forbidden=bad,phase=phase,rise_m=rise)
    report=dict(schema=1,experiment='EXP-0004',status='RECORDED_LIFT_REPLAY_PASSED' if passed else 'REPLAY_DIFFERENCES_REQUIRE_ANALYSIS',
        scope='recorded canonical controls; not autonomous GPU vision or learned grasp policy',
        model_sha256=sim.manifest['model_sha256'],recording=metadata,worlds=args.worlds,physics_steps=steps,
        cpu_transition_max_error=max(exact_errors),cpu_continuous_qpos_max_error=cpu_rollout_error,
        gpu_qpos_max_abs_error_by_world=qpos_error.tolist(),gpu_qvel_max_abs_error_by_world=qvel_error.tolist(),
        tolerances=dict(qpos_mixed_units=1e-3,qvel_mixed_units=.05),minimum_rise_m=height,
        lift_hold_steps=int(hold_mask.sum()),lift_hold_sim_s=float(hold_mask.sum()*model.opt.timestep),
        lift_hold_min_rise_m=float(hold_rise.min()) if hold_rise.size else None,
        lift_hold_max_slip_m=max_slip,lift_hold_contacts_retained=bool(np.all(hold_contacts)) if hold_contacts.size else False,
        forbidden_contact_steps=int(np.any(bad,axis=1).sum()),health=health,cumulative_flags=all_flags.tolist(),
        outcomes=outcomes,
        rollout_wall_s=rollout_wall,
        limitations=['GPU follows a prerecorded command tape, with privileged evaluation only.',
            'Robot self-contact masks exclude some pairs; the original canonical sweeps remain distinct from GPU engine contacts.',
            'This replay does not qualify crowded manipulation, visual outcome verification, CEM or policy training.'])
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--transitions',type=Path,required=True)
    parser.add_argument('--worlds',type=int,default=1);parser.add_argument('--max-steps',type=int,default=100000)
    parser.add_argument('--max-gpu-mib',type=int,default=2048);parser.add_argument('--max-wall-s',type=float,default=600.)
    parser.add_argument('--output',type=Path);parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if not 1<=args.worlds<=64 or not 1<=args.max_steps<=100000:parser.error('Use 1..64 worlds and a step budget <=100000')
    if args.worker:
        try:worker(args)
        except Exception as error:
            (args.output/'failure.json').write_text(json.dumps(dict(status='FAILED',error=str(error),traceback=traceback.format_exc()),indent=2))
            raise
        return
    from experiment import bounded_run
    arguments=['--config',str(args.config.resolve(strict=True)),'--transitions',str(args.transitions.resolve(strict=True)),
        '--worlds',str(args.worlds),'--max-steps',str(args.max_steps),'--max-gpu-mib',str(args.max_gpu_mib)]
    output,report=bounded_run(__file__,arguments,experiment='EXP-0004',output=args.output,
        sources=[Path(__file__).with_name(n) for n in ('batch.py','cuda_rollout.py','outcomes.py','requirements-windows-py312.lock')],
        max_wall_s=args.max_wall_s,request=dict(config=str(args.config),transitions=str(args.transitions),worlds=args.worlds))
    print(json.dumps(dict(status=report['status'],output=str(output))),flush=True)
    if report['status']!='RECORDED_LIFT_REPLAY_PASSED':raise SystemExit(2)


if __name__=='__main__':main()
