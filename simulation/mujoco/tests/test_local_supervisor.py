import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from atom_mujoco.approach_planner import model_identity, physical_identity, plan_identity
from atom_mujoco.autonomous_control import AutonomousControl
from atom_mujoco.backend import Simulation
from atom_mujoco.collision import SceneCollision
from atom_mujoco.contact_supervision import NonTargetContacts
from atom_mujoco.hybrid_contract import ApproachAdmission, LocalHandoff, LocalLimits, LocalProposal
from atom_mujoco.local_supervisor import LocalSupervisor
from atom_mujoco.model import build_bundle
from atom_mujoco.motion_controller import MotionController
from atom_mujoco.supervision import Evidence, Execution, MoveTask, TaskLedger


@pytest.fixture(scope='module')
def wrist_bundle(tmp_path_factory):
    path = tmp_path_factory.mktemp('local-supervisor')/'bundle'
    build_bundle(Path(__file__).resolve().parents[2]/'src/urdf/atom.urdf.xacro', path,
                 interactive=True, wrist=True, full_gripper_collision=True)
    return path


@pytest.fixture
def supervisor(wrist_bundle):
    sim = Simulation(wrist_bundle)
    command = np.array([-1.5, .12, -1.5, 0., 0., 1.25])
    sim.reset(command)
    controller = MotionController(sim)
    for _ in range(60):
        controller.step(command)
    collision = SceneCollision(sim)
    scene = SimpleNamespace(sim=sim, config={'piece':'white_pawn_e2', 'source':'e2', 'max_perception_age_s':1.},
        command=command, task_target='e4', dwell=10, pitch=sim.manifest['scene']['square_size_m'],
        controller=controller, collision=collision,
        vision=SimpleNamespace(camera_id='test-camera', reference_sha256='test-reference'))
    # Unit-level native solve stand-in, correct only for a zero-action target.
    # Actual nonzero native IK and vision are exercised by the watched diagnostic.
    scene.motion = SimpleNamespace(has_wrist=True, geometry=np.array([150., 150.]),
                                   solve=Mock(return_value=command.copy()))
    scene.contact_guard = NonTargetContacts(sim.model, collision.robot,
        [p['name'] for p in sim.manifest['pieces']], 'white_pawn_e2')
    sequence = [0]

    def observe():
        sequence[0] += 1
        return SimpleNamespace(sequence=sequence[0], captured_at_s=time.monotonic(), oriented=True,
            homography=np.eye(3), camera_id='test-camera', reference_sha256='test-reference',
            rectified_rgb=np.zeros((80, 80, 3), dtype=np.uint8))

    scene.observe = Mock(side_effect=observe)
    control = AutonomousControl(scene)
    tcp = control.commanded_tcp(command)
    limits = LocalLimits(tuple(sim.lower), tuple(sim.upper),
        (*list(tcp-.02), sim.lower[-1], sim.lower[3]),
        (*list(tcp+.02), sim.upper[-1], sim.upper[3]),
        tuple(control.rates*.1), sim.dt, 'synthetic-test-envelope')
    task = MoveTask('test-move', 'white_pawn_e2', 'e2', 'e4', 0, 60.)
    return LocalSupervisor(scene, task, limits)


def authorize_test_session(supervisor):
    # Synthetic approach assertions test the admission/wiring contract only.
    # They are not a claim that this unit fixture executed an M2 approach.
    plan = dict(status='PLANNED', model_identity=supervisor.model_id, homography=np.eye(3).tolist(),
        camera_id=supervisor.camera_id, reference_sha256=supervisor.reference,
        piece=supervisor.task.piece_id, source=supervisor.task.source_square)
    plan['signature'] = plan_identity(plan)
    report = dict(status='COMPLETED_SIMULATED_APPROACH', approach_complete=True, retreat_complete=False,
        plan_signature=plan['signature'], final_physical_identity=physical_identity(supervisor.sim),
        model_identity=supervisor.model_id, final_command=supervisor.scene.command.tolist())
    supervisor.begin_qualification(plan, report, max_decisions=10)
    return plan, report


def test_rl_cannot_use_deterministic_lane_without_lease(supervisor):
    authorize_test_session(supervisor)
    before = supervisor.sim.data.time
    assert supervisor.step(None)['category'] == 'RL_LEASE_REQUIRED'
    assert supervisor.sim.data.time == before


