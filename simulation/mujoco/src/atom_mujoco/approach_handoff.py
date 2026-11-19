"""Connect an executed native approach to an observation-only episode start."""
import time

import numpy as np

from .approach_execution import board_reference_shift, execute_approach
from .approach_planner import ApproachPlanner
from .board_piece_localization import square_offsets


def approach_handoff(scene, report, *, observer=None):
    """Advance the existing scene. Return the actor-facing frame and visual XY."""
    report['stage'] = 'PLANNING'
    plan = ApproachPlanner(scene).plan(
        require_visible_target=scene.config.get('autonomous', {}).get('require_visible_target', False))
    report['plan'] = plan
    if plan['status'] != 'PLANNED':
        raise RuntimeError(plan['reason'])
    report['validation'] = dict(ik='ACCEPTED', planned_sweep='ACCEPTED',
                                live_sweep='NOT_EXECUTED')

    report['stage'] = 'EXECUTION'
    execution = execute_approach(scene, plan, retreat=False, observer=observer)
    report['execution'] = execution
    if execution.get('preflight_failure'):
        report['validation']['live_sweep'] = 'REJECTED'
    elif execution['motion_applied']:
        report['validation']['live_sweep'] = 'ACCEPTED'
    if (execution['status'] != 'COMPLETED_SIMULATED_APPROACH'
            or not execution['approach_complete'] or execution['retreat_complete']
            or not execution['motion_applied'] or execution['reconciliation_required']):
        raise RuntimeError(execution.get('error', 'APPROACH_NOT_VERIFIED'))

    report['stage'] = 'ENDPOINT'
    planned = np.asarray(plan['target_command'])
    measured = np.asarray(execution['arrival']['position'])
    error = measured-planned
    report['endpoint'] = dict(planned_command=planned.tolist(),
        issued_command=scene.command.tolist(), measured_position=measured.tolist(),
        joint_error=error.tolist(), tracking_tolerance=execution['tracking_tolerance'],
        planned_tcp_m=plan['target_tcp_m'], measured_tcp_m=execution['arrival']['tcp_m'],
        tcp_error_m=execution['arrival']['tcp_error_m'])
    if (not np.array_equal(scene.command, planned) or not np.isfinite(error).all()
            or np.any(abs(error) > execution['tracking_tolerance'])):
        raise RuntimeError('APPROACH_ENDPOINT_TRACKING_MISMATCH')

    report['stage'] = 'ARRIVAL_PERCEPTION'
    frame = scene.observe()
    scene.last_camera_frame = frame
    perception = report['arrival_perception'] = dict(sequence=frame.sequence,
        camera_id=frame.camera_id, reference_sha256=frame.reference_sha256,
        oriented=frame.oriented, source_localized=False)
    if (not frame.oriented or frame.homography is None or frame.camera_id != plan['camera_id']
            or frame.reference_sha256 != plan['reference_sha256']
            or frame.sequence <= execution['fresh_frame_sequence']
            or not 0 <= time.monotonic()-frame.captured_at_s <= scene.config['max_perception_age_s']):
        raise RuntimeError('FRESH_MATCHING_ARRIVAL_FRAME_REQUIRED')
    clearance = plan['derived_geometry']['clearance_m']
    board_shift = board_reference_shift(frame, plan['homography'], scene.pitch)
    perception['board_reference_shift_m'] = board_shift if np.isfinite(board_shift) else None
    if board_shift > clearance:
        raise RuntimeError('ARRIVAL_BOARD_REFERENCE_CHANGED')
    source = scene.config['source']
    offsets = square_offsets(scene.empty_reference, scene.centered_reference, frame, [source], scene.pitch)
    if source not in offsets:
        raise RuntimeError('ARRIVAL_TARGET_NOT_VISUALLY_LOCALIZED')
    target_xy = scene.square_source[:2]+offsets[source]
    shift = float(np.linalg.norm(target_xy-plan['source_xy_m']))
    if not np.isfinite(shift):
        raise RuntimeError('ARRIVAL_TARGET_ESTIMATE_INVALID')
    perception.update(source_localized=True, source_xy_m=target_xy.tolist(), shift_m=shift)
    if shift > clearance:
        raise RuntimeError('ARRIVAL_TARGET_ESTIMATE_CHANGED')
    return frame, target_xy
