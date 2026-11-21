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


def grasp_geometry(sim, identity, surface_z, part, closing_load_factor=None, *,
                   head_edge_fraction=None, command=None):
    if part not in ('stem', 'head'):
        raise ValueError('Expected stem or head diagnostic')
    stem = sim.model.geom(identity+'_stem')
    selected = sim.model.geom(identity+'_'+part)
    kind = int(sim.model.geom_type[selected.id])
    if kind not in (int(mujoco.mjtGeom.mjGEOM_CYLINDER), int(mujoco.mjtGeom.mjGEOM_SPHERE)):
        raise ValueError('Diagnostic requires a cylindrical or spherical selected part')
    radius = float(selected.size[0])
    effective_radius, height_offset, capacity, horizontal_factor = radius, 0., None, 1.
    if head_edge_fraction is not None:
        if (part != 'head' or kind != int(mujoco.mjtGeom.mjGEOM_SPHERE)
                or not np.isfinite(head_edge_fraction) or not 0 <= head_edge_fraction < 1
                or closing_load_factor is None or command is None):
            raise ValueError('Upper head edge requires sphere, fraction in [0, 1), load factor and command')
        scratch = mujoco.MjData(sim.model)
        scratch.qpos[:] = sim.model.qpos0
        scratch.qpos[sim.qadr] = sim.validate(command)
        mujoco.mj_forward(sim.model, scratch)
        half_heights = []
        for index in (1, 2):
            pad = sim.model.geom(f'finger_{index}_pad')
            rotation = scratch.geom_xmat[pad.id].reshape(3, 3)
            if (sim.model.geom_type[pad.id] != mujoco.mjtGeom.mjGEOM_BOX
                    or abs(rotation[2, 2]) > 1e-6 or max(abs(rotation[2])) < 1-1e-6):
                raise ValueError('Upper head edge requires upright box pads with horizontal closing normals')
            half_heights.append(float(abs(rotation[2])@pad.size))
        if not np.isclose(*half_heights, rtol=0, atol=1e-9):
            raise ValueError('Matching vertical pad extents required')
        cosine = np.sqrt(1-head_edge_fraction**2)
        effective_radius = radius*cosine
        height_offset = half_heights[0]+head_edge_fraction*radius
    radius_delta = effective_radius-float(stem.size[0])
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
        capacity = friction
        if head_edge_fraction is not None:
            capacity = friction*cosine-head_edge_fraction
            horizontal_factor = cosine+friction*head_edge_fraction
        if capacity <= 0:
            raise ValueError('Contact latitude cannot support weight under the compiled friction bound')
        normal_load = closing_load_factor*weight/(2*capacity)
        horizontal_load = normal_load*horizontal_factor
        if horizontal_load > force_limit:
            raise ValueError('Requested preload exceeds compiled finger force limits')
        interference = max(interference, horizontal_load/gain)
        load = dict(factor=closing_load_factor, weight_N=weight, friction_lower_bound=friction,
                    finger_gain_N_per_m=gain, estimated_normal_load_N=normal_load,
                    vertical_capacity_per_normal_N=capacity, estimated_horizontal_load_N=horizontal_load)
    result = dict(part=part, geom=selected.name, radius_m=radius,
        head_edge_fraction=head_edge_fraction, effective_radius_m=float(effective_radius),
        pad_center_height_offset_m=float(height_offset),
        tcp_z_m=surface_z+float(selected.pos[2])+height_offset,
        aperture_m=pregrasp_opening(sim, identity)+radius_delta,
        closing_target_m=pregrasp_opening(sim, identity, side_gap_m=-interference)+radius_delta,
        closing_interference_m=interference, model_load_estimate=load,
        assumptions='experimental Coulomb/static-servo approximation; not measured hardware force')
    if not sim.lower[3] <= result['closing_target_m'] <= sim.upper[3]:
        raise ValueError('Requested preload exceeds finger travel')
    return result


def diagnostic_xy_bounds(source, entry, half_width, step_travel):
    """Include the verified lateral start; this is a bound, not a clearance proof."""
    source, entry, step_travel = map(np.asarray, (source, entry, step_travel))
    return (np.minimum(source-half_width, entry-step_travel),
            np.maximum(source+half_width, entry+step_travel))