def test_qualification_requires_current_unretreated_approach(supervisor):
    plan, report = authorize_test_session(supervisor)
    supervisor.qualification = False
    report['retreat_complete'] = True
    with pytest.raises(ValueError, match='Current verified unretreated'):
        supervisor.begin_qualification(plan, report, max_decisions=10)


def test_bad_actions_never_reach_controller(supervisor):
    authorize_test_session(supervisor)
    supervisor.scene.controller.step = Mock()
    assert supervisor.qualification_step([float('nan')]*5, phase='GRASPING')['category'] == 'INVALID_INPUT'
    assert supervisor.qualification_step([2., 0., 0., 0., 0.], phase='GRASPING')['category'] == 'ACTION_BOUNDS'
    assert supervisor.qualification_step([0.]*5, phase='TRANSPORTING')['category'] == 'PHASE_NOT_AUTHORIZED'
    supervisor.scene.controller.step.assert_not_called()


@pytest.mark.parametrize('change,category', [('model','MODEL_CHANGED'), ('state','EXTERNAL_SCENE_OR_CONTROLLER_CHANGE')])
def test_changed_model_or_state_requires_reconciliation(supervisor, change, category):
    authorize_test_session(supervisor)
    if change == 'model':
        supervisor.sim.model.dof_damping[0] += .01
    else:
        supervisor.sim.data.qvel[0] += .01
    before = supervisor.sim.data.time
    result = supervisor.qualification_step([0.]*5, phase='GRASPING')
    assert result['category'] == category and result['reconciliation_required']
    assert supervisor.sim.data.time == before
    assert supervisor.qualification_step([0.]*5, phase='GRASPING')['category'] == 'RECONCILIATION_REQUIRED'


@pytest.mark.parametrize('change', ['stale', 'reference', 'camera', 'orientation', 'sequence', 'board_moved'])
def test_invalid_perception_never_executes(supervisor, change):
    authorize_test_session(supervisor)
    frame = supervisor.scene.observe()
    if change == 'stale':
        frame.captured_at_s -= 2.
    elif change == 'reference':
        frame.reference_sha256 = 'other'
    elif change == 'camera':
        frame.camera_id = 'other'
    elif change == 'orientation':
        frame.oriented = False
    elif change == 'sequence':
        supervisor.sequence = frame.sequence
    else:
        frame.homography[0, 2] = 20.
    supervisor.scene.observe = Mock(return_value=frame)
    before = supervisor.sim.data.time
    result = supervisor.qualification_step([0.]*5, phase='GRASPING')
    assert result['status'] == 'STOPPED' and result['reconciliation_required']
    assert supervisor.sim.data.time == before


def test_native_ik_rejection_is_explicit_and_never_projected(supervisor):
    authorize_test_session(supervisor)
    supervisor.scene.motion.solve.side_effect = ValueError('fixture IK unreachable')
    result = supervisor.qualification_step([0.]*5, phase='GRASPING')
    assert result['category'] == 'IK_OR_LIMIT_REJECTED'
    assert result['detail']['reason'] == 'fixture IK unreachable'
    assert supervisor.scene.motion.solve.call_count == 1


def test_swept_collision_rejection_never_executes(supervisor):
    authorize_test_session(supervisor)
    supervisor.control.checker.interval = Mock(return_value={'status':'collision', 'geoms':['hand','neighbor']})
    supervisor.scene.controller.step = Mock()
    result = supervisor.qualification_step([0.]*5, phase='GRASPING')
    assert result['category'] == 'SWEEP_REJECTED'
    assert result['detail']['failure']['geoms'] == ['hand', 'neighbor']
    supervisor.scene.controller.step.assert_not_called()


def test_zero_action_advances_real_physics_after_all_checks(supervisor):
    authorize_test_session(supervisor)
    before = supervisor.sim.data.time
    result = supervisor.qualification_step([0.]*5, phase='GRASPING')
    assert result['status'] == 'EXECUTED_SIMULATION'
    assert supervisor.sim.data.time > before
    assert result['owner'] == 'DETERMINISTIC_QUALIFICATION'
    assert result['transformation'] == 'none' and not result['training_eligible']
    assert supervisor.expected_physical == physical_identity(supervisor.sim)
    assert supervisor.scene.observe.call_count == 1
    assert result['camera_captures'] == 1 and result['camera_reuses'] == 1


