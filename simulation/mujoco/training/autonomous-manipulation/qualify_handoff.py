"""Run fixed-seed native approach resets and archive M1 endpoint evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import mujoco
from PIL import Image

from atom_mujoco.autonomous_env import AutonomousManipulationEnv
from atom_mujoco.paths import new_run


def write_json(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seeds', type=int, nargs='+', default=[7, 8])
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--require-visible-target', action='store_true',
                        help='Screen candidate poses using the fixed camera before approach execution')
    args = parser.parse_args()
    if min(args.seeds) < 0 or len(set(args.seeds)) != len(args.seeds):
        parser.error('Use distinct nonnegative seeds')
    configuration = json.loads(args.config.read_text(encoding='utf-8'))
    configuration.setdefault('autonomous', {})['start_mode'] = 'native_approach'
    if args.require_visible_target:
        configuration['autonomous']['require_visible_target'] = True
    output = args.output or new_run('training/autonomous-manipulation/runs')
    output.mkdir(parents=True, exist_ok=False)
    config = output/'environment.json'
    write_json(config, configuration)
    sources = Path(__file__).resolve().parents[2]/'src/atom_mujoco'
    files = [args.config, config, Path(__file__), *sources.glob('*.py'),
             *(Path(configuration[key]) for key in ('motion_library', 'vision_library', 'layout'))]
    write_json(output/'provenance.json', dict(seeds=args.seeds, mujoco=mujoco.__version__,
        objective='lift', qualification='native approach and initial observation',
        files_sha256={str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}))

    env = AutonomousManipulationEnv(config, objective='lift')
    viewer = None
    trials = []
    try:
        if args.watch:
            from mujoco.viewer import launch_passive
            display = mujoco.MjData(env.sim.model)
            viewer = launch_passive(env.sim.model, display, show_left_ui=False, show_right_ui=False)
            with viewer.lock():
                viewer.cam.lookat[:] = env.base.camera.lookat
                viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = .8, 135, -35

            def observe(phase, info):
                if viewer.is_running():
                    with viewer.lock():
                        mujoco.mj_copyData(display, env.sim.model, env.sim.data)
                    viewer.set_texts((mujoco.mjtFontScale.mjFONTSCALE_100,
                        mujoco.mjtGridPos.mjGRID_TOPLEFT, 'M1 / NATIVE HANDOFF', f'{phase}\n{info or ""}'))
                    viewer.sync(state_only=True)

            env.approach_observer = observe
        for seed in args.seeds:
            print(f'[ATOM M1] Seed {seed} | native approach', flush=True)
            started = time.perf_counter()
            try:
                observation, _ = env.reset(seed=seed)
                if not env.observation_space.contains(observation):
                    raise AssertionError('Initial actor observation is outside its space')
            except (RuntimeError, ValueError) as error:
                if env.last_handoff['status'] != 'FAILED':
                    raise
                print(f'[ATOM M1] Seed {seed} | {error}', flush=True)
            trial = env.last_handoff
            trial['wall_s'] = time.perf_counter()-started
            write_json(output/f'seed-{seed}.json', trial)
            if 'arrival_perception' in trial:
                frame = env.base.last_camera_frame
                Image.fromarray(frame.raw_rgb).save(output/f'seed-{seed}-arrival-rgb.png')
                Image.fromarray(frame.rectified_rgb).save(output/f'seed-{seed}-arrival-board.png')
            trials.append(dict(seed=seed, status=trial['status'],
                failure_category=trial.get('failure_category'), stage=trial['stage'],
                endpoint=trial.get('endpoint'), validation=trial.get('validation'),
                wall_s=trial['wall_s']))
            print(f'[ATOM M1] Seed {seed} | {trial["status"]} | {trial["wall_s"]:.2f}s', flush=True)
        initialized = sum(trial['status'] == 'INITIALIZED' for trial in trials)
        write_json(output/'summary.json', dict(environment_version=env.VERSION, attempted=len(trials),
            initialized=initialized, training_eligible=False, trials=trials))
        print(f'[ATOM M1] {initialized}/{len(trials)} initialized | {output}', flush=True)
        return 0 if initialized == len(trials) else 1
    finally:
        if viewer is not None:
            viewer.close()
        env.close()


if __name__ == '__main__':
    raise SystemExit(main())
