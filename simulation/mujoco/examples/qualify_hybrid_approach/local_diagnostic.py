"""Bounded deterministic diagnostic, never a learned-policy admission."""
import json
import time
import uuid

import mujoco
import numpy as np
from PIL import Image

from atom_mujoco.autonomous_control import AutonomousControl
from atom_mujoco.collision import pregrasp_opening
from atom_mujoco.hybrid_contract import LocalLimits
from atom_mujoco.local_supervisor import LocalSupervisor
from atom_mujoco.supervision import MoveTask


def grasp_geometry(sim, identity, surface_z, part, closing_load_factor=None):
    if part not in ('stem', 'head'):
        raise ValueError('Expected stem or head diagnostic')
    stem = sim.model.geom(identity+'_stem')
    selected = sim.model.geom(identity+'_'+part)
    kind = int(sim.model.geom_type[selected.id])
    if kind not in (int(mujoco.mjtGeom.mjGEOM_CYLINDER), int(mujoco.mjtGeom.mjGEOM_SPHERE)):
        raise ValueError('Diagnostic requires a cylindrical or spherical selected part')
    radius_delta = float(selected.size[0]-stem.size[0])
    interference = .0005
    load = None
    if closing_load_factor is not None:
        if not np.isfinite(closing_load_factor) or closing_load_factor < 1:
            raise ValueError('Closing load factor must be finite and at least one')
        pads = [sim.model.geom(f'finger_{i}_pad').id for i in (1, 2)]
        friction = float(sim.model.geom_friction[[selected.id, *pads], 0].min())
        gain = float(sim.model.actuator_gainprm[3:5, 0].min())
        weight = float(sim.model.body_mass[sim.model.body(identity).id]*np.linalg.norm(sim.model.opt.gravity))
        force_limit = float(np.abs(sim.model.actuator_forcerange[3:5]).min())
        if friction <= 0 or gain <= 0:
            raise ValueError('Positive compiled friction and finger gains required')
        normal_load = closing_load_factor*weight/(2*friction)
        if normal_load > force_limit:
            raise ValueError('Requested preload exceeds compiled finger force limits')
        interference = max(interference, normal_load/gain)
        load = dict(factor=closing_load_factor, weight_N=weight, friction_lower_bound=friction,
                    finger_gain_N_per_m=gain, estimated_normal_load_N=normal_load)
    result = dict(part=part, geom=selected.name, radius_m=float(selected.size[0]),
        tcp_z_m=surface_z+float(selected.pos[2]),
        aperture_m=pregrasp_opening(sim, identity)+radius_delta,
        closing_target_m=pregrasp_opening(sim, identity, side_gap_m=-interference)+radius_delta,
        closing_interference_m=interference, model_load_estimate=load,
        assumptions='experimental Coulomb/static-servo approximation; not measured hardware force')
    if not sim.lower[3] <= result['closing_target_m'] <= sim.upper[3]:
        raise ValueError('Requested preload exceeds finger travel')
    return result


