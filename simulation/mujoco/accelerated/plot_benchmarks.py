"""Render raw repeated physics timings as standalone research figures."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    reports=[json.loads((path/'report.json').read_text(encoding='utf-8')) for path in args.runs]
    if len({r['model_sha256'] for r in reports})!=1:raise ValueError('Benchmark models differ')
    samples=[];rows=[]
    for path,report in zip(args.runs,reports):
        if report['status']!='PHYSICS_BENCHMARK_COMPLETED':raise ValueError('Completed benchmark required')
        with (path/'samples.csv').open(newline='',encoding='utf-8') as stream:
            samples.extend(dict(record,source_run=path.name) for record in csv.DictReader(stream))
        rows.extend(report['rows'])
    with (args.output/'combined-samples.csv').open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(samples[0]));writer.writeheader();writer.writerows(samples)
    plt.rcParams.update({'font.size':10,'figure.dpi':140,'svg.fonttype':'none'})
    fig,(ax,mem)=plt.subplots(1,2,figsize=(11,4.6))
    backends=('cpu-1-thread','cpu-6-thread','gpu-graph')
    for backend,color,label in zip(backends,('#777777','#0072B2','#D55E00'),('CPU, 1 thread','CPU, 6 threads','MJWarp, CUDA graph')):
        selected=sorted(rows,key=lambda row:row['worlds']);x=[r['worlds'] for r in selected]
        med=np.array([r[backend]['median_world_steps_per_s'] for r in selected])
        lower=np.array([r['worlds']*int(next(s['steps_per_world'] for s in samples if int(s['worlds'])==r['worlds']))/r[backend]['max_wall_s'] for r in selected])
        upper=np.array([r['worlds']*int(next(s['steps_per_world'] for s in samples if int(s['worlds'])==r['worlds']))/r[backend]['min_wall_s'] for r in selected])
        ax.errorbar(x,med/1000,yerr=np.stack((med-lower,upper-med))/1000,fmt='o-',capsize=3,color=color,label=label)
    ax.set(xscale='log',yscale='log',xlabel='Independent worlds in batch',ylabel='Aggregate physics steps/s (thousands)',
           title='EXP-0005 · fixed-control held pawn')
    ax.grid(True,which='both',alpha=.2);ax.legend(loc='upper left',fontsize=8)
    selected=sorted(rows,key=lambda row:row['worlds'])
    mem.plot([r['worlds'] for r in selected],[r['health']['warp_pool_bytes']/1024**2 for r in selected],'o-',color='#009E73')
    mem.set(xscale='log',xlabel='Worlds in batch',ylabel='Observed Warp pool allocation (MiB)',
            title='Allocation pool · excludes driver/other apps');mem.grid(True,alpha=.2)
    fig.text(.5,.01,'FIG-0003 · same model/state; medians and min–max repeats. N≤64: 128 steps ×3; N≥128: 256 steps ×5.\nPhysics only: no camera, planner, policy or rendering; workstation contention was not controlled.',
             ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.10,1,1))
    for suffix in ('svg','pdf','png'):fig.savefig(args.output/f'FIG-0003-physics-throughput.{suffix}')
    svg=args.output/'FIG-0003-physics-throughput.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
    metadata=dict(experiment='EXP-0005',figure='FIG-0003',sources=[dict(path=str(p),
        report_sha256=hashlib.sha256((p/'report.json').read_bytes()).hexdigest(),
        samples_sha256=hashlib.sha256((p/'samples.csv').read_bytes()).hexdigest()) for p in args.runs],
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (args.output/'figure-provenance.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(args.output,flush=True)


if __name__=='__main__':main()
