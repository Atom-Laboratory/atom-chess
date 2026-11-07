"""First study exercise: command one joint at a time and inspect the response.

Run from the repository root with the MuJoCo virtual environment. This example
uses only the public backend API, without accessing mjData or training code.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

from atom_mujoco.backend import Simulation
from atom_mujoco.recording import provenance, save_record


def inspect(sim):
    started = time.perf_counter()
    trials = []
    for index, displacement in enumerate((.3, .08, -.4)):
        initial = sim.reset()
        goal = initial['position'].copy()
        goal[index] += displacement
        trace = []
        for _ in range(round(4/sim.dt)):
            state = sim.advance(goal)
            trace.append(state['position'])
        final = state
        # Replay exactly the same commands from the same reset, without randomness.
        sim.reset()
        replay_error = 0.
        for expected in trace:
            repeated = sim.advance(goal)
            replay_error = max(replay_error, float(np.max(abs(repeated['position']-expected))))
        relative_rotation = final['arm2_rotation'] @ initial['arm2_rotation'].T
        angle = np.arccos(np.clip((np.trace(relative_rotation)-1)/2, -1, 1))
        trials.append(dict(joint=sim.names[index], unit='m' if index == 1 else 'rad',
                           target=goal.tolist(), final_position=final['position'].tolist(),
                           joint_error=(goal-final['position']).tolist(),
                           frame_translation_delta_m=(final['arm2_position']-initial['arm2_position']).tolist(),
                           frame_rotation_delta_rad=float(angle), replay_max_error=replay_error,
                           simulated_duration_s=final['time_s']))
    return dict(schema=1, exercise='inspect-joints-v1', manifest=sim.manifest, trials=trials,
                provenance=provenance(), seed=None, reset='zero-clipped-to-limits',
                task=None, algorithm=None, episodes=3, checkpoints=[],
                wall_time_s=time.perf_counter()-started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output path; existing results are preserved')
    result = inspect(Simulation(args.bundle))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_record(args.output, result)
    for trial in result['trials']:
        print(json.dumps(trial, indent=2))


if __name__ == '__main__':
    main()