def run_local_diagnostic(scene, plan, approach, output, *, observer, max_decisions=1000,
                         grasp_part='stem', closing_load_factor=None, lift_speed_fraction=1.):
    if not np.isfinite(lift_speed_fraction) or not 0 < lift_speed_fraction <= 1:
        raise ValueError('Lift speed fraction must be in (0, 1]')
    sim = scene.sim
    control = AutonomousControl(scene)
    source = np.asarray(plan['source_xy_m'])
    half = scene.pitch/2
    drop = plan['derived_geometry']['tool_drop_m']
    lower_z = scene.surface_z+drop+control.checker.clearance
    upper_z = plan['target_tcp_m'][2]+scene.piece_height
    limits = LocalLimits(tuple(sim.lower), tuple(sim.upper),
        (*list(source-half), lower_z, sim.lower[-1], sim.lower[3]),
        (*list(source+half), upper_z, sim.upper[-1], sim.upper[3]),
        tuple(control.rates*.25/1.875), sim.dt, 'unqualified-diagnostic:'+plan['signature'])
    task = MoveTask('local-diagnostic-'+uuid.uuid4().hex, scene.config['piece'],
        scene.config['source'], scene.task_target, 0,
        max_decisions*scene.config['max_perception_age_s'])
    supervisor = LocalSupervisor(scene, task, limits, observer=observer)
    supervisor.begin_qualification(plan, approach, max_decisions=max_decisions)
    report = dict(schema=1, status='DIAGNOSTIC_STARTED', owner='DETERMINISTIC_QUALIFICATION',
        training_eligible=False, local_manipulation_workspace_qualified=False,
        visual_grasp_verified=False, grasp_success=False, lift_success=False, stages=[],
        limits=vars(limits), max_decisions=max_decisions, geometry_source='existing experimental colliders')
    report['lift_speed_fraction'] = lift_speed_fraction
    started = time.perf_counter()
    body = sim.model.body(scene.config['piece']).id
    initial_z = float(sim.data.xpos[body, 2])  # Independent evaluation, never a target.

    def finish():
        report.update(decisions=supervisor.decisions, elapsed_wall_s=time.perf_counter()-started,
            camera_captures=supervisor.camera_captures, camera_reuses=supervisor.camera_reuses,
            measured_lift_m=float(sim.data.xpos[body, 2])-initial_z,
            final_pad_contacts=supervisor.feedback.pad_contacts(scene.config['piece']))
        return report
    path = output/'local-decisions.jsonl'
    with path.open('x', encoding='utf-8') as trace:
        def record(stage, action, result):
            result['camera_captures'] = supervisor.camera_captures
            result['camera_reuses'] = supervisor.camera_reuses
            trace.write(json.dumps(dict(stage=stage, action=list(action), result=result))+'\n')
            trace.flush()
            if supervisor.decisions % 10 == 0 or result['status'] != 'EXECUTED_SIMULATION':
                print(f'[ATOM M4] {supervisor.decisions}/{max_decisions} | {stage} | {result["status"]}', flush=True)

        # Demonstrate one individually checked local step before screening the
        # full descent. This does not claim the complete envelope is safe.
        action = [0., 0., -.25, 0., 0.]
        initial = supervisor.qualification_step(action, phase='GRASPING')
        record('LOCAL_DESCENT_PROBE', action, initial)
        report['probe'] = initial
        if initial['status'] != 'EXECUTED_SIMULATION':
            report['status'] = 'LOCAL_PROBE_REJECTED_OR_FAILED'
            return finish()
        report['grasp_geometry'] = geometry = grasp_geometry(sim, scene.config['piece'], scene.surface_z,
                                                           grasp_part, closing_load_factor)
        pick_z, aperture, grasp = geometry['tcp_z_m'], geometry['aperture_m'], geometry['closing_target_m']
        wrist = float(scene.command[-1])
        targets = [('DESCEND', np.array([*source, pick_z, wrist, aperture]), 'GRASPING'),
                   ('CLOSE', np.array([*source, pick_z, wrist, grasp]), 'GRASPING'),
                   ('LIFT', np.array([*source, plan['target_tcp_m'][2], wrist, grasp]), 'LIFTING')]
        for name, target, phase in targets:
            screen = supervisor.screen_target(target[:3], target[4], target[3])
            stage = dict(name=name, target=target.tolist(), screen=screen)
            report['stages'].append(stage)
            if screen['status'] != 'PATH_SCREENED':
                report['status'] = 'BASELINE_PATH_REJECTED'
                report['decisions'] = supervisor.decisions
                observer(report['status'], screen)
                return finish()
            while True:
                current = np.array([*control.commanded_tcp(scene.command), scene.command[-1], scene.command[3]])
                delta = target-current
                # This constructs a deterministic proposal; the supervisor never
                # projects/scales an action after it has been proposed.
                if np.max(abs(delta)/(np.asarray(limits.rates)*sim.dt)) < 1e-6:
                    break
                action = np.clip(delta/(np.asarray(limits.rates)*sim.dt), -1., 1.)
                if phase == 'LIFTING':
                    action[:3] = np.clip(action[:3], -lift_speed_fraction, lift_speed_fraction)
                result = supervisor.qualification_step(action, phase=phase)
                record(name, action, result)
                if result['status'] != 'EXECUTED_SIMULATION':
                    stage['failure'] = result
                    report['status'] = 'BASELINE_EXECUTION_REJECTED_OR_FAILED'
                    report['decisions'] = supervisor.decisions
                    return finish()
            Image.fromarray(scene.render()).save(output/f'camera-local-{name.lower()}.png')
            if name == 'CLOSE':
                report['grasp_success'] = bool(supervisor.feedback.grip_contacts(scene.config['piece'])
                                              and supervisor.feedback.settled(scene.config['piece']))
                if not report['grasp_success']:
                    report['status'] = 'GRASP_NOT_CONFIRMED_IN_SIMULATION'
                    return finish()
        report['measured_lift_m'] = float(sim.data.xpos[body, 2])-initial_z
        report['lift_success'] = bool(report['grasp_success'] and report['measured_lift_m'] >= scene.piece_height
            and supervisor.feedback.grip_contacts(scene.config['piece'])
            and supervisor.feedback.settled(scene.config['piece']))
        report['status'] = 'SIMULATED_LIFT_DIAGNOSTIC' if report['lift_success'] else 'LIFT_NOT_CONFIRMED'
        report['feedback_source'] = 'simulation evaluation only; camera-only outcome verifier still unqualified'
        report['decisions'] = supervisor.decisions
        return finish()
