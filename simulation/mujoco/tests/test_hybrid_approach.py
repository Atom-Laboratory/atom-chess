from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from atom_mujoco.approach_execution import execute_approach, smooth_fraction
from atom_mujoco.approach_planner import geometry_bounds, model_identity, physical_identity, plan_identity


def test_rotated_off_center_geometry_bounds():
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    model = SimpleNamespace(geom_aabb=np.array([[.1, .2, .3, .4, .5, .6]]))
    data = SimpleNamespace(geom_xmat=rotation.reshape(1, 9), geom_xpos=np.array([[1., 2., 3.]]))
    lower, upper = geometry_bounds(model, data, [0])
    np.testing.assert_allclose(lower, [[.3, 1.7, 2.7]])
    np.testing.assert_allclose(upper, [[1.3, 2.5, 3.9]])


def test_quintic_progress_preserves_path_and_peak_speed():
    intervals = 10000
    values = np.array([smooth_fraction(index, intervals) for index in range(intervals+1)])
    assert values[0] == 0. and values[-1] == 1.
    assert np.all(np.diff(values) >= 0)
    assert np.max(np.diff(values))*intervals <= 1.875+1e-8
    assert values[1] < 1e-10 and 1.-values[-2] < 1e-10


def test_plan_signature_covers_nested_route_and_region():
    plan = {'status': 'PLANNED', 'approach': [{'end': [1., 2.]}], 'entry_region': {'lower': [0.]}}
    signature = plan_identity(plan)
    plan['signature'] = signature
    assert plan_identity(plan) == signature
    plan['entry_region']['lower'][0] = -.1
    assert plan_identity(plan) != signature
    with pytest.raises(ValueError):
        plan_identity({'bad': float('nan')})


@pytest.fixture
def execution_scene(sim):
    # Early rejection tests must never issue an actuator command or query RGB.
    guard = SimpleNamespace(reset=Mock(), start_displacement=Mock())
    return SimpleNamespace(sim=sim, command=sim.reference.copy(), dwell=2,
                           config={}, contact_guard=guard,
                           collision=SimpleNamespace(pairs=[]), observe=Mock(), controller=Mock())


def signed_start(scene):
    sim = scene.sim
    plan = dict(status='PLANNED', model_identity=model_identity(sim),
                initial_physical_identity=physical_identity(sim),
                joint_names=sim.names, initial_command=scene.command.tolist())
    plan['signature'] = plan_identity(plan)
    return plan


@pytest.mark.parametrize('change,reason', [
    ('contents', 'PLAN_CONTENT_CHANGED'),
    ('model', 'MODEL_CHANGED_SINCE_PLANNING'),
    ('scene', 'SCENE_CHANGED_SINCE_PLANNING'),
    ('command', 'COMMAND_MAPPING_OR_START_CHANGED'),
])
def test_stale_or_modified_plan_cannot_move_robot(execution_scene, change, reason):
    scene = execution_scene
    plan = signed_start(scene)
    if change == 'contents':
        plan['initial_command'][0] += .001
    elif change == 'model':
        scene.sim.model.dof_damping[0] += .001
    elif change == 'scene':
        scene.sim.data.qvel[0] += .001
    else:
        scene.command[0] += .001
    initial = scene.sim.data.qpos.copy()
    report = execute_approach(scene, plan)
    assert report['status'] == 'REJECTED' and report['error'] == reason
    assert not report['motion_applied'] and not report['training_eligible']
    scene.controller.step.assert_not_called()
    scene.observe.assert_not_called()
    np.testing.assert_array_equal(scene.sim.data.qpos, initial)


@pytest.mark.parametrize('fraction', [0., -1., 1.01, float('nan')])
def test_invalid_timing_rejected_before_execution(execution_scene, fraction):
    report = execute_approach(execution_scene, signed_start(execution_scene), speed_fraction=fraction)
    assert report['status'] == 'REJECTED'
    assert report['error'] == 'Speed fraction must lie in (0, 1]'
    execution_scene.controller.step.assert_not_called()


def test_fresh_camera_and_continuous_route_required_before_motion(execution_scene, monkeypatch):
    import time
    import atom_mujoco.approach_execution as module

    scene = execution_scene
    frame = SimpleNamespace(oriented=True, homography=np.eye(3), camera_id='camera',
        reference_sha256='reference', captured_at_s=time.monotonic(), sequence=5,
        rectified_rgb=np.zeros((80, 80, 3), dtype=np.uint8))
    scene.observe.return_value = frame
    scene.empty_reference = scene.centered_reference = object()
    scene.occupied = {'e2': 'P'}
    scene.pitch = .035
    scene.config = {'max_perception_age_s': 10.}
    monkeypatch.setattr(module, 'square_offsets', lambda *args: {'e2': [0., 0.]})
    plan = signed_start(scene)
    plan.update(camera_id='camera', reference_sha256='reference', offsets_m={'e2': [0., 0.]},
                homography=np.eye(3).tolist(), approach=[], retreat=[])
    bad_start = scene.command.copy()
    bad_start[0] += .001
    plan['approach'] = [dict(start=bad_start.tolist(), end=scene.command.tolist())]
    plan['signature'] = plan_identity(plan)
    report = execute_approach(scene, plan)
    assert report['error'] == 'DISCONTINUOUS_TRAJECTORY'
    assert not report['motion_applied']
    scene.controller.step.assert_not_called()

    frame.oriented = False
    report = execute_approach(scene, plan)
    assert report['error'] == 'FRESH_MATCHING_CAMERA_REFERENCE_REQUIRED'
    scene.controller.step.assert_not_called()
