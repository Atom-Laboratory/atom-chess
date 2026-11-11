"""Execute and measure a qualified native approach, without a learned policy."""
import time

import mujoco
import numpy as np

from .approach_planner import model_identity, physical_identity, plan_identity
from .autonomous_control import interpolate_command
from .board_piece_localization import square_offsets
from .collision import SweptChecker
from .scene_feedback import SceneFeedback


def smooth_fraction(index, intervals):
    """Quintic progress with zero velocity and acceleration at both ends."""
    fraction = min(index/intervals, 1.)
    return fraction**3*(10.-15.*fraction+6.*fraction**2)


def execute_approach(scene, plan, *, observer=None, retreat=True, settle_timeout_s=2., speed_fraction=.25):
    sim, model, data = scene.sim, scene.sim.model, scene.sim.data
    report = dict(schema=1, status='REJECTED', approach_complete=False, retreat_complete=False,
                  motion_applied=False, reconciliation_required=False, training_eligible=False,
                  local_manipulation_workspace_qualified=False, segments=[],
                  scope='simulated approach and retreat; no grasp or carried-object transport')
    start_time = float(data.time)
    body_ids = [model.body(piece['name']).id for piece in sim.manifest['pieces']]
    initial_pieces = data.xpos[body_ids].copy()
    tracking_tolerance = sim.speed*model.opt.timestep
    velocity_tolerance = sim.speed/scene.dwell
    guard = scene.contact_guard
    guard.reset()
    guard.start_displacement(data)
    feedback = SceneFeedback(sim)
    runtime_failure = None
    checker = SweptChecker(model, data.qpos, sim.joint_ids, scene.collision.pairs)

    def notify(phase, info=None):
        if observer is not None:
            observer(phase, info)

    def stop():
        nonlocal runtime_failure
        guard.observe(data)
        contacts = scene.collision.unexpected_contacts(scene.config['piece'], 'APPROACHING')
        displacement = np.linalg.norm(data.xpos[body_ids]-initial_pieces, axis=1)
        excess = np.maximum(sim.lower-data.qpos[sim.qadr], data.qpos[sim.qadr]-sim.upper)
        if contacts or guard.event:
            runtime_failure = dict(category='UNEXPECTED_CONTACT', contacts=contacts, neighbor=guard.event)
        elif guard.topple_event:
            runtime_failure = dict(category='PIECE_TOPPLED', event=guard.topple_event)
        elif np.max(displacement) > feedback.limits.bystander_position_m:
            runtime_failure = dict(category='PIECE_DISPLACED', displacement_m=displacement.tolist())
        elif np.any(excess > tracking_tolerance):
            runtime_failure = dict(category='DYNAMIC_JOINT_LIMIT_EXCESS', excess=excess.tolist())
        return runtime_failure is not None

    try:
        if not np.isfinite(settle_timeout_s) or settle_timeout_s <= 0:
            raise ValueError('Positive finite settling timeout required')
        if not np.isfinite(speed_fraction) or not 0 < speed_fraction <= 1:
            raise ValueError('Speed fraction must lie in (0, 1]')
        report['speed_fraction'] = float(speed_fraction)
        report['time_parameterization'] = 'quintic rest-to-rest; peak derivative 1.875'
        if plan.get('status') != 'PLANNED':
            raise ValueError('ACCEPTED_PLAN_REQUIRED')
        if plan.get('signature') != plan_identity(plan):
            raise ValueError('PLAN_CONTENT_CHANGED')
        if model_identity(sim) != plan['model_identity']:
            raise ValueError('MODEL_CHANGED_SINCE_PLANNING')
        if physical_identity(sim) != plan['initial_physical_identity']:
            raise ValueError('SCENE_CHANGED_SINCE_PLANNING')
        if plan['joint_names'] != sim.names or not np.array_equal(scene.command, plan['initial_command']):
            raise ValueError('COMMAND_MAPPING_OR_START_CHANGED')
        if np.any(abs(data.qpos[sim.qadr]-scene.command) > tracking_tolerance):
            raise ValueError('INITIAL_COMMAND_NOT_SETTLED')
        notify('VERIFYING FRESH CAMERA REFERENCE')
        frame = scene.observe()
        if (not frame.oriented or frame.homography is None or frame.camera_id != plan['camera_id']
                or frame.reference_sha256 != plan['reference_sha256']
                or not 0 <= time.monotonic()-frame.captured_at_s <= scene.config['max_perception_age_s']):
            raise ValueError('FRESH_MATCHING_CAMERA_REFERENCE_REQUIRED')
        offsets = square_offsets(scene.empty_reference, scene.centered_reference, frame,
                                 scene.occupied, scene.pitch)
        if set(offsets) != set(plan['offsets_m']):
            raise ValueError('OCCUPIED_PIECES_NOT_VISUALLY_LOCALIZED')
        if any(np.linalg.norm(np.array(offsets[square])-plan['offsets_m'][square]) > checker.clearance
               for square in offsets):
            raise ValueError('VISUAL_SCENE_CHANGED_SINCE_PLANNING')
        height, width = frame.rectified_rgb.shape[:2]
        corners = np.array([[0., width, width, 0.], [0., 0., height, height], [1., 1., 1., 1.]])
        mapped = frame.homography@np.linalg.inv(np.asarray(plan['homography']))@corners
        mapped = mapped[:2]/mapped[2]
        delta = (mapped-corners[:2])*np.array([8*scene.pitch/width, 8*scene.pitch/height])[:, None]
        if not np.isfinite(delta).all() or np.linalg.norm(delta, axis=0).max() > checker.clearance:
            raise ValueError('BOARD_REFERENCE_CHANGED_SINCE_PLANNING')
        report['fresh_frame_sequence'] = frame.sequence
        stages = [('APPROACH', plan['approach'])]
        if retreat:
            stages.append(('RETREAT', plan['retreat']))
        cursor = sim.validate(plan['initial_command'])
        # Revalidate the entire submitted trajectory against the live simulated
        # scene before issuing the first command, including continuity and bounds.
        checker.initial[:] = data.qpos
        for phase, edges in stages:
            for edge in edges:
                start, end = sim.validate(edge['start']), sim.validate(edge['end'])
                if not np.array_equal(cursor, start):
                    raise ValueError('DISCONTINUOUS_TRAJECTORY')
                checker.samples = 0
                failure = checker.interval(start, end, prune_spheres=True)
                if failure:
                    report['preflight_failure'] = dict(phase=phase, detail=failure)
                    raise ValueError('LIVE_SCENE_PREFLIGHT_REJECTED')
                cursor = end
        for phase, edges in stages:
            for edge in edges:
                start = scene.command.copy()
                end = sim.validate(edge['end'])
                intervals = max(1, int(np.ceil(1.875*np.max(abs(end-start)/sim.speed)
                                               /(sim.dt*speed_fraction))))
                segment = dict(phase=phase, start=start.tolist(), end=end.tolist(),
                               interpolation_intervals=intervals, trace=[])
                report['segments'].append(segment)
                settled = 0
                for index in range(1, intervals+int(np.ceil(settle_timeout_s/sim.dt))+1):
                    smooth = smooth_fraction(index, intervals)
                    goal = interpolate_command(start, end, smooth, 1.)
                    state = scene.controller.step(goal, stop_when=stop)
                    scene.command = goal.copy()
                    report['motion_applied'] = True
                    segment['trace'].append(dict(time_s=float(data.time), command=goal.tolist(),
                        position=state['position'].tolist(), tcp_m=data.site('grasp_center').xpos.tolist()))
                    notify(phase, f'{min(index, intervals)}/{intervals} control intervals | wrist {goal[-1]:.3f} rad')
                    if runtime_failure:
                        report['runtime_failure'] = runtime_failure
                        raise ValueError(runtime_failure['category'])
                    stable = (index >= intervals and np.all(abs(state['position']-end) <= tracking_tolerance)
                              and np.all(abs(state['velocity']) <= velocity_tolerance))
                    settled = settled+1 if stable else 0
                    if settled >= scene.dwell:
                        break
                else:
                    raise ValueError('TRACKING_OR_SETTLING_TIMEOUT')
                segment['tracking_error'] = (state['position']-end).tolist()
                segment['elapsed_sim_s'] = segment['trace'][-1]['time_s']-segment['trace'][0]['time_s']+sim.dt
            report[phase.lower()+'_complete'] = True
            if phase == 'APPROACH':
                report['arrival'] = dict(position=state['position'].tolist(),
                    tcp_m=data.site('grasp_center').xpos.tolist(),
                    tcp_error_m=float(np.linalg.norm(data.site('grasp_center').xpos-plan['target_tcp_m'])),
                    wrist_rad=float(state['position'][-1]))
                notify('APPROACH_VERIFIED', report['arrival'])
        report['status'] = 'COMPLETED_SIMULATED_APPROACH'
        notify(report['status'])
    except (ValueError, RuntimeError, KeyError, np.linalg.LinAlgError) as error:
        report.update(status='FAILED' if report['motion_applied'] else 'REJECTED', error=str(error),
                      reconciliation_required=report['motion_applied'])
        notify(report['status'], str(error))
    report.update(elapsed_sim_s=float(data.time)-start_time,
                  model_identity=model_identity(sim), plan_signature=plan.get('signature'),
                  final_physical_identity=physical_identity(sim), final_command=scene.command.tolist(),
                  piece_displacements_mm={piece['name']:float(value*1000) for piece, value in zip(
                      sim.manifest['pieces'], np.linalg.norm(data.xpos[body_ids]-initial_pieces, axis=1))},
                  final_position=data.qpos[sim.qadr].tolist(), tracking_tolerance=tracking_tolerance.tolist(),
                  tracking_tolerance_source='one model physics-step travel at configured joint speed')
    return report