def test_perception_rechecked_after_slow_preflight(supervisor):
    authorize_test_session(supervisor)
    original = supervisor.control.validate

    def validate(*args, **kwargs):
        result = original(*args, **kwargs)
        supervisor.last_frame.captured_at_s -= 2.
        supervisor.scene.observe.side_effect = RuntimeError('camera disconnected during preflight')
        return result

    supervisor.control.validate = validate
    supervisor.scene.controller.step = Mock()
    result = supervisor.qualification_step([0.]*5, phase='GRASPING')
    assert result['category'] == 'PERCEPTION_OR_COMMAND_FAILURE'
    supervisor.scene.controller.step.assert_not_called()


def test_runtime_topple_stops_future_commands(supervisor):
    authorize_test_session(supervisor)
    supervisor.scene.contact_guard.topple_event = {'piece':'neighbor'}
    before = supervisor.sim.data.time
    result = supervisor.qualification_step([0.]*5, phase='GRASPING')
    assert result['category'] == 'PIECE_TOPPLED' and not result['motion_applied']
    assert supervisor.sim.data.time == before


def test_budget_exhaustion_cannot_issue_another_command(supervisor):
    authorize_test_session(supervisor)
    supervisor.decisions = supervisor.max_decisions
    assert supervisor.qualification_step([0.]*5, phase='GRASPING')['category'] == 'QUALIFICATION_BUDGET_EXHAUSTED'


def test_unsafe_declared_rates_rejected_at_construction(supervisor):
    from dataclasses import replace
    with pytest.raises(ValueError, match='exceed selected model'):
        LocalSupervisor(supervisor.scene, supervisor.task,
                        replace(supervisor.limits, rates=(1e5,)*5))


def test_rl_proposal_reaches_physics_only_through_admitted_real_lease(supervisor, tmp_path):
    from dataclasses import replace
    import hashlib
    import json
    ledger = TaskLedger(tmp_path/'lease.sqlite')
    try:
        now = time.monotonic()
        execution = Execution(supervisor.task, ledger, now_s=now-1., max_age_s=1.)
        for index, (source, signals) in enumerate([
            ('board', {'preconditions_valid'}), ('planner', {'plan_valid'}), ('robot', {'approach_settled'}),
        ]):
            timestamp = now-.5+index*.1
            execution.advance(Evidence(source, timestamp, index, frozenset(signals), 0), now_s=timestamp)
        baseline = tmp_path/'synthetic-baseline.json'
        baseline.write_text(json.dumps(dict(grasp_success=True, lift_success=True, synthetic_test_only=True)))
        artifact = dict(schema=1, scope='simulation_only_local_grasp_lift_with_per_action_sweeps',
            qualified=True, training_eligible=True, model_identity=supervisor.model_id,
            task_id=supervisor.task.task_id, board_revision=0, camera_id=supervisor.camera_id,
            reference_sha256=supervisor.reference,
            limits={key:value for key,value in vars(supervisor.limits).items() if key != 'workspace_evidence_id'},
            baseline_reports=[dict(path=baseline.name, sha256=hashlib.sha256(baseline.read_bytes()).hexdigest())])
        artifact_path = tmp_path/'synthetic-workspace.json'
        artifact_path.write_text(json.dumps(artifact), encoding='utf-8')
        limits = replace(supervisor.limits, workspace_evidence_id=hashlib.sha256(artifact_path.read_bytes()).hexdigest())
        gate = LocalHandoff(execution, limits, model_identity=supervisor.model_id,
                            camera_id=supervisor.camera_id, reference_sha256=supervisor.reference)
        # Synthetic test qualification: this is not a real grasp-workspace proof.
        admission = ApproachAdmission(supervisor.task.task_id, 0, supervisor.model_id,
            supervisor.camera_id, supervisor.reference, limits.workspace_evidence_id,
            now, True, False, True, True)
        assert gate.authorize(admission, now_s=now)['status'] == 'LEASE_GRANTED'
        with pytest.raises(ValueError, match='requires a bound qualified workspace'):
            LocalSupervisor(supervisor.scene, supervisor.task, limits, handoff=gate)
        wired = LocalSupervisor(supervisor.scene, supervisor.task, limits, handoff=gate, workspace_artifact=artifact_path)
        before = supervisor.sim.data.time
        result = wired.step(LocalProposal(supervisor.task.task_id, 1, 1, 'GRASPING', [0.]*5))
        assert result['status'] == 'EXECUTED_SIMULATION' and result['owner'] == 'RL'
        assert supervisor.sim.data.time > before
        after = supervisor.sim.data.time
        assert wired.step(LocalProposal(supervisor.task.task_id, 1, 1, 'GRASPING', [0.]*5))['category'] == 'PROPOSAL_REPLAY'
        assert supervisor.sim.data.time == after
        artifact_path.write_text(artifact_path.read_text()+'\n')
        result = wired.step(LocalProposal(supervisor.task.task_id, 1, 2, 'GRASPING', [0.]*5))
        assert result['category'] == 'WORKSPACE_EVIDENCE_CHANGED' and result['reconciliation_required']
        assert supervisor.sim.data.time == after
    finally:
        ledger.close()


