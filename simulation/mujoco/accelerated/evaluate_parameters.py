"""Evaluate independent bounded parameter actions; no actor observations from truth."""
import argparse
import hashlib
import json
from pathlib import Path
import traceback

import mujoco
import numpy as np

from atom_mujoco.autonomous_scene import collision_height
from atom_mujoco.backend import Simulation
from atom_mujoco.grasp_geometry import grasp_geometry
from atom_mujoco.native_motion import NativeMotion
from batch import SIGNATURE
from cem import candidate, validated_reference
from cem_core import LOWER, UPPER
from outcomes import manipulation_outcomes
from replay import load_recording
from tapes import evaluate_cpu, evaluate_gpu


def worker(args):
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    sim = Simulation(config['bundle'])
    if len(sim.manifest['pieces']) != 1:
        raise ValueError('Isolated Stage A parameter evaluation only')
    cases = json.loads(args.actions.read_text())['cases']
    if not 1 <= len(cases) <= 64:
        raise ValueError('Batch must contain 1..64 independent macro episodes')
    motion = NativeMotion(config['motion_library'], sim)
    cache, tapes, labels, initials, accepted, records, initial_z = {}, [], [], [], [], [], []
    body = sim.model.body(config['piece']).id
    address = sim.model.jnt_qposadr[sim.model.body_jntadr[body]]
    for index, case in enumerate(cases):
        path = Path(case['reference']).resolve(strict=True)
        if str(path) not in cache:
            reference = validated_reference(config, sim, path)
            before, _, phase, metadata = load_recording(path / 'physics-transitions.npz', sim.model, sim.manifest['model_sha256'], 100000)
            close = np.flatnonzero(phase == 'CLOSE')
            if not len(close):
                raise ValueError('Recorded close entry required')
            cache[str(path)] = reference, before[close[0]], metadata['sha256']
        reference, initial, recording_hash = cache[str(path)]
        values = np.asarray(case['parameters'], dtype=float)
        if values.shape != (3,) or not np.isfinite(values).all() or np.any(values < LOWER) or np.any(values > UPPER):
            raise ValueError('Finite bounded planner parameters required')
        record = dict(index=index, reference=str(path), recording_sha256=recording_hash, parameters=values.tolist(), geometry_valid=False)
        try:
            tape, phase, geometry = candidate(sim, motion, config, reference, initial, values, grasp_geometry, 40.)
            record.update(geometry_valid=True, geometry=geometry, duration_s=geometry['duration_s'])
            tapes.append(tape); labels.append(phase); initials.append(initial); accepted.append(index)
            mujoco.mj_setState(sim.model, sim.data, initial, SIGNATURE)
            initial_z.append(float(sim.data.qpos[address + 2]))
        except ValueError as error:
            record['failure'] = str(error)
        records.append(record)
    health = None
    if accepted:
        length = max(map(len, tapes))
        commands = np.empty((len(tapes), length, sim.model.nu))
        phases = np.full((length, len(tapes)), 'PADDING', dtype='<U16')
        for world, (tape, phase) in enumerate(zip(tapes, labels)):
            commands[world, :len(tape)] = tape
            commands[world, len(tape):] = tape[-1]
            phases[:len(tape), world] = phase
        result = evaluate_gpu(sim, config['piece'], commands, np.stack(initials), args.max_gpu_mib)
        outcomes = manipulation_outcomes(sim.model, config['piece'], result['qpos'], result['qvel'], result['contacts'],
            result['forbidden'], phases, initial_z, collision_height(sim.model, config['piece']))
        health = dict(gpu_rollout_wall_s=result['wall_s'], health=result['health'], cumulative_flags=result['cumulative_flags'])
        for world, index in enumerate(accepted):
            records[index]['outcome'] = outcomes[world]
            if args.verify_cpu:
                cpu = evaluate_cpu(sim, config['piece'], tapes[world], initials[world])
                records[index]['cpu_outcome'] = manipulation_outcomes(sim.model, config['piece'], cpu['qpos'], cpu['qvel'],
                    cpu['contacts'], cpu['forbidden'], labels[world], initial_z[world], collision_height(sim.model, config['piece']))[0]
                artifact = args.output / f'case-{index}'
                artifact.mkdir()
                np.savez_compressed(artifact / 'candidate.npz', controls=tapes[world], phase=labels[world], initial=initials[world],
                    cpu_qpos=cpu['qpos'], cpu_qvel=cpu['qvel'])
                path = Path(records[index]['reference'])
                candidate_report = dict(schema=1, experiment='EXP-0008',
                    status='FROZEN_CANDIDATE_EVALUATION_PASSED' if outcomes[world]['success'] and records[index]['cpu_outcome']['success']
                           else 'FROZEN_CANDIDATE_EVALUATION_FAILED',
                    scope='frozen neural parameter policy action; canonical CPU/GPU verification, not CEM optimization',
                    reference_sha256=hashlib.sha256((path / 'local-report.json').read_bytes()).hexdigest(),
                    recording_sha256=records[index]['recording_sha256'], parameters=records[index]['parameters'],
                    model_sha256=sim.manifest['model_sha256'], geometry=records[index]['geometry'],
                    outcomes=dict(gpu=outcomes[world], cpu=records[index]['cpu_outcome']))
                (artifact / 'report.json').write_text(json.dumps(candidate_report, indent=2) + '\n', encoding='utf-8')
        np.savez_compressed(args.output / 'episodes.npz', controls=commands, phase=phases, initial=np.stack(initials),
            qpos=result['qpos'], qvel=result['qvel'], contacts=result['contacts'], forbidden=result['forbidden'], accepted_indices=accepted)
    report = dict(schema=1, experiment='EXP-0008', status='PARAMETER_BATCH_EVALUATED',
        model_sha256=sim.manifest['model_sha256'], actions_sha256=hashlib.sha256(args.actions.read_bytes()).hexdigest(),
        records=records, telemetry=health, verify_cpu=args.verify_cpu,
        scope='one isolated complete close/lift/hold macro action per independent physics world; not low-level policy steps')
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--actions', type=Path, required=True)
    parser.add_argument('--verify-cpu', action='store_true')
    parser.add_argument('--max-gpu-mib', type=int, default=2048)
    parser.add_argument('--max-wall-s', type=float, default=180.)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        try:
            worker(args)
        except Exception as error:
            (args.output / 'failure.json').write_text(json.dumps(dict(status='FAILED', error=str(error), traceback=traceback.format_exc()), indent=2))
            raise
        return
    from experiment import bounded_run
    arguments = ['--config', str(args.config.resolve(strict=True)), '--actions', str(args.actions.resolve(strict=True)),
                 '--max-gpu-mib', str(args.max_gpu_mib)]
    if args.verify_cpu:
        arguments.append('--verify-cpu')
    sources = [Path(__file__).with_name(n) for n in ('cem.py', 'cem_core.py', 'batch.py', 'tapes.py', 'outcomes.py', 'cuda_rollout.py', 'replay.py')]
    output, report = bounded_run(__file__, arguments, experiment='EXP-0008', output=args.output, sources=sources,
                                 max_wall_s=args.max_wall_s, request=dict(verify_cpu=args.verify_cpu))
    print(json.dumps(dict(status=report['status'], output=str(output))), flush=True)


if __name__ == '__main__':
    main()
