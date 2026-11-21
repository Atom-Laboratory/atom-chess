"""Frozen parameter-policy inference from signed vision and issued-command history."""
import argparse
import json
from pathlib import Path
import subprocess
import traceback

import mujoco
import numpy as np
import torch

from atom_mujoco.backend import Simulation
from batch import SIGNATURE
from cem import validated_reference
from demonstrations import digest
from parameter_policy import ParameterPolicy, context, to_parameters
from replay import load_recording


def reference_context(config, sim, directory):
    reference = validated_reference(config, sim, directory)
    before, _, phase, _ = load_recording(directory / 'physics-transitions.npz', sim.model, sim.manifest['model_sha256'], 100000)
    close = np.flatnonzero(phase == 'CLOSE')
    if not len(close):
        raise ValueError('Executed near-grasp command history required')
    # This adapter extracts ONLY the issued actuator command. No actual joint,
    # TCP, object position, velocity or contact is queried for inference.
    history = mujoco.MjData(sim.model)
    mujoco.mj_setState(sim.model, history, before[close[0]], SIGNATURE)
    source_xy = next(s['target'][:2] for s in reference['stages'] if s['name'] == 'DESCEND')
    def square(name):
        return ['abcdefgh'.index(name[0]) / 7., (int(name[1]) - 1) / 7.]
    fields = dict(source_xy_m=source_xy, issued_command=history.ctrl.tolist(),
                  squares=square(config['source']) + square(config['target']))
    return context(fields, sim.lower, sim.upper), fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--references', type=Path, nargs='+', required=True)
    parser.add_argument('--gpu-python', type=Path, required=True)
    parser.add_argument('--max-gpu-mib', type=int, default=2048)
    parser.add_argument('--max-wall-s', type=float, default=180.)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 1 <= len(args.references) <= 16:
        parser.error('At most sixteen independent evaluation references per batch')
    if not args.worker:
        from experiment import bounded_run
        arguments = ['--config', str(args.config.resolve(strict=True)), '--checkpoint', str(args.checkpoint.resolve(strict=True)),
            '--references', *[str(r.resolve(strict=True)) for r in args.references],
            '--gpu-python', str(args.gpu_python.resolve(strict=True)), '--max-gpu-mib', str(args.max_gpu_mib),
            '--max-wall-s', str(max(10., args.max_wall_s - 30.))]
        sources = [Path(__file__).with_name(n) for n in ('parameter_policy.py', 'evaluate_parameters.py', 'demonstrations.py',
            'cem.py', 'cem_core.py', 'batch.py', 'tapes.py', 'outcomes.py', 'cuda_rollout.py', 'replay.py')]
        output, report = bounded_run(__file__, arguments, experiment='EXP-0008', output=args.output, sources=sources,
            max_wall_s=args.max_wall_s, request=dict(kind='frozen-policy-independent-evaluation', references=len(args.references)))
        print(json.dumps(dict(status=report['status'], output=str(output),
            cpu_successes=sum(r.get('cpu_outcome', {}).get('success', False) for r in report['records']))), flush=True)
        return
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    sim = Simulation(config['bundle'])
    saved = torch.load(args.checkpoint, map_location='cpu', weights_only=True)
    identity = saved['identity']
    if (identity['schema'] != 'stage-a-camera-command-macro-v1' or identity['model_sha256'] != sim.manifest['model_sha256']
            or identity['config_sha256'] != digest(args.config)
            or identity['sources']['parameter_policy.py'] != digest(Path(__file__).with_name('parameter_policy.py'))):
        raise ValueError('Frozen policy model/config/schema/source mismatch')
    policy = ParameterPolicy(); policy.load_state_dict(saved['policy']); policy.eval()
    observations, fields = [], []
    for reference in args.references:
        observation, raw = reference_context(config, sim, reference)
        observations.append(observation); fields.append(raw)
    with torch.no_grad():
        parameters = to_parameters(policy.actor(torch.tensor(np.stack(observations)))).numpy()
    request = args.output / 'actions.json'
    request.write_text(json.dumps(dict(cases=[dict(reference=str(r.resolve(strict=True)), parameters=p.tolist())
        for r, p in zip(args.references, parameters)]), indent=2), encoding='utf-8')
    (args.output / 'inference.json').write_text(json.dumps(dict(checkpoint_sha256=digest(args.checkpoint),
        context_source='signed native-camera source XY + issued actuator command history + logical task',
        excluded_actor_fields=['actual qpos', 'qvel', 'object pose', 'contacts', 'reward', 'outcome'],
        context=fields, reference_sha256=[digest(r / 'local-report.json') for r in args.references],
        parameters=parameters.tolist(), source_sha256=digest(__file__)), indent=2), encoding='utf-8')
    command = [str(args.gpu_python.resolve(strict=True)), '-u', '-B', str(Path(__file__).with_name('evaluate_parameters.py')),
        '--config', str(args.config.resolve(strict=True)), '--actions', str(request.resolve()), '--verify-cpu',
        '--max-gpu-mib', str(args.max_gpu_mib), '--max-wall-s', str(args.max_wall_s), '--output', str((args.output / 'physics').resolve())]
    with (args.output / 'evaluation.log').open('w', encoding='utf-8') as stream:
        subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=args.max_wall_s + 15, check=True)
    report = json.loads((args.output / 'physics/report.json').read_text())
    report.update(scope='frozen neural policy on declared camera references; no optimization or training',
                  policy_checkpoint_sha256=digest(args.checkpoint), actor_context_source='inference.json')
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], output=str(args.output),
        cpu_successes=sum(r.get('cpu_outcome', {}).get('success', False) for r in report['records']), references=len(args.references))), flush=True)


if __name__ == '__main__':
    main()
