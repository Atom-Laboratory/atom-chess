"""Bounded Stage A CEM: native-IK screened isolated close/lift/hold plans."""
import argparse
import csv
import gc
import hashlib
import json
from pathlib import Path
import time
import traceback

import mujoco
import numpy as np

from atom_mujoco.backend import Simulation
from atom_mujoco.native_motion import NativeMotion,commanded_elbow_down
from atom_mujoco.motion_controller import MotionController
from atom_mujoco.collision import SceneCollision,SweptChecker
from atom_mujoco.autonomous_control import control_rates
from atom_mujoco.autonomous_scene import collision_height
from atom_mujoco.grasp_geometry import grasp_geometry
from atom_mujoco.approach_planner import plan_identity
from batch import SIGNATURE
from cem_core import Distribution,LOWER,UPPER,rank
from outcomes import manipulation_outcomes
from replay import load_recording
from tapes import evaluate_gpu,evaluate_cpu,forbidden_pairs


def segment(start,end,speed,dt):
    duration=max(dt,1.875*float(np.max(abs(end-start)/speed)))
    count=int(np.ceil(duration/dt));t=np.arange(1,count+1)/count
    weight=10*t**3-15*t**4+6*t**5
    return start[None,:]+weight[:,None]*(end-start)[None,:]


def validated_reference(config,sim,directory):
    reference=json.loads((directory/'local-report.json').read_text())
    handoff=json.loads((directory/'handoff.json').read_text());plan=handoff['plan']
    source=next(stage['target'] for stage in reference['stages'] if stage['name']=='DESCEND')
    if (not reference.get('lift_success') or not reference.get('lift_hold',{}).get('confirmed')
            or plan.get('signature')!=plan_identity(plan) or plan.get('status')!='PLANNED'
            or plan.get('model_sha256')!=sim.manifest['model_sha256'] or plan.get('piece')!=config['piece']
            or plan.get('source')!=config['source'] or not np.array_equal(source[:2],plan['source_xy_m'])
            or not handoff.get('arrival_perception',{}).get('source_localized')):
        raise ValueError('Verified held-lift and matching signed camera-derived source required')
    return reference


