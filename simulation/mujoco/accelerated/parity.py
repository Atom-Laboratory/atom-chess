"""Bounded unchanged-robot forward/single-step parity diagnostic."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import traceback

import mujoco
import numpy as np

from atom_mujoco.backend import Simulation
from batch import CpuBatch,Limits,WarpBatch,pack


TOLERANCES={
    'xpos':(1e-5,1e-4),'xquat':(1e-5,1e-4),'site_xpos':(1e-5,1e-4),
    'actuator_length':(1e-5,1e-4),'M':(1e-8,1e-5),
    'actuator_force':(1e-3,1e-3),'qfrc_actuator':(1e-3,1e-3),
    'qfrc_bias':(1e-3,1e-3),'qfrc_passive':(1e-3,1e-3),
    'qfrc_smooth':(1e-3,1e-3),'qacc_smooth':(1e-2,1e-3),
    'qfrc_constraint':(1e-1,1e-2),'qacc':(1e-1,1e-2),
}


def compare(reference,actual,absolute,relative):
    reference,actual=np.asarray(reference),np.asarray(actual)
    if reference.shape!=actual.shape or not np.isfinite(actual).all():
        return dict(passed=False,shape_error=True,reference_shape=reference.shape,actual_shape=actual.shape)
    if not reference.size:return dict(passed=True,max_abs=0.,max_normalized=0.)
    delta=abs(actual-reference);norm=delta/(absolute+relative*abs(reference))
    index=np.unravel_index(np.argmax(norm),norm.shape)
    return dict(passed=bool(norm.max()<=1),max_abs=float(delta.max()),max_normalized=float(norm[index]),
                worst_index=list(map(int,index)),reference=float(reference[index]),actual=float(actual[index]))


def cpu_contacts(model,batch):
    records=[]
    for world,data in enumerate(batch.data):
        for index,contact in enumerate(data.contact):
            force=np.zeros(6);mujoco.mj_contactForce(model,data,index,force)
            rotation=contact.frame.reshape(3,3)
            wrench=np.r_[rotation.T@force[:3],rotation.T@force[3:]]
            records.append(dict(world=world,geoms=list(map(int,contact.geom)),distance=float(contact.dist),
                margin=float(contact.includemargin),normal_force=float(force[0]),world_wrench=wrench.tolist()))
    return records


def gpu_contacts(batch):
    from mujoco_warp._src.types import ContactType
    wp,mjw=batch.wp,batch.mjw;data=batch.data
    count=min(int(data.nacon.numpy()[0]),data.naconmax)
    with wp.ScopedDevice(batch.device):
        ids=wp.array(np.arange(count,dtype=np.int32));forces=wp.empty(count,dtype=wp.spatial_vector)
        mjw.contact_force(batch.gpu_model,data,ids,True,forces)
        local_forces=wp.empty(count,dtype=wp.spatial_vector)
        mjw.contact_force(batch.gpu_model,data,ids,False,local_forces)
    arrays={name:getattr(data.contact,name).numpy()[:count] for name in ('type','worldid','geom','dist','includemargin')}
    wrench,local=forces.numpy(),local_forces.numpy();records=[]
    for index in range(count):
        if not arrays['type'][index]&int(ContactType.CONSTRAINT|ContactType.PASSIVE):continue
        records.append(dict(world=int(arrays['worldid'][index]),geoms=arrays['geom'][index].tolist(),
            distance=float(arrays['dist'][index]),margin=float(arrays['includemargin'][index]),
            normal_force=float(local[index,0]),world_wrench=wrench[index].tolist()))
    return records


def contact_summary(cpu,gpu):
    def aggregate(records):
        groups={};ambiguous=[]
        for record in records:
            if abs(record['distance']-record['margin'])<=1e-5:
                ambiguous.append(record);continue
            key=(record['world'],*sorted(record['geoms']))
            group=groups.setdefault(key,dict(count=0,normal=0.,wrench=np.zeros(6)))
            group['count']+=1;group['normal']+=record['normal_force']
            sign=1 if record['geoms'][0]<record['geoms'][1] else -1
            group['wrench']+=sign*np.asarray(record['world_wrench'])
        return groups,ambiguous
    a,ambiguous_cpu=aggregate(cpu);b,ambiguous_gpu=aggregate(gpu);pairs=[]
    for key in sorted(a.keys()|b.keys()):
        left=a.get(key,dict(count=0,normal=0.,wrench=np.zeros(6)))
        right=b.get(key,dict(count=0,normal=0.,wrench=np.zeros(6)))
        pairs.append(dict(world=key[0],geoms=key[1:],cpu_count=left['count'],gpu_count=right['count'],
            normal_force=compare(left['normal'],right['normal'],.005,.05),
            linear_force=compare(left['wrench'][:3],right['wrench'][:3],.005,.05),
            cpu_wrench=left['wrench'].tolist(),gpu_wrench=right['wrench'].tolist()))
    return dict(pairs=pairs,ambiguous_cpu=ambiguous_cpu,ambiguous_gpu=ambiguous_gpu,
                passed=all(r['cpu_count']==r['gpu_count'] and r['normal_force']['passed'] and r['linear_force']['passed'] for r in pairs))


def worker(args):
    config=json.loads(args.config.read_text(encoding='utf-8-sig'))
    sim=Simulation(config['bundle']);model=sim.model
    parked=mujoco.MjData(model);parked.qpos[sim.qadr]=sim.validate(config['initial_command'])
    parked.ctrl[:]=config['initial_command'];mujoco.mj_forward(model,parked)
    states=[parked];labels=['parked, explicit default hidden state']
    if args.snapshot:
        snapshot=json.loads(args.snapshot.read_text());restored=mujoco.MjData(model)
        restored.qpos[:]=snapshot['qpos'];restored.qvel[:]=snapshot['qvel'];restored.ctrl[:]=snapshot['ctrl']
        restored.time=snapshot['time_s'];mujoco.mj_forward(model,restored)
        states.append(restored);labels.append('restored snapshot, explicit default omitted hidden state')
    limits=Limits(worlds=len(states),max_worlds=4,max_gpu_mib=args.max_gpu_mib,
                  nconmax=max(64,2*max(d.ncon for d in states)),njmax=max(256,2*max(d.nefc for d in states)))
    initial=pack(model,states)
    np.savez_compressed(args.output/'initial-states.npz',integration=initial,signature=int(mujoco.mjtState.mjSTATE_INTEGRATION))
    cpu=CpuBatch(model,limits);gpu=WarpBatch(model,limits)
    cpu.reset(initial);gpu.reset(initial)
    state_error=compare(initial,gpu.state(),1e-6,1e-6)
    cpu.forward();gpu.forward();health=gpu.health()
    fields=gpu.arrays(TOLERANCES)
    metrics={}
    for name,(absolute,relative) in TOLERANCES.items():
        reference=cpu.arrays([name])[name];actual=fields[name]
        if name=='xquat':actual*=np.where(np.sum(reference*actual,axis=-1,keepdims=True)<0,-1.,1.)
        metrics[name]=compare(reference,actual,absolute,relative)
    contacts=contact_summary(cpu_contacts(model,cpu),gpu_contacts(gpu))
    # Reset identical complete state before a single integration step.
    cpu.reset(initial);gpu.reset(initial);cpu.step();gpu.step();step_health=gpu.health()
    stepped=gpu.arrays(('qpos','qvel'))
    step={name:compare(cpu.arrays([name])[name],stepped[name],1e-5 if name=='qpos' else 1e-3,1e-4)
          for name in ('qpos','qvel')}
    # Reset only world zero; unchanged worlds must remain bit-identical.
    before=gpu.state();active=np.zeros(limits.worlds,dtype=bool);active[0]=True
    gpu.reset(initial,active);after=gpu.state()
    isolated=bool(np.array_equal(before[1:],after[1:]))
    passed=state_error['passed'] and all(r['passed'] for r in metrics.values()) and contacts['passed'] and all(r['passed'] for r in step.values()) and isolated
    report=dict(schema=1,experiment='EXP-0003',status='FORWARD_STEP_SCREEN_PASSED' if passed else 'PARITY_DIFFERENCES_REQUIRE_ANALYSIS',
        scope='diagnostic screen only; no complete grasp replay, CEM or policy qualification',
        versions={name:importlib.metadata.version(name) for name in ('mujoco','mujoco-warp','warp-lang')},
        labels=labels,model_sha256=hashlib.sha256((Path(config['bundle'])/'model.xml').read_bytes()).hexdigest(),
        config_sha256=hashlib.sha256(args.config.read_bytes()).hexdigest(),
        snapshot_sha256=hashlib.sha256(args.snapshot.read_bytes()).hexdigest() if args.snapshot else None,
        initial_state=state_error,forward=metrics,contacts=contacts,single_step=step,reset_isolation=isolated,
        initial_health=health,step_health=step_health,limits=vars(limits),
        tolerances={name:dict(absolute=a,relative=r) for name,(a,r) in TOLERANCES.items()},
        limitations=['Unconditioned dynamics screen; affine float32 and mass conditioning must be analyzed before attributing differences to the backend.',
                     'Snapshot omitted hidden state was explicitly reset; not historical force reconstruction.',
                     'No dedicated lifted hold or full trajectory was replayed.'])
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--snapshot',type=Path)
    parser.add_argument('--output',type=Path);parser.add_argument('--max-wall-s',type=float,default=600.)
    parser.add_argument('--max-gpu-mib',type=int,default=2048)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:
        try:worker(args)
        except Exception as error:
            (args.output/'failure.json').write_text(json.dumps(dict(status='FAILED',error=str(error),traceback=traceback.format_exc()),indent=2))
            raise
        return
    from experiment import bounded_run
    arguments=['--config',str(args.config.resolve(strict=True)),'--max-gpu-mib',str(args.max_gpu_mib)]
    if args.snapshot:arguments+=['--snapshot',str(args.snapshot.resolve(strict=True))]
    sources=[Path(__file__).with_name(name) for name in ('batch.py','requirements-windows-py312.lock')]
    output,report=bounded_run(__file__,arguments,experiment='EXP-0003',output=args.output,sources=sources,
        max_wall_s=args.max_wall_s,request=dict(config=str(args.config.resolve()),snapshot=str(args.snapshot),max_gpu_mib=args.max_gpu_mib))
    print(json.dumps(dict(status=report['status'],output=str(output),reset_isolation=report['reset_isolation'])),flush=True)
    if report['status'] != 'FORWARD_STEP_SCREEN_PASSED':raise SystemExit(2)


if __name__=='__main__':main()