def hold_grasp(supervisor, identity, dwell, record):
    """Evaluate sustained simulation contact; never feed this into a command."""
    if type(dwell) is not int or dwell <= 0:
        raise ValueError('Positive integer dwell required')
    streak, samples = 0, []
    for _ in range(2*dwell):
        action = [0.]*5
        result = supervisor.qualification_step(action, phase='GRASPING')
        record('HOLD_CLOSE', action, result)
        if result['status'] != 'EXECUTED_SIMULATION':
            return dict(confirmed=False, failure=result, samples=samples, required_consecutive=dwell)
        contact = bool(supervisor.feedback.grip_contacts(identity))
        settled = bool(supervisor.feedback.settled(identity))
        streak = streak+1 if contact and settled else 0
        samples.append(dict(bilateral_contact=contact, settled=settled, consecutive=streak))
        if streak >= dwell:
            return dict(confirmed=True, samples=samples, required_consecutive=dwell)
    return dict(confirmed=False, samples=samples, required_consecutive=dwell)


def lifted_hold_valid(sample, minimum_rise_m, maximum_slip_m):
    return bool(sample['rise_m']>=minimum_rise_m and sample['vertical_slip_m']<=maximum_slip_m
                and sample['bilateral_contact'] and sample['settled'])


def run_local_diagnostic(scene, plan, approach, output, *, observer, max_decisions=1000,
                         grasp_part='stem', closing_load_factor=None, lift_speed_fraction=1.,
                         head_edge_fraction=None, diagnostic_wrist_rad=None, target_finger_clearance_m=None,
                         lift_rise_heights=None, lift_hold_s=0., max_lift_slip_m=.003):
    if not np.isfinite(lift_speed_fraction) or not 0 < lift_speed_fraction <= 1:
        raise ValueError('Lift speed fraction must be in (0, 1]')
    if lift_rise_heights is not None and (not np.isfinite(lift_rise_heights) or lift_rise_heights < 1):
        raise ValueError('Diagnostic lift travel must be at least one piece height')
    if not np.isfinite([lift_hold_s,max_lift_slip_m]).all() or not 0<=lift_hold_s<=10 or not 0<=max_lift_slip_m<=.01:
        raise ValueError('Lift hold must be 0..10 s with a slip threshold 0..10 mm')
    sim = scene.sim
    control = AutonomousControl(scene)
    source = np.asarray(plan['source_xy_m'])
    half = scene.pitch/2
    drop = plan['derived_geometry']['tool_drop_m']
    lower_z = scene.surface_z+drop+control.checker.clearance
    upper_z = plan['target_tcp_m'][2]+scene.piece_height
    rates = control.rates*.25/1.875
    lower_xy, upper_xy = diagnostic_xy_bounds(source, np.asarray(plan['target_tcp_m'])[:2],
                                             half, rates[:2]*sim.dt)
    limits = LocalLimits(tuple(sim.lower), tuple(sim.upper),
        (*list(lower_xy), lower_z, sim.lower[-1], sim.lower[3]),
        (*list(upper_xy), upper_z, sim.upper[-1], sim.upper[3]),
        tuple(rates), sim.dt, 'unqualified-diagnostic:'+plan['signature'])
    task = MoveTask('local-diagnostic-'+uuid.uuid4().hex, scene.config['piece'],
        scene.config['source'], scene.task_target, 0,
        max_decisions*scene.config['max_perception_age_s'])
    supervisor = LocalSupervisor(scene, task, limits, observer=observer,
                                 target_finger_clearance_m=target_finger_clearance_m)
    supervisor.begin_qualification(plan, approach, max_decisions=max_decisions)
    report = dict(schema=1, status='DIAGNOSTIC_STARTED', owner='DETERMINISTIC_QUALIFICATION',
        training_eligible=False, local_manipulation_workspace_qualified=False,
        visual_grasp_verified=False, grasp_success=False, lift_success=False, stages=[],
        limits=vars(limits), max_decisions=max_decisions, geometry_source='existing experimental colliders')
    report['lift_speed_fraction'] = lift_speed_fraction
    report['target_finger_clearance_m'] = target_finger_clearance_m
    report['lift_rise_heights'] = lift_rise_heights
    report['lift_hold_s'],report['max_lift_slip_m']=lift_hold_s,max_lift_slip_m
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
        wrist = float(scene.command[-1] if diagnostic_wrist_rad is None else diagnostic_wrist_rad)
        geometry_command = scene.command.copy()
        geometry_command[-1] = wrist
        report['grasp_geometry'] = geometry = grasp_geometry(sim, scene.config['piece'], scene.surface_z,
            grasp_part, closing_load_factor, head_edge_fraction=head_edge_fraction, command=geometry_command)
        pick_z, aperture, grasp = geometry['tcp_z_m'], geometry['aperture_m'], geometry['closing_target_m']
        targets = []
        if head_edge_fraction is not None:
            current = control.commanded_tcp(scene.command)
            targets += [('ALIGN_WRIST', np.array([*current, wrist, scene.command[3]]), 'GRASPING'),
                        ('CENTER_ABOVE', np.array([*source, current[2], wrist, aperture]), 'GRASPING')]
        lift_z = (max(plan['target_tcp_m'][2], pick_z+1.5*scene.piece_height)
                  if head_edge_fraction is not None else plan['target_tcp_m'][2])
        if lift_rise_heights is not None:
            lift_z = max(plan['target_tcp_m'][2], pick_z+lift_rise_heights*scene.piece_height)
        targets += [('DESCEND', np.array([*source, pick_z, wrist, aperture]), 'GRASPING'),
                   ('CLOSE', np.array([*source, pick_z, wrist, grasp]), 'GRASPING'),
                   ('LIFT', np.array([*source, lift_z, wrist, grasp]), 'LIFTING')]
        for name, target, phase in targets:
            if sim.step_observer is not None:sim.step_observer.phase=name
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
                if sim.step_observer is not None:sim.step_observer.phase='HOLD_CLOSE'
                report['initial_bilateral_contact'] = bool(supervisor.feedback.grip_contacts(scene.config['piece']))
                report['grasp_hold'] = hold_grasp(supervisor, scene.config['piece'], scene.dwell, record)
                report['grasp_success'] = report['grasp_hold']['confirmed']
                if not report['grasp_success']:
                    report['status'] = 'GRASP_HOLD_NOT_CONFIRMED_IN_SIMULATION'
                    return finish()
        report['measured_lift_m'] = float(sim.data.xpos[body, 2])-initial_z
        report['lift_success'] = bool(report['grasp_success'] and report['measured_lift_m'] >= scene.piece_height
            and supervisor.feedback.grip_contacts(scene.config['piece'])
            and supervisor.feedback.settled(scene.config['piece']))
        if report['lift_success'] and lift_hold_s>0:
            if sim.step_observer is not None:sim.step_observer.phase='LIFT_HOLD'
            hold_start=float(sim.data.time);peak_z=float(sim.data.xpos[body,2]);samples=[]
            report['lift_hold']=dict(confirmed=False,samples=samples)
            while float(sim.data.time)-hold_start<lift_hold_s:
                result=supervisor.qualification_step([0.]*5,phase='LIFTING')
                record('LIFT_HOLD',[0.]*5,result)
                height=float(sim.data.xpos[body,2]);peak_z=max(peak_z,height)
                sample=dict(elapsed_sim_s=float(sim.data.time)-hold_start,rise_m=height-initial_z,
                    vertical_slip_m=peak_z-height,bilateral_contact=bool(supervisor.feedback.grip_contacts(scene.config['piece'])),
                    settled=bool(supervisor.feedback.settled(scene.config['piece'])))
                samples.append(sample)
                if (result['status']!='EXECUTED_SIMULATION'
                        or not lifted_hold_valid(sample,scene.piece_height,max_lift_slip_m)):
                    report['lift_hold']['failure']=result
                    report['lift_success']=False;report['status']='LIFT_HOLD_NOT_CONFIRMED'
                    return finish()
            report['lift_hold']['confirmed']=True
        report['status'] = 'SIMULATED_LIFT_DIAGNOSTIC' if report['lift_success'] else 'LIFT_NOT_CONFIRMED'
        report['feedback_source'] = 'simulation evaluation only; camera-only outcome verifier still unqualified'
        report['decisions'] = supervisor.decisions
        return finish()
