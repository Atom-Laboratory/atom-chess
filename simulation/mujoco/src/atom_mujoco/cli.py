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


def serializable(state):
    return {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in state.items()}


def demonstration(sim, seconds):
    sim.reset()
    # Software test scenario, not a calibrated manipulation target.
    goal = np.clip(np.array([.3, .08, -.4]), sim.lower, sim.upper)
    trajectory = [serializable(sim.observe())]
    for _ in range(round(seconds/sim.dt)):
        trajectory.append(serializable(sim.advance(goal)))
    error = np.abs(sim.data.qpos-goal)
    return dict(schema=1, mode='conventional_position_control',
                mujoco_version=mujoco.__version__, python=platform.python_version(),
                manifest=sim.manifest, control_dt_s=sim.dt, target=goal.tolist(),
                final_error=error.tolist(), max_joint_limit_excess=np.max([
                    s['joint_limit_excess'] for s in trajectory], axis=0).tolist(),
                finite=all(np.isfinite(s['position']).all() for s in trajectory),
                contacts=None, trajectory=trajectory)


def viewer(sim):
    import mujoco.viewer
    # Q/A, W/S, E/D adjust target by a fraction of each prototype range.
    target = sim.target.copy()
    requests = []
    def on_key(key):
        requests.append(key)
    print('Q/A: joint 1; W/S: joint 2; E/D: joint 3; R: reset; Space: hold; Esc: close', flush=True)
    with mujoco.viewer.launch_passive(sim.model, sim.data, key_callback=on_key) as window:
        with window.lock():
            window.cam.lookat[:] = [.15, .08, 0]
            window.cam.distance = 1.3
            window.cam.azimuth = 120
            window.cam.elevation = -25
        while window.is_running():
            start = time.monotonic()
            while requests:
                key = requests.pop(0)
                if key == ord('R'):
                    sim.reset()
                    target = sim.target.copy()
                elif key == 32:
                    target = np.clip(sim.data.qpos.copy(), sim.lower, sim.upper)
                else:
                    for i, pair in enumerate(('QA', 'WS', 'ED')):
                        if key in map(ord, pair):
                            target[i] += (1 if key == ord(pair[0]) else -1)*.05*(sim.upper[i]-sim.lower[i])
                            target = np.clip(target, sim.lower, sim.upper)
            sim.advance(target)
            window.sync()
            time.sleep(max(0, sim.dt-(time.monotonic()-start)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('build')
    build.add_argument('--urdf', required=True, type=Path)
    build.add_argument('--output', required=True, type=Path)
    for command in ('demo', 'view', 'render'):
        child = sub.add_parser(command)
        child.add_argument('--bundle', type=Path, required=True)
        if command != 'view':
            child.add_argument('--output', type=Path, required=True)
        if command == 'demo':
            child.add_argument('--seconds', type=float, default=4.)
    args = parser.parse_args()
    if args.command == 'build':
        print(json.dumps(build_bundle(args.urdf, args.output), indent=2))
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
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
        print(json.dumps({key: value for key, value in result.items() if key not in ('trajectory', 'manifest')}, indent=2))
    else:
        # PPM uses only the standard library; no image or training dependencies.
        with mujoco.Renderer(sim.model, height=600, width=800) as renderer:
            camera = mujoco.MjvCamera()
            mujoco.mjv_defaultCamera(camera)
            camera.lookat[:] = [.15, .08, 0]
            camera.distance, camera.azimuth, camera.elevation = 1.3, 120, -25
            renderer.update_scene(sim.data, camera=camera)
            pixels = renderer.render()
            if np.ptp(pixels) == 0:
                raise RuntimeError('Renderer produced a uniform frame')
            args.output.write_bytes(b'P6\n800 600\n255\n'+pixels.tobytes())
        print(str(args.output))


if __name__ == '__main__':
    main()
