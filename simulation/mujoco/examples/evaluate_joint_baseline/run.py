"""Measure conventional joint-target tracking. This is not a chess-move benchmark."""
import argparse
from pathlib import Path
import time

import numpy as np

from atom_mujoco.backend import Simulation
from atom_mujoco.recording import provenance, save_record


def evaluate(bundle, seed, trials):
    if trials <= 0:
        raise ValueError('trials must be positive')
    sim = Simulation(bundle)
    rng = np.random.default_rng(seed)
    records = []
    start = time.perf_counter()
    for index in range(trials):
        sim.reset()
        goal = sim.target.copy()
        goal[:3] = rng.uniform([-.3, .08, -.4], [.3, .15, .4])
        peak_excess = 0.
        robot_contact_steps = 0
        for _ in range(200):
            state = sim.advance(goal)
            peak_excess = max(peak_excess, float(max(state['joint_limit_excess'])))
            robot_contact_steps += int(any('collision' in str(c) or 'finger_' in str(c)
                                           for c in state['contacts'] or []))
        records.append(dict(trial=index, target=goal.tolist(),
                            absolute_joint_error=abs(state['position']-goal).tolist(),
                            peak_limit_excess=peak_excess,
                            robot_contact_steps=robot_contact_steps,
                            simulated_time_s=state['time_s']))
    return dict(schema=1, experiment='joint-tracking-baseline-v1', seed=seed,
                provenance=provenance(), manifest=sim.manifest, trials=records,
                wall_time_s=time.perf_counter()-start,
                limitations=['not manipulation', 'not measured hardware',
                             'mixed joint units: radians and metres', 'no learned-policy comparison'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--trials', type=int, default=5)
    args = parser.parse_args()
    result = evaluate(args.bundle, args.seed, args.trials)
    save_record(args.output, result)
    print(f"Saved {len(result['trials'])} trials to {args.output}")