def test_exception_after_partial_controller_step_marks_reconciliation(supervisor):
    authorize_test_session(supervisor)
    original = supervisor.scene.controller.step

    def broken(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('controller fixture failure after advancing physics')

    supervisor.scene.controller.step = broken
    before = supervisor.sim.data.time
    result = supervisor.qualification_step([0.]*5, phase='GRASPING')
    assert result['category'] == 'CONTROLLER_FAILURE' and result['motion_applied']
    assert result['reconciliation_required'] and supervisor.sim.data.time > before


def test_grasp_diagnostic_reads_real_mujoco_geometry_types(supervisor):
    import importlib.util
    path = Path(__file__).resolve().parents[1]/'examples/qualify_hybrid_approach/local_diagnostic.py'
    spec = importlib.util.spec_from_file_location('qualify_local_diagnostic', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    surface = .018  # Explicit synthetic test reference, not calibration.
    stem = module.grasp_geometry(supervisor.sim, 'white_pawn_e2', surface, 'stem')
    head = module.grasp_geometry(supervisor.sim, 'white_pawn_e2', surface, 'head')
    assert head['tcp_z_m']-stem['tcp_z_m'] == pytest.approx(.009)
    assert head['aperture_m']-stem['aperture_m'] == pytest.approx(.002)
    assert head['closing_target_m']-stem['closing_target_m'] == pytest.approx(.002)
    stronger = module.grasp_geometry(supervisor.sim, 'white_pawn_e2', surface, 'head', 1.5)
    assert stronger['closing_target_m'] < head['closing_target_m']
    load = stronger['model_load_estimate']
    assert load['estimated_normal_load_N'] == pytest.approx(1.5*load['weight_N']/(2*load['friction_lower_bound']))
    with pytest.raises(ValueError, match='at least one'):
        module.grasp_geometry(supervisor.sim, 'white_pawn_e2', surface, 'head', .5)


def test_contact_closure_is_not_confused_with_arm_tracking_failure(supervisor):
    sim = supervisor.sim
    target = supervisor.scene.command.copy()
    target[3:5] = -.005
    sim.data.qpos[sim.qadr[3:5]] = -.004
    sim.data.qvel[sim.vadr[3:5]] = 0.
    sim.data.actuator_force[3:5] = -.15
    supervisor.feedback.grip_contacts = Mock(return_value=True)
    assert supervisor._tracking_ok(target)
    supervisor.feedback.grip_contacts.return_value = False
    assert not supervisor._tracking_ok(target)
    supervisor.feedback.grip_contacts.return_value = True
    sim.data.qpos[sim.qadr[0]] += .1
    assert not supervisor._tracking_ok(target)


def test_contact_closure_requires_correct_direction_and_force_limit(supervisor):
    sim = supervisor.sim
    target = supervisor.scene.command.copy()
    target[3:5] = -.005
    sim.data.qpos[sim.qadr[3:5]] = -.004
    sim.data.qvel[sim.vadr[3:5]] = 0.
    supervisor.feedback.grip_contacts = Mock(return_value=True)
    sim.data.actuator_force[3:5] = 9.
    assert not supervisor._tracking_ok(target)
    sim.data.actuator_force[3:5] = -.15
    sim.data.qpos[sim.qadr[3:5]] = -.006
    assert not supervisor._tracking_ok(target)


def test_lift_without_bilateral_grip_stops_before_motion(supervisor):
    authorize_test_session(supervisor)
    before = supervisor.sim.data.time
    result = supervisor.qualification_step([0.]*5, phase='LIFTING')
    assert result['category'] == 'GRIP_LOST_DURING_LIFT'
    assert not result['motion_applied'] and supervisor.sim.data.time == before
