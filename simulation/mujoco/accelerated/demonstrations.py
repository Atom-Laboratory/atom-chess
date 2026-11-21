"""Export camera/command demonstrations after fresh canonical physical replay."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time
import traceback

import mujoco
import numpy as np

from atom_mujoco.autonomous_scene import collision_height
from atom_mujoco.backend import Simulation
from atom_mujoco.virtual_camera import make_camera
from batch import SIGNATURE
from cem import validated_reference
from outcomes import manipulation_outcomes
from replay import load_recording
from tapes import forbidden_pairs


ACTOR_KEYS = frozenset(('rgb', 'issued_command', 'source_xy_m', 'squares', 'phase'))
PHASES = ('CLOSE', 'HOLD_CLOSE', 'LIFT', 'LIFT_HOLD')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def intervals(steps, stride):
    if type(stride) is not int or stride < 1 or not 1 <= steps <= 20000:
        raise ValueError('Bounded positive physics steps and interval required')
    return [(start, min(start + stride, steps)) for start in range(0, steps, stride)]


def actor_observation(rgb, issued, source_xy, source, target, phase):
    """Only RGB, issued commands, signed vision geometry and task/plan context."""
    def square(name):
        if len(name) != 2 or name[0] not in 'abcdefgh' or name[1] not in '12345678':
            raise ValueError('Board squares required')
        return ['abcdefgh'.index(name[0]) / 7., (int(name[1]) - 1) / 7.]
    return dict(rgb=np.asarray(rgb, dtype=np.uint8), issued_command=np.asarray(issued).copy(),
                source_xy_m=np.asarray(source_xy).copy(), squares=np.array(square(source) + square(target)),
                phase=np.eye(len(PHASES))[PHASES.index(phase)])


def validate_actor(actor, frames, actuators):
    if set(actor) != ACTOR_KEYS:
        raise ValueError('Actor allowlist rejects privileged or unknown fields')
    if actor['rgb'].dtype != np.uint8 or actor['rgb'].ndim != 4 or actor['rgb'].shape[0] != frames or actor['rgb'].shape[-1] != 3:
        raise ValueError('Pre-action uint8 RGB frames required')
    for key, width in [('issued_command', actuators), ('source_xy_m', 2), ('squares', 4), ('phase', 4)]:
        if actor[key].shape != (frames, width) or not np.isfinite(actor[key]).all():
            raise ValueError('Invalid actor field: ' + key)


def load_candidate(directory, config, sim, reference):
    report = json.loads((directory / 'report.json').read_text())
    if report['status'] == 'FROZEN_CANDIDATE_EVALUATION_PASSED':
        path = directory / 'candidate.npz'
        if report['reference_sha256'] != digest(reference / 'local-report.json'):
            raise ValueError('Candidate reference mismatch')
        if report['recording_sha256'] != digest(reference / 'physics-transitions.npz'):
            raise ValueError('Candidate recording mismatch')
        position_key, velocity_key = 'cpu_qpos', 'cpu_qvel'
    elif report['status'] == 'CEM_CPU_VERIFIED_CANDIDATE':
        path = directory / 'best-candidate.npz'
        identity = report['identity']
        if identity['model_sha256'] != sim.manifest['model_sha256'] or identity['recording_sha256'] != digest(reference / 'physics-transitions.npz'):
            raise ValueError('Candidate model/recording mismatch')
        if identity['config_sha256'] != digest(config):
            raise ValueError('Candidate config mismatch')
        position_key, velocity_key = 'qpos', 'qvel'
    else:
        raise ValueError('Canonical-verified candidate report required')
    with np.load(path, allow_pickle=False) as data:
        tape, initial, phase = data['controls'], data['initial'], data['phase']
        expected_qpos, expected_qvel = data[position_key], data[velocity_key]
    steps = len(tape)
    if (not 1 <= steps <= 20000 or tape.shape != (steps, sim.model.nu)
            or initial.shape != (mujoco.mj_stateSize(sim.model, SIGNATURE),)
            or phase.shape != (steps,) or not set(phase) <= set(PHASES)
            or expected_qpos.shape != (steps, 1, sim.model.nq) or expected_qvel.shape != (steps, 1, sim.model.nv)
            or not all(np.isfinite(a).all() for a in (tape, initial, expected_qpos, expected_qvel))
            or np.any(tape < sim.lower) or np.any(tape > sim.upper)
            or np.any(abs(np.diff(tape, axis=0)) > sim.speed * sim.model.opt.timestep + 1e-10)):
        raise ValueError('Finite matching bounded candidate trajectory required')
    return tape, initial, phase, expected_qpos, expected_qvel, path


def replay_watch(sim, tape, initial, phases, camera, *, repeats, speed):
    """Re-simulate controls; only the display copy is forwarded for rendering."""
    from mujoco import viewer
    model = sim.model
    display, data = mujoco.MjData(model), mujoco.MjData(model)
    mujoco.mj_setState(model, display, initial, SIGNATURE)
    mujoco.mj_forward(model, display)
    with viewer.launch_passive(model, display, show_left_ui=False, show_right_ui=False) as handle:
        with handle.lock():
            handle.cam.lookat[:] = camera['lookat']
            handle.cam.distance, handle.cam.azimuth, handle.cam.elevation = .8, 135., -35.
        stride = max(1, round(1 / (30 * model.opt.timestep)))
        completed = 0
        for repeat in range(repeats):
            mujoco.mj_setState(model, data, initial, SIGNATURE)
            started = time.perf_counter()
            for index, command in enumerate(tape):
                if not handle.is_running():
                    return dict(completed_repeats=completed, interrupted=True)
                data.ctrl[:] = command
                mujoco.mj_step(model, data)
                if np.any(data.warning.number) or not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all():
                    raise RuntimeError('Watch physics numerical failure')
                if index % stride == 0 or index == len(tape) - 1:
                    with handle.lock():
                        mujoco.mj_copyData(display, model, data)
                        mujoco.mj_forward(model, display)
                    handle.set_texts((mujoco.mjtFontScale.mjFONTSCALE_100, mujoco.mjtGridPos.mjGRID_TOPLEFT,
                        'ATOM / VERIFIED PHYSICS REPLAY - NOT RL TRAINING',
                        f'{phases[index]} | {index + 1}/{len(tape)} physics steps | replay {repeat + 1}/{repeats}'))
                    handle.sync(state_only=True)
                    time.sleep(max(0., (index + 1) * model.opt.timestep / speed - (time.perf_counter() - started)))
            completed += 1
        return dict(completed_repeats=completed, interrupted=False)


def worker(args):
    from PIL import Image
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    sim = Simulation(config['bundle'])
    if len(sim.manifest['pieces']) != 1:
        raise ValueError('Only isolated Stage A demonstrations are qualified')
    reference = validated_reference(config, sim, args.reference)
    tape, initial, phases, expected_pos, expected_vel, candidate_path = load_candidate(args.candidate, args.config, sim, args.reference)
    provenance = json.loads((args.reference / 'provenance.json').read_text())
    if provenance['config_sha256'] != digest(args.config):
        raise ValueError('Reference config/camera mismatch')
    before, _, recorded_phases, _ = load_recording(args.reference / 'physics-transitions.npz', sim.model,
                                                   sim.manifest['model_sha256'], 100000)
    close = np.flatnonzero(recorded_phases == 'CLOSE')
    if not len(close) or not np.array_equal(initial, before[close[0]]):
        raise ValueError('Candidate initial state differs from verified reference entry')
    model, data = sim.model, mujoco.MjData(sim.model)
    mujoco.mj_setState(model, data, initial, SIGNATURE)
    source_xy = next(s['target'][:2] for s in reference['stages'] if s['name'] == 'DESCEND')
    groups = intervals(len(tape), args.stride)
    if len(groups) > args.max_frames:
        raise ValueError('Frame budget exceeded; increase stride or explicit frame budget')
    lookup = {start: frame for frame, (start, _) in enumerate(groups)}
    bad_pairs, pads, selected = forbidden_pairs(sim, config['piece'])
    address = model.jnt_qposadr[model.body_jntadr[selected]]
    initial_z = float(data.qpos[address + 2])
    camera = config['camera']
    display = mujoco.MjData(model)
    actor_rows, pos, vel, contacts, bad, pre_states = [], [], [], [], [], []
    full_samples = {0, len(groups) // 2, len(groups) - 1}
    with mujoco.Renderer(model, height=camera['height'], width=camera['width']) as renderer:
        for index, command in enumerate(tape):
            if index in lookup:
                frame = lookup[index]
                # Render a copy: forward must not modify the live solver integration state.
                mujoco.mj_copyData(display, model, data)
                mujoco.mj_forward(model, display)
                renderer.update_scene(display, camera=make_camera(camera))
                image = Image.fromarray(renderer.render())
                if frame in full_samples:
                    image.save(args.output / f'camera-{frame:04d}.png')
                rgb = np.asarray(image.resize((args.image_size, args.image_size), Image.Resampling.BILINEAR))
                actor_rows.append(actor_observation(rgb, data.ctrl, source_xy, config['source'], config['target'], phases[index]))
                state = np.empty(mujoco.mj_stateSize(model, SIGNATURE))
                mujoco.mj_getState(model, data, state, SIGNATURE)
                pre_states.append(state)
            data.ctrl[:] = command
            mujoco.mj_step(model, data)
            if np.any(data.warning.number) or not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all():
                raise RuntimeError('Canonical numerical failure')
            pos.append(data.qpos.copy()); vel.append(data.qvel.copy())
            flags, violation = [0, 0], False
            for contact in data.contact:
                if contact.dist > 0:
                    continue
                a, b = map(int, contact.geom)
                for i, pad in enumerate(pads):
                    if (a == pad and model.geom_bodyid[b] == selected) or (b == pad and model.geom_bodyid[a] == selected):
                        flags[i] = 1
                violation |= bool(bad_pairs[a * model.ngeom + b])
            contacts.append(flags); bad.append(violation)
    pos, vel = np.asarray(pos)[:, None, :], np.asarray(vel)[:, None, :]
    contacts, bad = np.asarray(contacts)[:, None, :], np.asarray(bad)[:, None]
    errors = dict(qpos=float(np.max(abs(pos - expected_pos))), qvel=float(np.max(abs(vel - expected_vel))))
    if max(errors.values()) > 1e-12:
        raise RuntimeError('Canonical candidate replay mismatch: ' + json.dumps(errors))
    outcome = manipulation_outcomes(model, config['piece'], pos, vel, contacts, bad, phases, initial_z, collision_height(model, config['piece']))[0]
    if not outcome['success']:
        raise RuntimeError('Candidate failed physical demonstration criteria: ' + json.dumps(outcome))
    actor = {key: np.stack([row[key] for row in actor_rows]) for key in ACTOR_KEYS}
    validate_actor(actor, len(groups), model.nu)
    np.savez_compressed(args.output / 'actor.npz', **actor)
    chunks = np.zeros((len(groups), args.stride, model.nu))
    for frame, (start, end) in enumerate(groups):
        chunks[frame, :end - start] = tape[start:end]
        chunks[frame, end - start:] = tape[end - 1]
    np.savez_compressed(args.output / 'actions.npz', command_sequence=chunks,
        start_step=np.array([s for s, _ in groups]), valid_steps=np.array([e - s for s, e in groups]))
    np.savez_compressed(args.output / 'privileged.npz', initial=initial, controls=tape,
        before_frame_integration_state=np.asarray(pre_states), qpos=pos, qvel=vel, contacts=contacts, forbidden=bad, phase=phases)
    with (args.output / 'frame-metrics.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['frame', 'pre_action_step', 'action_steps', 'phase', 'post_interval_rise_m', 'bilateral_at_interval_end', 'forbidden_during_interval'])
        for frame, (start, end) in enumerate(groups):
            writer.writerow([frame, start, end - start, phases[start], pos[end - 1, 0, address + 2] - initial_z,
                             bool(np.all(contacts[end - 1])), bool(np.any(bad[start:end]))])
    import atom_mujoco
    report = dict(schema=1, experiment='EXP-0007', status='PHYSICAL_DEMONSTRATION_EXPORTED',
        scope='isolated close/lift/hold; conditional on verified native entry; not a learned policy',
        model_sha256=sim.manifest['model_sha256'], config_sha256=digest(args.config),
        reference_report_sha256=digest(args.reference / 'local-report.json'),
        handoff_sha256=digest(args.reference / 'handoff.json'), candidate_report_sha256=digest(args.candidate / 'report.json'),
        candidate_tape_sha256=digest(candidate_path), source_xy_m=source_xy, camera=camera,
        camera_source='configured fixed RGB view; signed native camera-derived source XY frozen at entry',
        frames=len(groups), physics_steps=len(tape), physics_dt_s=model.opt.timestep, stride=args.stride,
        actor_keys=sorted(ACTOR_KEYS), causal_alignment='RGB and issued command precede action at start_step',
        action_semantics='exact original actuator command chunks; honor valid_steps, ignore padding',
        joint_names=sim.names, outcome=outcome, replay_max_errors=errors,
        runtime_sources={p.name: digest(p) for p in sorted(Path(atom_mujoco.__file__).parent.glob('*.py'))},
        artifacts_sha256={p.name: digest(p) for p in args.output.iterdir() if p.suffix in ('.npz', '.png', '.csv')},
        limitations=['No crowded entry, transfer, placement or hardware qualification.',
            'Physics truth is excluded from actor.npz but available for safety/reward auditing.',
            'Frozen entry perception; no online re-localization or camera-only grasp verifier.',
            'Split future evaluation by reference/run, not correlated neighboring frames.'])
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'[ATOM EXP-0007] verified | {len(tape)} physics steps | {len(groups)} pre-action RGB frames', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'reference', 'candidate'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--stride', type=int, default=50, help='Physics steps per action chunk/RGB frame')
    parser.add_argument('--max-frames', type=int, default=512)
    parser.add_argument('--image-size', type=int, default=96)
    parser.add_argument('--headless', action='store_true', help='Skip the separate verified Watch replay')
    parser.add_argument('--watch-repeats', type=int, default=2)
    parser.add_argument('--watch-speed', type=float, default=1.)
    parser.add_argument('--max-wall-s', type=float, default=300.)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not (1 <= args.stride <= 1000 and 1 <= args.max_frames <= 1024 and 32 <= args.image_size <= 256
            and 1 <= args.watch_repeats <= 20 and .25 <= args.watch_speed <= 4):
        parser.error('Bounded stride, frame/image size and Watch settings required')
    if args.worker:
        try:
            worker(args)
        except Exception as error:
            (args.output / 'failure.json').write_text(json.dumps(dict(status='FAILED', error=str(error), traceback=traceback.format_exc()), indent=2))
            raise
        return
    from experiment import bounded_run
    arguments = [item for name in ('config', 'reference', 'candidate') for item in ('--' + name, str(getattr(args, name).resolve(strict=True)))]
    for name in ('stride', 'max_frames', 'image_size', 'watch_repeats', 'watch_speed'):
        arguments += ['--' + name.replace('_', '-'), str(getattr(args, name))]
    if args.headless:
        arguments.append('--headless')
    sources = [Path(__file__).with_name(n) for n in ('cem.py', 'cem_core.py', 'batch.py', 'tapes.py', 'outcomes.py', 'replay.py')]
    output, report = bounded_run(__file__, arguments, experiment='EXP-0007', output=args.output, sources=sources,
                                 max_wall_s=args.max_wall_s, request=dict(camera_actor_only=True, watch=not args.headless))
    print(json.dumps(dict(status=report['status'], output=str(output))), flush=True)
    if not args.headless:
        # A fresh process must own its GLFW context; do not open passive Watch
        # after destroying an offscreen renderer in the export worker on Windows.
        from watch_demonstration import launch
        launch(args.config, output, repeats=args.watch_repeats, speed=args.watch_speed,
               max_wall_s=args.max_wall_s, output=output / 'watch')


if __name__ == '__main__':
    main()
