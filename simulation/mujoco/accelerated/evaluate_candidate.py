"""Evaluate frozen CEM command parameters on a separately captured entry."""
import argparse
import hashlib
import json
from pathlib import Path
import traceback

import mujoco
import numpy as np

from atom_mujoco.backend import Simulation
from atom_mujoco.native_motion import NativeMotion
from atom_mujoco.grasp_geometry import grasp_geometry
from atom_mujoco.autonomous_scene import collision_height
from batch import SIGNATURE
from cem import candidate,validated_reference
from cem_core import LOWER,UPPER
from replay import load_recording
from tapes import evaluate_gpu,evaluate_cpu
from outcomes import manipulation_outcomes


def worker(args):
    config=json.loads(args.config.read_text(encoding='utf-8-sig'));sim=Simulation(config['bundle'])
    if len(sim.manifest['pieces'])!=1:raise ValueError('Isolated Stage A evaluation only')
    winner=json.loads(args.winner.read_text())
    if winner.get('status')!='CEM_CPU_VERIFIED_CANDIDATE' or winner['identity']['model_sha256']!=sim.manifest['model_sha256']:
        raise ValueError('Matching canonical-verified winner required')
    values=np.asarray(winner['best']['parameters'],dtype=float)
    if values.shape!=(3,) or np.any(values<LOWER) or np.any(values>UPPER):raise ValueError('Bounded frozen parameters required')
    reference=validated_reference(config,sim,args.reference)
    before,_,phase,metadata=load_recording(args.reference/'physics-transitions.npz',sim.model,sim.manifest['model_sha256'],100000)
    initial=before[np.flatnonzero(phase=='CLOSE')[0]]
    motion=NativeMotion(config['motion_library'],sim)
    tape,labels,geometry=candidate(sim,motion,config,reference,initial,values,grasp_geometry,40.)
    selected=sim.model.body(config['piece']).id;address=sim.model.jnt_qposadr[sim.model.body_jntadr[selected]]
    mujoco.mj_setState(sim.model,sim.data,initial,SIGNATURE);initial_z=float(sim.data.qpos[address+2])
    gpu=evaluate_gpu(sim,config['piece'],tape[None,:,:],initial[None,:],args.max_gpu_mib)
    cpu=evaluate_cpu(sim,config['piece'],tape,initial)
    outcomes={name:manipulation_outcomes(sim.model,config['piece'],result['qpos'],result['qvel'],result['contacts'],result['forbidden'],
        labels,initial_z,collision_height(sim.model,config['piece']))[0] for name,result in (('gpu',gpu),('cpu',cpu))}
    np.savez_compressed(args.output/'candidate.npz',controls=tape,phase=labels,initial=initial,
        cpu_qpos=cpu['qpos'],cpu_qvel=cpu['qvel'],cpu_contacts=cpu['contacts'],gpu_qpos=gpu['qpos'],gpu_qvel=gpu['qvel'],
        gpu_contacts=gpu['contacts'],gpu_forbidden=gpu['forbidden'])
    report=dict(schema=1,experiment='EXP-0006',status='FROZEN_CANDIDATE_EVALUATION_PASSED' if all(r['success'] for r in outcomes.values()) else 'FROZEN_CANDIDATE_EVALUATION_FAILED',
        scope='frozen parameters, new camera-localized isolated entry; no optimization or learned policy',
        winner_sha256=hashlib.sha256(args.winner.read_bytes()).hexdigest(),parameters=values.tolist(),
        reference_sha256=hashlib.sha256((args.reference/'local-report.json').read_bytes()).hexdigest(),
        recording_sha256=metadata['sha256'],geometry=geometry,outcomes=outcomes,health=gpu['health'],
        cumulative_flags=gpu['cumulative_flags'],target_xy_source='signed new camera reference; not transferred simulator object coordinates')
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--winner',type=Path,required=True);parser.add_argument('--max-gpu-mib',type=int,default=2048)
    parser.add_argument('--max-wall-s',type=float,default=180.);parser.add_argument('--output',type=Path)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.worker:
        try:worker(args)
        except Exception as error:
            (args.output/'failure.json').write_text(json.dumps(dict(status='FAILED',error=str(error),traceback=traceback.format_exc()),indent=2))
            raise
        return
    from experiment import bounded_run
    arguments=['--config',str(args.config.resolve(strict=True)),'--reference',str(args.reference.resolve(strict=True)),
        '--winner',str(args.winner.resolve(strict=True)),'--max-gpu-mib',str(args.max_gpu_mib)]
    output,report=bounded_run(__file__,arguments,experiment='EXP-0006',output=args.output,
        sources=[Path(__file__).with_name(name) for name in ('cem.py','cem_core.py','batch.py','tapes.py','outcomes.py','cuda_rollout.py','replay.py','requirements-windows-py312.lock')],
        max_wall_s=args.max_wall_s,request=dict(config=str(args.config),reference=str(args.reference),winner=str(args.winner)))
    print(json.dumps(dict(status=report['status'],output=str(output))),flush=True)
    if report['status']!='FROZEN_CANDIDATE_EVALUATION_PASSED':raise SystemExit(2)


if __name__=='__main__':main()