def candidate(sim,motion,config,reference,initial,values,geometry_fn,max_duration):
    # All target XY values originate from the signed camera/local diagnostic.
    source=next(s['target'] for s in reference['stages'] if s['name']=='DESCEND')
    xyz=np.asarray(source[:3]);wrist=float(source[3]);aperture=float(source[4])
    load,close_fraction,lift_fraction=values
    geometry=geometry_fn(sim,config['piece'],xyz[2]-float(sim.model.geom(config['piece']+'_head').pos[2]),'head',load)
    scratch=mujoco.MjData(sim.model);scratch.qpos[sim.qadr]=motion.solve(xyz,aperture,wrist=wrist)
    elbow=commanded_elbow_down(sim,scratch.qpos[sim.qadr],scratch)
    start=sim.validate(motion.solve(xyz,aperture,wrist=wrist,elbow_down=elbow))
    close=sim.validate(motion.solve(xyz,geometry['closing_target_m'],wrist=wrist,elbow_down=elbow))
    height=collision_height(sim.model,config['piece']);lift_xyz=xyz+np.array([0.,0.,1.5*height])
    lift=sim.validate(motion.solve(lift_xyz,geometry['closing_target_m'],wrist=wrist,elbow_down=elbow))
    collision=SceneCollision(sim);selected=sim.model.body(config['piece']).id
    selected_geoms=[g for g in collision.environment if sim.model.geom_bodyid[g]==selected]
    others=[g for g in collision.environment if sim.model.geom_bodyid[g]!=selected]
    pads=[sim.model.geom(f'finger_{i}_pad').id for i in (1,2)]
    supports=[g for g in others if sim.model.geom(g).name=='board_frame' or sim.model.geom(g).name.startswith('graveyard_support_')]
    allowed=[(a,b) for a in selected_geoms for b in (*pads,*supports)]
    checker=SweptChecker(sim.model,sim.data.qpos,sim.joint_ids,collision.pairs+[(a,b) for a in selected_geoms for b in others])
    mujoco.mj_setState(sim.model,sim.data,initial,SIGNATURE);mujoco.mj_forward(sim.model,sim.data)
    checker.initial[:]=sim.data.qpos
    fingers={sim.model.geom_bodyid[g] for g in pads}
    margins={frozenset((a,b)):0. for a in collision.robot if sim.model.geom_bodyid[a] in fingers
        and sim.model.geom(a).name.endswith('_collision_hull') for b in selected_geoms}
    failure=checker.interval(start,close,allowed=allowed,pair_clearances=margins,prune_spheres=True)
    if failure:raise ValueError('Closure sweep rejected: '+json.dumps(failure))
    # Carried envelope is independent privileged safety data, never an IK target.
    scratch.qpos[:]=sim.data.qpos;scratch.qpos[sim.qadr]=close;mujoco.mj_forward(sim.model,scratch)
    site=sim.model.site('grasp_center').id;rotation=scratch.site_xmat[site].reshape(3,3)
    offset=rotation.T@(sim.data.xpos[selected]-scratch.site_xpos[site])
    relative=rotation.T@sim.data.xmat[selected].reshape(3,3)
    address=sim.model.jnt_qposadr[sim.model.body_jntadr[selected]]
    coefficients=checker.coefficients.copy()
    for geom in selected_geoms:
        coefficients[geom]=np.max(checker.coefficients[collision.robot],axis=0)
        for i,joint in enumerate(sim.joint_ids):
            if sim.model.jnt_type[joint]==mujoco.mjtJoint.mjJNT_HINGE:
                coefficients[geom,i]+=2*(np.linalg.norm(offset)+sim.model.geom_rbound[geom])
    def held(data):
        rotation=data.site_xmat[site].reshape(3,3)
        data.qpos[address:address+3]=data.site_xpos[site]+rotation@offset
        mujoco.mju_mat2Quat(data.qpos[address+3:address+7],(rotation@relative).reshape(-1))
    failure=checker.interval(close,lift,allowed=allowed,pair_clearances=margins,configure=held,
        extra_coefficients=coefficients,prune_spheres=True)
    if failure:raise ValueError('Carried lift sweep rejected: '+json.dumps(failure))
    from types import SimpleNamespace
    base=SimpleNamespace(sim=sim,motion=motion,dwell=config['dwell_steps'])
    vertical_rate=control_rates(base)[2]*.25/1.875*lift_fraction
    close_speed=sim.speed.copy();close_speed[3:5]*=close_fraction
    lift_speed=sim.speed.copy();lift_speed[1]=min(lift_speed[1],vertical_rate)
    dt=sim.model.opt.timestep
    close_path=segment(start,close,close_speed,dt);close_hold=np.repeat(close[None,:],int(np.ceil(.2/dt)),axis=0)
    lift_path=segment(close,lift,lift_speed,dt);hold=np.repeat(lift[None,:],int(np.ceil(1./dt)),axis=0)
    desired=np.concatenate((close_path,close_hold,lift_path,hold))
    if len(desired)*dt>max_duration:raise ValueError('Candidate trajectory exceeds duration budget')
    controller=MotionController(sim);bias=controller.command(start)-start
    if not np.allclose(controller.command(lift)-lift,bias,rtol=0,atol=1e-10):
        raise ValueError('This pilot requires constant static gravity bias along its fixed planar pose')
    commands=np.clip(desired+bias,sim.lower,sim.upper)
    if np.any(abs(np.diff(commands,axis=0))>sim.speed*dt+1e-10):raise ValueError('Candidate actuator speed limit exceeded')
    phase=np.array(['CLOSE']*len(close_path)+['HOLD_CLOSE']*len(close_hold)+['LIFT']*len(lift_path)+['LIFT_HOLD']*len(hold))
    return commands,phase,dict(duration_s=len(commands)*dt,source_xy_m=xyz[:2].tolist(),
        target_source='camera-derived reference diagnostic',native_ik=True,geometry=geometry,
        sweep_samples=checker.samples,selected_finger_margin_m=0.)


