"""Qualify a native wrist-aware approach in the existing physical fixture."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback

import mujoco
import numpy as np

from atom_mujoco.autonomous_scene import AutonomousScene
from atom_mujoco.approach_planner import ApproachPlanner
from atom_mujoco.paths import new_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--max-candidates', type=int, default=48)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--speed-fraction', type=float, default=.25)
    parser.add_argument('--local-diagnostic', action='store_true')
    parser.add_argument('--max-local-decisions', type=int, default=1000)
    parser.add_argument('--grasp-part', choices=('stem', 'head'), default='stem')
    parser.add_argument('--closing-load-factor', type=float)
    parser.add_argument('--lift-speed-fraction', type=float, default=1.)
    args = parser.parse_args()
    if args.local_diagnostic and args.plan_only:
        parser.error('--local-diagnostic requires actual approach execution')
    if args.max_local_decisions <= 0:
        parser.error('--max-local-decisions must be positive')
    output = args.output or new_run('examples/qualify_hybrid_approach/runs')
    output.mkdir(parents=True, exist_ok=False)
    sources = [*sorted(Path(__file__).resolve().parent.glob('*.py')),
               *sorted((Path(__file__).resolve().parents[2]/'src/atom_mujoco').glob('*.py'))]
    configuration = json.loads(args.config.read_text(encoding='utf-8'))
    provenance = dict(schema=1, seed=args.seed, config=str(args.config.resolve()),
        config_sha256=hashlib.sha256(args.config.read_bytes()).hexdigest(),
        mujoco_version=mujoco.__version__, speed_fraction=args.speed_fraction,
        local_diagnostic=args.local_diagnostic, max_local_decisions=args.max_local_decisions,
        grasp_part=args.grasp_part,
        closing_load_factor=args.closing_load_factor,
        lift_speed_fraction=args.lift_speed_fraction,
        source_sha256={str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        libraries={key: dict(path=configuration[key], sha256=hashlib.sha256(
            Path(configuration[key]).read_bytes()).hexdigest()) for key in ('motion_library', 'vision_library')})
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    scene = AutonomousScene(args.config)
    provenance.update(model_profile=scene.sim.manifest['profile'],
        actual_gripper_collision_hulls=sum((scene.sim.model.geom(g).name or '').endswith('_collision_hull')
                                          for g in range(scene.sim.model.ngeom)),
        gravity_m_s2=scene.sim.model.opt.gravity.tolist())
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    handle = None
    try:
        scene.reset(seed=args.seed)
        from PIL import Image
        Image.fromarray(scene.render()).save(output/'camera-initial.png')
        if not args.headless:
            from mujoco import viewer
            display = mujoco.MjData(scene.sim.model)
            mujoco.mj_copyData(display, scene.sim.model, scene.sim.data)
            handle = viewer.launch_passive(scene.sim.model, display, show_left_ui=False, show_right_ui=False)
            with handle.lock():
                handle.cam.lookat[:] = scene.camera.lookat
                handle.cam.distance, handle.cam.azimuth, handle.cam.elevation = .8, 135, -35

        def observe(phase, info=None):
            if phase == 'APPROACH_VERIFIED':
                Image.fromarray(scene.render()).save(output/'camera-approach.png')
            if phase.startswith('VERIFYING') or phase.endswith('VERIFIED'):
                print(f'[ATOM M2] {phase} | {info or ""}', flush=True)
            if handle is not None and handle.is_running():
                with handle.lock():
                    mujoco.mj_copyData(display, scene.sim.model, scene.sim.data)
                handle.set_texts((mujoco.mjtFontScale.mjFONTSCALE_100,
                    mujoco.mjtGridPos.mjGRID_TOPLEFT,
                    'M4 / LOCAL SUPERVISOR - NO RL' if args.local_diagnostic else 'M2 / NATIVE PLANNER',
                    f'{phase}\n{info or "Full gripper collision checks enabled"}'))
                handle.sync(state_only=True)

        observe('VALIDATING APPROACH — NO RL')
        print(f'[ATOM M2] Planning | output {output}', flush=True)
        started = time.perf_counter()
        planner = ApproachPlanner(scene)
        plan = planner.plan(max_candidates=args.max_candidates)
        (output/'plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
        observe(plan['status'], f'{len(plan["candidates"])} candidate configurations examined')
        print(f'[ATOM M2] {plan["status"]} | {time.perf_counter()-started:.2f}s', flush=True)
        if args.plan_only:
            result = dict(status='PLANNED_ONLY', approach_executed=False, training_eligible=False)
        else:
            from atom_mujoco.approach_execution import execute_approach
            result = execute_approach(scene, plan, observer=observe, speed_fraction=args.speed_fraction,
                                      retreat=not args.local_diagnostic)
        (output/'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        final_status = result['status']
        if args.local_diagnostic and result.get('approach_complete'):
            from local_diagnostic import run_local_diagnostic
            diagnostic = run_local_diagnostic(scene, plan, result, output, observer=observe,
                                             max_decisions=args.max_local_decisions, grasp_part=args.grasp_part,
                                             closing_load_factor=args.closing_load_factor,
                                             lift_speed_fraction=args.lift_speed_fraction)
            (output/'local-report.json').write_text(json.dumps(diagnostic, indent=2), encoding='utf-8')
            print(f'[ATOM M4] {diagnostic["status"]} | {output / "local-report.json"}', flush=True)
            final_status = diagnostic['status']
        Image.fromarray(scene.render()).save(output/'camera-final.png')
        (output/'state-final.json').write_text(json.dumps(dict(
            qpos=scene.sim.data.qpos.tolist(), qvel=scene.sim.data.qvel.tolist(),
            ctrl=scene.sim.data.ctrl.tolist(), time_s=float(scene.sim.data.time),
            source='privileged diagnostic snapshot; excluded from actor')), encoding='utf-8')
        print(json.dumps({key: value for key, value in result.items() if key != 'segments'}), flush=True)
        observe(final_status)
        if handle is not None:
            print('[ATOM M2] Report saved. Close MuJoCo to exit.', flush=True)
            while handle.is_running():
                time.sleep(.1)
    except Exception as error:
        (output/'failure.json').write_text(json.dumps(dict(status='EXPERIMENT_FAILED',
            error=str(error), traceback=traceback.format_exc(), training_eligible=False,
            physical_state_requires_review=True), indent=2), encoding='utf-8')
        raise
    finally:
        if handle is not None:
            handle.close()
        scene.close()


if __name__ == '__main__':
    main()
