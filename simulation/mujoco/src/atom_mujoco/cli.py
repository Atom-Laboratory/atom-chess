"""Build, inspect and demonstrate the backend without implementing an RL agent."""
import argparse
import json
from pathlib import Path
import platform
import time

import mujoco
import numpy as np

from .backend import Simulation
from .model import build_bundle
from .recording import provenance, save_record


def serializable(state):
    if isinstance(state, np.ndarray):
        return state.tolist()
    if isinstance(state, dict):
        return {k: serializable(v) for k, v in state.items()}
    if isinstance(state, (list, tuple)):
        return [serializable(v) for v in state]
    return state


def demonstration(sim, seconds):
    started = time.perf_counter()
    sim.reset()
    # Software test scenario, not a calibrated manipulation target.
    goal = sim.target.copy()
    goal[:3] = [.3, .08, -.4]
    goal = np.clip(goal, sim.lower, sim.upper)
    trajectory = [serializable(sim.observe())]
    for _ in range(round(seconds/sim.dt)):
        trajectory.append(serializable(sim.advance(goal)))
    error = np.abs(sim.observe()['position']-goal)
    return dict(schema=1, mode='conventional_position_control',
                provenance=provenance(), seed=None, reset=('raised-interactive-home' if sim.manifest['profile']['contacts'] else 'zero-clipped-to-limits'),
                task=None, algorithm=None, episodes=1, checkpoints=[],
                wall_time_s=time.perf_counter()-started,
                mujoco_version=mujoco.__version__, python=platform.python_version(),
                manifest=sim.manifest, control_dt_s=sim.dt, target=goal.tolist(),
                final_error=error.tolist(), max_joint_limit_excess=np.max([
                    s['joint_limit_excess'] for s in trajectory], axis=0).tolist(),
                finite=all(np.isfinite(s['position']).all() for s in trajectory),
                contacts=sim.observe()['contacts'], trajectory=trajectory)


def viewer(sim):
    from .controls import run_viewer
    return run_viewer(sim)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('build')
    build.add_argument('--urdf', required=True, type=Path)
    build.add_argument('--output', required=True, type=Path)
    build.add_argument('--parameters', type=Path, help='JSON overrides; experimental, not calibration')
    build.add_argument('--interactive', action='store_true', help='Experimental gravity/contact/gripper profile')
    for command in ('demo', 'view', 'render'):
        child = sub.add_parser(command)
        child.add_argument('--bundle', type=Path, required=True)
        if command != 'view':
            child.add_argument('--output', type=Path, required=True)
        if command == 'demo':
            child.add_argument('--seconds', type=float, default=4.)
    args = parser.parse_args()
    if args.command == 'build':
        parameters = json.loads(args.parameters.read_text(encoding='utf-8-sig')) if args.parameters else None
        print(json.dumps(build_bundle(args.urdf, args.output, parameters=parameters, interactive=args.interactive), indent=2))
        return
    sim = Simulation(args.bundle)
    if args.command == 'view':
        viewer(sim)
        return
    if args.output.exists():
        parser.error('Output already exists; choose a new output path')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.command == 'demo':
        if not np.isfinite(args.seconds) or args.seconds <= 0:
            parser.error('seconds must be finite and positive')
        result = demonstration(sim, args.seconds)
        save_record(args.output, result)
        print(json.dumps({key: value for key, value in result.items() if key not in ('trajectory', 'manifest')}, indent=2))
    else:
        # PPM uses only the standard library; no image or training dependencies.
        with mujoco.Renderer(sim.model, height=600, width=800) as renderer:
            camera = mujoco.MjvCamera()
            mujoco.mjv_defaultCamera(camera)
            settings = sim.manifest.get('scene', {}).get('camera', {})
            camera.lookat[:] = settings.get('lookat', [.15, .08, 0])
            camera.distance = settings.get('distance', 1.3)
            camera.azimuth = settings.get('azimuth', 120)
            camera.elevation = settings.get('elevation', -25)
            renderer.update_scene(sim.data, camera=camera)
            pixels = renderer.render()
            if np.ptp(pixels) == 0:
                raise RuntimeError('Renderer produced a uniform frame')
            args.output.write_bytes(b'P6\n800 600\n255\n'+pixels.tobytes())
        print(str(args.output))


if __name__ == '__main__':
    main()