def worker(args):
    config=json.loads(args.config.read_text(encoding='utf-8-sig'));sim=Simulation(config['bundle'])
    if len(sim.manifest['pieces'])!=1:raise ValueError('Stage A pilot requires the isolated fixture; crowded operation is not qualified')
    reference=validated_reference(config,sim,args.reference)
    before,_,phases,recording=load_recording(args.reference/'physics-transitions.npz',sim.model,sim.manifest['model_sha256'],100000)
    initial=before[np.flatnonzero(phases=='CLOSE')[0]]
    motion=NativeMotion(config['motion_library'],sim)
    distribution=Distribution(args.seed)
    identity=dict(model_sha256=sim.manifest['model_sha256'],recording_sha256=recording['sha256'],
        reference_report_sha256=hashlib.sha256((args.reference/'local-report.json').read_bytes()).hexdigest(),
        handoff_sha256=hashlib.sha256((args.reference/'handoff.json').read_bytes()).hexdigest(),
        config_sha256=hashlib.sha256(args.config.read_bytes()).hexdigest(),
        motion_library_sha256=hashlib.sha256(Path(config['motion_library']).read_bytes()).hexdigest())
    import atom_mujoco
    runtime_sources={path.name:hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(Path(atom_mujoco.__file__).parent.glob('*.py'))}
    if args.resume:
        checkpoint=json.loads(args.resume.read_text())
        if checkpoint['identity']!=identity:raise ValueError('CEM resume input identity mismatch')
        distribution.restore(checkpoint['distribution'])
    records=[];best=None;best_tape=best_phase=None;simulations=0
    selected=sim.model.body(config['piece']).id;address=sim.model.jnt_qposadr[sim.model.body_jntadr[selected]]
    mujoco.mj_setState(sim.model,sim.data,initial,SIGNATURE);initial_z=float(sim.data.qpos[address+2])
    for _ in range(args.generations):
        generation=distribution.generation;parameters=distribution.ask(args.population)
        generation_records=[];accepted=[];tapes=[];labels=[]
        for index,values in enumerate(parameters):
            record=dict(generation=generation,index=index,parameters=values.tolist(),geometry_valid=False)
            try:
                tape,phase,metadata=candidate(sim,motion,config,reference,initial,values,grasp_geometry,args.max_duration_s)
                record.update(metadata,geometry_valid=True);accepted.append(index);tapes.append(tape);labels.append(phase)
            except ValueError as error:record['failure']=str(error)
            generation_records.append(record)
        if accepted:
            simulations+=len(accepted)
            if simulations>args.max_simulations:raise RuntimeError('CEM simulation budget exhausted')
            length=max(map(len,tapes));batched=np.empty((len(tapes),length,sim.model.nu));stage=np.full((length,len(tapes)),'PADDING',dtype='<U16')
            for world,(tape,phase) in enumerate(zip(tapes,labels)):
                batched[world,:len(tape)]=tape;batched[world,len(tape):]=tape[-1];stage[:len(tape),world]=phase
            result=evaluate_gpu(sim,config['piece'],batched,np.repeat(initial[None,:],len(accepted),axis=0),args.max_gpu_mib)
            outcomes=manipulation_outcomes(sim.model,config['piece'],result['qpos'],result['qvel'],result['contacts'],result['forbidden'],
                stage,initial_z,collision_height(sim.model,config['piece']))
            for world,index in enumerate(accepted):generation_records[index]['outcome']=outcomes[world]
            np.savez_compressed(args.output/f'generation-{generation}-tapes.npz',controls=batched,phase=stage,initial=initial,
                parameters=parameters[accepted],accepted_indices=accepted)
            np.savez_compressed(args.output/f'generation-{generation}-physics.npz',qpos=result['qpos'],qvel=result['qvel'],
                contacts=result['contacts'],forbidden=result['forbidden'],phase=stage,accepted_indices=accepted)
            (args.output/f'generation-{generation}-health.json').write_text(json.dumps(dict(
                gpu_rollout_wall_s=result['wall_s'],health=result['health'],cumulative_flags=result['cumulative_flags']),indent=2))
        order=distribution.update(parameters,generation_records)
        winner=generation_records[order[0]]
        if best is None or rank(winner)>rank(best):
            best=dict(winner)
            if winner['geometry_valid']:
                index=accepted.index(order[0]);best_tape=tapes[index].copy();best_phase=labels[index].copy()
        records.extend(generation_records)
        with (args.output/'candidate-metrics.csv').open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=['generation','candidate','load_factor','close_speed_fraction','lift_rate_fraction',
                'geometry_valid','physical_success','maximum_rise_m','maximum_hold_slip_m','forbidden_contact','duration_s','failure'])
            writer.writeheader()
            for item in records:
                outcome=item.get('outcome',{})
                writer.writerow(dict(generation=item['generation'],candidate=item['index'],load_factor=item['parameters'][0],
                    close_speed_fraction=item['parameters'][1],lift_rate_fraction=item['parameters'][2],geometry_valid=item['geometry_valid'],
                    physical_success=outcome.get('success',False),maximum_rise_m=outcome.get('maximum_rise_m'),
                    maximum_hold_slip_m=outcome.get('maximum_hold_slip_m'),forbidden_contact=outcome.get('forbidden_contact'),
                    duration_s=item.get('duration_s'),failure=item.get('failure')))
        (args.output/f'generation-{generation}.json').write_text(json.dumps(generation_records,indent=2),encoding='utf-8')
        (args.output/f'checkpoint-{generation}.json').write_text(json.dumps(dict(identity=identity,distribution=distribution.state(),
            best=best,simulations_this_run=simulations,runtime_source_sha256=runtime_sources),indent=2),encoding='utf-8')
        print(f'[ATOM CEM] generation {generation} | geometry {len(accepted)}/{args.population} | held lifts '
              f'{sum(r.get("outcome",{}).get("success",False) for r in generation_records)} | simulations {simulations}/{args.max_simulations}',flush=True)
        del tapes,labels;gc.collect()
    canonical=None
    if best_tape is not None:
        result=evaluate_cpu(sim,config['piece'],best_tape,initial)
        canonical=manipulation_outcomes(sim.model,config['piece'],result['qpos'],result['qvel'],result['contacts'],result['forbidden'],
            best_phase,initial_z,collision_height(sim.model,config['piece']))[0]
        np.savez_compressed(args.output/'best-candidate.npz',controls=best_tape,phase=best_phase,initial=initial,
            qpos=result['qpos'],qvel=result['qvel'],contacts=result['contacts'],forbidden=result['forbidden'])
    report=dict(schema=1,experiment='EXP-0006',status='CEM_CPU_VERIFIED_CANDIDATE' if canonical and canonical['success'] else 'CEM_PILOT_NO_VERIFIED_WINNER',
        scope='isolated Stage A fixed camera-derived entry; not learned policy or crowded/full manipulation',
        identity=identity,seed=args.seed,parameter_names=['closing_load_factor','closing_speed_fraction','lift_rate_fraction'],
        runtime_source_sha256=runtime_sources,resume_from=str(args.resume) if args.resume else None,
        bounds=dict(lower=LOWER.tolist(),upper=UPPER.tolist()),population=args.population,generations=args.generations,
        total_gpu_simulations=simulations,best=best,canonical_winner=canonical,distribution=distribution.state(),
        limitations=['No initial-state randomization or held-out task generalization in this pilot.',
            'GPU engine contacts do not replace independent planner self-collision sweeps.',
            'Vision provides frozen target XY; no live multiworld camera pipeline or RL training.'])
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--population',type=int,default=8);parser.add_argument('--generations',type=int,default=2)
    parser.add_argument('--max-simulations',type=int,default=16);parser.add_argument('--max-duration-s',type=float,default=40.)
    parser.add_argument('--seed',type=int,default=970300);parser.add_argument('--max-gpu-mib',type=int,default=2048)
    parser.add_argument('--max-wall-s',type=float,default=300.);parser.add_argument('--resume',type=Path)
    parser.add_argument('--output',type=Path);parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if not 4<=args.population<=64 or not 1<=args.generations<=20 or not 1<=args.max_simulations<=1024 or not 1<=args.max_duration_s<=40:
        parser.error('Bounded population 4..64, generations 1..20, simulations <=1024 and duration <=40 s required')
    if args.worker:
        try:worker(args)
        except Exception as error:
            (args.output/'failure.json').write_text(json.dumps(dict(status='FAILED',error=str(error),traceback=traceback.format_exc()),indent=2))
            raise
        return
    from experiment import bounded_run
    arguments=['--config',str(args.config.resolve(strict=True)),'--reference',str(args.reference.resolve(strict=True)),
        '--population',str(args.population),'--generations',str(args.generations),'--max-simulations',str(args.max_simulations),
        '--max-duration-s',str(args.max_duration_s),'--seed',str(args.seed),'--max-gpu-mib',str(args.max_gpu_mib)]
    if args.resume:arguments+=['--resume',str(args.resume.resolve(strict=True))]
    sources=[Path(__file__).with_name(n) for n in ('cem_core.py','batch.py','cuda_rollout.py','tapes.py','outcomes.py','replay.py','requirements-windows-py312.lock')]
    output,report=bounded_run(__file__,arguments,experiment='EXP-0006',output=args.output,sources=sources,
        max_wall_s=args.max_wall_s,request=dict(population=args.population,generations=args.generations,max_simulations=args.max_simulations,
            max_duration_s=args.max_duration_s,seed=args.seed,max_gpu_mib=args.max_gpu_mib))
    print(json.dumps(dict(status=report['status'],output=str(output))),flush=True)
    if report['status']!='CEM_CPU_VERIFIED_CANDIDATE':raise SystemExit(2)


if __name__=='__main__':main()
