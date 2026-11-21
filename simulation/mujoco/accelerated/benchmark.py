"""Matched CPU-threaded/GPU physics-only robot contact benchmark."""
import argparse
import csv
import gc
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time
import traceback

import mujoco
from mujoco import batch as cpu_batch
import numpy as np
import psutil

from atom_mujoco.backend import Simulation
from batch import Limits,WarpBatch,pack


def validate(args):
    if (not args.worlds or any(type(n) is not int or not 1<=n<=args.max_worlds for n in args.worlds)
            or not 1<=args.max_worlds<=1024 or args.worlds!=sorted(set(args.worlds))
            or not 16<=args.steps<=4096 or args.steps%8 or not 3<=args.repeats<=20
            or not 1<=args.threads<=12):raise ValueError('Ordered bounded worlds, steps 16..4096 divisible by 8, repeats 3..20, threads 1..12 required')
    Limits(worlds=max(args.worlds),max_worlds=args.max_worlds,max_gpu_mib=args.max_gpu_mib)


def worker(args):
    import warp as wp
    config=json.loads(args.config.read_text(encoding='utf-8-sig'));sim=Simulation(config['bundle'])
    snapshot=json.loads(args.snapshot.read_text());state=mujoco.MjData(sim.model)
    state.qpos[:]=snapshot['qpos'];state.qvel[:]=snapshot['qvel'];state.ctrl[:]=snapshot['ctrl']
    state.time=snapshot['time_s'];mujoco.mj_forward(sim.model,state)
    initial=pack(sim.model,[state]);samples=[];rows=[]
    context=dict(cpu=psutil.cpu_count(),ram_available_bytes=psutil.virtual_memory().available,
        gpu=subprocess.run(['nvidia-smi','--query-gpu=name,driver_version,memory.total,memory.free,utilization.gpu',
            '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10,check=True).stdout.strip())
    wp.init()
    for worlds in args.worlds:
        repeated=np.repeat(initial,worlds,axis=0)
        np.savez_compressed(args.output/f'initial-{worlds}.npz',integration=repeated)
        for threads in sorted(set((1,args.threads))):
            values=cpu_batch.Batch(sim.model,worlds,nthread=threads)
            np.testing.assert_array_equal(values.state.shape,repeated.shape)
            values.state[:]=repeated;values.step(nstep=8)
            for repeat in range(args.repeats):
                start=time.perf_counter();values.state[:]=repeated;reset=time.perf_counter()-start
                start=time.perf_counter();values.step(nstep=args.steps);elapsed=time.perf_counter()-start
                if np.any(values.warning) or not np.isfinite(values.state).all():raise RuntimeError('CPU numerical warning/nonfinite benchmark state')
                samples.append(dict(worlds=worlds,backend=f'cpu-{threads}-thread',repeat=repeat,
                    steps_per_world=args.steps,wall_s=elapsed,reset_wall_s=reset,world_steps_per_s=worlds*args.steps/elapsed))
            np.savez_compressed(args.output/f'cpu-{threads}-final-{worlds}.npz',integration=values.state)
            del values;gc.collect()
        gpu=WarpBatch(sim.model,Limits(worlds=worlds,max_worlds=args.max_worlds,max_gpu_mib=args.max_gpu_mib,
            nconmax=max(64,2*state.ncon),njmax=max(256,2*state.nefc)))
        gpu.reset(repeated);gpu.forward();gpu.health()
        compile_started=time.perf_counter();gpu.step();wp.synchronize_device(gpu.device)
        with wp.ScopedDevice(gpu.device),wp.ScopedCapture(device=gpu.device) as capture:
            for _ in range(8):gpu.mjw.step(gpu.gpu_model,gpu.data)
        wp.synchronize_device(gpu.device);compile_wall=time.perf_counter()-compile_started
        for repeat in range(args.repeats):
            start=time.perf_counter();gpu.reset(repeated);wp.synchronize_device(gpu.device);reset=time.perf_counter()-start
            start=time.perf_counter()
            for _ in range(args.steps//8):wp.capture_launch(capture.graph)
            wp.synchronize_device(gpu.device);elapsed=time.perf_counter()-start
            health=gpu.health()
            samples.append(dict(worlds=worlds,backend='gpu-graph',repeat=repeat,steps_per_world=args.steps,
                wall_s=elapsed,reset_wall_s=reset,world_steps_per_s=worlds*args.steps/elapsed))
        np.savez_compressed(args.output/f'gpu-final-{worlds}.npz',integration=gpu.state())
        row=dict(worlds=worlds,graph_compile_wall_s=compile_wall,health=health)
        for backend in sorted({s['backend'] for s in samples if s['worlds']==worlds}):
            selected=[s for s in samples if s['worlds']==worlds and s['backend']==backend]
            row[backend]=dict(median_wall_s=statistics.median(s['wall_s'] for s in selected),
                median_world_steps_per_s=statistics.median(s['world_steps_per_s'] for s in selected),
                min_wall_s=min(s['wall_s'] for s in selected),max_wall_s=max(s['wall_s'] for s in selected),
                median_reset_wall_s=statistics.median(s['reset_wall_s'] for s in selected))
        rows.append(row)
        (args.output/'partial.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(json.dumps(row),flush=True)
        del capture,gpu;gc.collect();wp.synchronize()
    with (args.output/'samples.csv').open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(samples[0]));writer.writeheader();writer.writerows(samples)
    report=dict(schema=1,experiment='EXP-0005',status='PHYSICS_BENCHMARK_COMPLETED',context=context,
        scope='fixed-control held-pawn physics only; no camera/planner/policy/episode throughput',
        model_sha256=hashlib.sha256((Path(config['bundle'])/'model.xml').read_bytes()).hexdigest(),
        snapshot_sha256=hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
        steps=args.steps,repeats=args.repeats,rows=rows,
        limitations=['All worlds begin in the same restored state with explicit defaults for omitted hidden fields.',
            'No complete manipulation rollout or lifted-hold qualification is inferred from timing.',
            'Driver/compiler and other applications are outside Warp pool accounting.'])
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--worlds',type=int,nargs='+',default=[1,16,32])
    parser.add_argument('--max-worlds',type=int,default=64);parser.add_argument('--steps',type=int,default=128)
    parser.add_argument('--repeats',type=int,default=3);parser.add_argument('--threads',type=int,default=6)
    parser.add_argument('--max-gpu-mib',type=int,default=2048);parser.add_argument('--max-wall-s',type=float,default=900.)
    parser.add_argument('--output',type=Path);parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    try:validate(args)
    except ValueError as error:parser.error(str(error))
    if args.worker:
        try:worker(args)
        except Exception as error:
            (args.output/'failure.json').write_text(json.dumps(dict(status='FAILED',error=str(error),traceback=traceback.format_exc()),indent=2))
            raise
        return
    from experiment import bounded_run
    arguments=['--config',str(args.config.resolve(strict=True)),'--snapshot',str(args.snapshot.resolve(strict=True)),
        '--worlds',*map(str,args.worlds),'--max-worlds',str(args.max_worlds),'--steps',str(args.steps),
        '--repeats',str(args.repeats),'--threads',str(args.threads),'--max-gpu-mib',str(args.max_gpu_mib)]
    output,report=bounded_run(__file__,arguments,experiment='EXP-0005',output=args.output,
        sources=[Path(__file__).with_name(name) for name in ('batch.py','requirements-windows-py312.lock')],
        max_wall_s=args.max_wall_s,request=dict(worlds=args.worlds,steps=args.steps,repeats=args.repeats,
            threads=args.threads,max_worlds=args.max_worlds,max_gpu_mib=args.max_gpu_mib))
    print(json.dumps(dict(status=report['status'],output=str(output))),flush=True)


if __name__=='__main__':main()
