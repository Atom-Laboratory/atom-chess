"""Bounded standalone Watch of verified physical command chunks, not training."""
import argparse
import json
from pathlib import Path
import traceback

import numpy as np

from atom_mujoco.backend import Simulation
from demonstrations import digest, replay_watch


def worker(args):
    report = json.loads((args.demonstration / 'report.json').read_text())
    if report.get('status') != 'PHYSICAL_DEMONSTRATION_EXPORTED' or not report['outcome']['success']:
        raise ValueError('Verified demonstration required')
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    sim = Simulation(config['bundle'])
    if report['config_sha256'] != digest(args.config) or report['model_sha256'] != sim.manifest['model_sha256']:
        raise ValueError('Demonstration config/model mismatch')
    path = args.demonstration / 'privileged.npz'
    if digest(path) != report['artifacts_sha256'][path.name]:
        raise ValueError('Demonstration physics archive hash mismatch')
    with np.load(path, allow_pickle=False) as archive:
        tape, initial, phase = archive['controls'], archive['initial'], archive['phase']
    viewing = replay_watch(sim, tape, initial, phase, config['camera'], repeats=args.repeats, speed=args.speed)
    result = dict(schema=1, experiment='EXP-0007', status='WATCH_REPLAY_EXITED',
        scope='bounded CPU physics replay, not live optimization or RL',
        demonstration=str(args.demonstration), demonstration_report_sha256=digest(args.demonstration / 'report.json'),
        repeats_requested=args.repeats, speed=args.speed, user_may_close_early=True, **viewing)
    (args.output / 'report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


def launch(config, demonstration, *, repeats=2, speed=1., max_wall_s=300., output=None):
    if not 1 <= repeats <= 20 or not .25 <= speed <= 4:
        raise ValueError('Bounded replay settings required')
    from experiment import bounded_run
    script = Path(__file__)
    sources = [script.with_name(n) for n in ('demonstrations.py', 'cem.py', 'cem_core.py', 'batch.py', 'tapes.py', 'outcomes.py', 'replay.py')]
    return bounded_run(script, ['--config', str(Path(config).resolve(strict=True)),
        '--demonstration', str(Path(demonstration).resolve(strict=True)), '--repeats', str(repeats), '--speed', str(speed)],
        experiment='EXP-0007', output=output, sources=sources, max_wall_s=max_wall_s,
        request=dict(kind='separate-process-watch', repeats=repeats, speed=speed))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--demonstration', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=2)
    parser.add_argument('--speed', type=float, default=1.)
    parser.add_argument('--max-wall-s', type=float, default=300.)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 20 or not .25 <= args.speed <= 4:
        parser.error('repeats 1..20 and speed .25..4 required')
    if args.worker:
        try:
            worker(args)
        except Exception as error:
            (args.output / 'failure.json').write_text(json.dumps(dict(status='FAILED', error=str(error), traceback=traceback.format_exc()), indent=2))
            raise
    else:
        output, report = launch(args.config, args.demonstration, repeats=args.repeats, speed=args.speed,
                                max_wall_s=args.max_wall_s, output=args.output)
        print(json.dumps(dict(status=report['status'], output=str(output))), flush=True)


if __name__ == '__main__':
    main()
