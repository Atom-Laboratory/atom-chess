"""Deterministic local reach feasibility check; no learning and no global travel."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from atom_mujoco.autonomous_env import AutonomousManipulationEnv
from atom_mujoco.paths import new_run


def reference_action(env):
    if not env.xyz_only:
        raise ValueError('Reference requires the reach_xyz profile')
    # XY is the camera estimate; Z uses static calibrated board and known model
    # height. Never use a live object pose to generate the command.
    target = np.array([*env.source_xy, env.base.surface_z+env.base.piece_height])
    start = env.control.commanded_tcp(env.command)
    delta = env.control.rates[:3]*env.xyz_scale*env.sim.dt
    return np.clip((target-start)/delta, -1., 1.).astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--episodes', type=int, default=8)
    parser.add_argument('--seed', type=int, default=910000)
    args = parser.parse_args()
    if args.episodes <= 0:
        parser.error('Positive episode count required')
    output = args.output or new_run('training/autonomous-manipulation/runs')
    output.mkdir(parents=True, exist_ok=False)
    env = AutonomousManipulationEnv(args.config, objective='reach', horizon=64)
    records = []
    try:
        for seed in range(args.seed, args.seed+args.episodes):
            env.reset(seed=seed)
            for _ in range(env.horizon):
                _, _, done, truncated, info = env.step(reference_action(env))
                if done or truncated:
                    break
            records.append(dict(seed=seed, **info))
            print(f'[REFERENCE / NO RL] seed {seed} success {info["success"]} '
                  f'gap {1000*info["pad_distance_m"]:.2f} mm', flush=True)
        report = dict(schema=1, type='deterministic_local_reference_not_learning',
            success_rate=sum(r['success'] for r in records)/len(records), records=records,
            model_sha256=env.sim.manifest['model_sha256'],
            config_sha256=hashlib.sha256(args.config.read_bytes()).hexdigest(),
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            scope='isolated local reach only; no executed global planner approach, grasp or lift')
        (output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(output/'report.json', flush=True)
    finally:
        env.close()


if __name__ == '__main__':
    main()
