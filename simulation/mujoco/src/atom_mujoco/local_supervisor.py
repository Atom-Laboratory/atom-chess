"""Native local safety/execution adapter. No policy or chess rules live here."""
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .approach_planner import model_identity, physical_identity, plan_identity
from .autonomous_control import AutonomousControl, MotionChoice
from .hybrid_contract import LocalHandoff, LocalLimits, decode_local_action, vector
from .scene_feedback import SceneFeedback
from .supervision import MoveTask


class LocalSupervisor:
    def __init__(self, scene, task, limits, *, handoff=None, workspace_artifact=None,
                 observer=None, settle_timeout_s=2.):
        if not isinstance(task, MoveTask) or not isinstance(limits, LocalLimits):
            raise ValueError('Existing task and validated local limits required')
        task.validate()
        if (task.piece_id != scene.config['piece'] or task.source_square != scene.config['source']
                or task.target_square != scene.task_target):
            raise ValueError('Task differs from prepared physical/visual fixture')
        self.scene, self.sim, self.task, self.limits = scene, scene.sim, task, limits
        self.control = AutonomousControl(scene)
        if not self.scene.motion.has_wrist or len(self.sim.names) != 6:
            raise ValueError('Six-command wrist-aware model required')
        if (not np.array_equal(limits.command_lower, self.sim.lower)
                or not np.array_equal(limits.command_upper, self.sim.upper)
                or not np.isclose(limits.control_dt_s, self.sim.dt, rtol=0, atol=1e-12)
                or np.any(np.array(limits.rates) > self.control.rates)):
            raise ValueError('Declared limits/rates/interval exceed selected model contract')
        if not np.isfinite(settle_timeout_s) or settle_timeout_s <= 0:
            raise ValueError('Positive finite settling timeout required')
        self.model_id = model_identity(self.sim)
        if handoff is not None and (not isinstance(handoff, LocalHandoff)
                or handoff.limits != limits or handoff.model_identity != self.model_id
                or handoff.execution.task != task):
            raise ValueError('Lease/task/model/limits mismatch')
        self.handoff, self.observer = handoff, observer
        self.settle_timeout = settle_timeout_s
        self.expected_physical = physical_identity(self.sim)
        self.camera_id = scene.vision.camera_id
        self.reference = scene.vision.reference_sha256
        self.workspace_artifact = None
        if handoff is not None:
            if workspace_artifact is None:
                raise ValueError('RL requires a bound qualified workspace artifact')
            self.workspace_artifact = Path(workspace_artifact).resolve(strict=True)
            self._validate_workspace_artifact()
        self.sequence = -1
        self.last_frame = None
        self.camera_captures = self.camera_reuses = 0
        self.started = time.monotonic()
        self.last_time = self.started
        self.qualification = False
        self.failed = False
        self.decisions = 0
        self.max_decisions = 0
        self.board_homography = None
        self.feedback = SceneFeedback(self.sim)
        self.scene.contact_guard.reset()
        self.scene.contact_guard.start_displacement(self.sim.data)

    def _validate_workspace_artifact(self):
        path = self.workspace_artifact
        raw = path.read_bytes()
        artifact = json.loads(raw)
        expected_limits = {key: value for key, value in vars(self.limits).items()
                           if key != 'workspace_evidence_id'}
        if (hashlib.sha256(raw).hexdigest() != self.limits.workspace_evidence_id
                or artifact.get('schema') != 1
                or artifact.get('scope') != 'simulation_only_local_grasp_lift_with_per_action_sweeps'
                or artifact.get('qualified') is not True or artifact.get('training_eligible') is not True
                or artifact.get('model_identity') != self.model_id
                or artifact.get('task_id') != self.task.task_id
                or artifact.get('board_revision') != self.task.expected_board_revision
                or artifact.get('camera_id') != self.camera_id
                or artifact.get('reference_sha256') != self.reference
                or json.dumps(artifact.get('limits'), sort_keys=True) != json.dumps(expected_limits, sort_keys=True)
                or not isinstance(artifact.get('baseline_reports'), list) or not artifact['baseline_reports']):
            raise ValueError('Workspace artifact identity, scope or limits mismatch')
        for record in artifact['baseline_reports']:
            report_path = (path.parent/record['path']).resolve(strict=True)
            raw_report = report_path.read_bytes()
            report = json.loads(raw_report)
            if (hashlib.sha256(raw_report).hexdigest() != record['sha256']
                    or report.get('grasp_success') is not True or report.get('lift_success') is not True):
                raise ValueError('Qualified grasp/lift baseline evidence required')

    def begin_qualification(self, plan, report, *, max_decisions):
        """Explicit deterministic test lane; does not create an RL lease."""
        if type(max_decisions) is not int or max_decisions <= 0:
            raise ValueError('Positive qualification decision budget required')
        if self.handoff is not None or self.qualification or self.failed:
            raise ValueError('Separate unused deterministic qualification supervisor required')
        if (plan.get('status') != 'PLANNED' or plan.get('signature') != plan_identity(plan)
                or report.get('plan_signature') != plan['signature']
                or report.get('status') != 'COMPLETED_SIMULATED_APPROACH'
                or report.get('approach_complete') is not True or report.get('retreat_complete') is not False
                or report.get('final_physical_identity') != physical_identity(self.sim)
                or report.get('model_identity') != self.model_id or plan['model_identity'] != self.model_id
                or not np.array_equal(report.get('final_command'), self.scene.command)
                or plan['camera_id'] != self.camera_id or plan['reference_sha256'] != self.reference
                or plan['piece'] != self.task.piece_id or plan['source'] != self.task.source_square):
            raise ValueError('Current verified unretreated matching approach required')
        self.board_homography = np.asarray(plan['homography'], dtype=float).copy()
        self.qualification, self.max_decisions = True, max_decisions
        return dict(status='DETERMINISTIC_QUALIFICATION_ONLY', training_eligible=False,
                    local_manipulation_workspace_qualified=False, max_decisions=max_decisions)

    def _fault(self, category, detail=None):
        self.failed = True
        if self.handoff is not None:
            self.handoff.revoke(category)
            self.handoff.execution.fault(category)
        # No further physics tick: retain the issued reference at this boundary.
        self.sim.target = self.sim.reference.copy()
        self.sim.data.ctrl[:] = self.sim.reference
        self.expected_physical = physical_identity(self.sim)
        return dict(status='STOPPED', category=category, detail=detail,
                    reconciliation_required=True, motion_applied=False, training_eligible=False)

    def _preconditions(self, frame=None):
        if self.failed:
            return None, dict(status='REJECTED', category='RECONCILIATION_REQUIRED', motion_applied=False)
        now = time.monotonic()
        if (not np.isfinite(now) or now < self.last_time or now-self.started >= self.task.timeout_s):
            return None, self._fault('CLOCK_OR_TASK_TIMEOUT')
        self.last_time = now
        if model_identity(self.sim) != self.model_id:
            return None, self._fault('MODEL_CHANGED')
        if self.workspace_artifact is not None:
            try:
                self._validate_workspace_artifact()
            except (ValueError, KeyError, OSError, TypeError) as error:
                return None, self._fault('WORKSPACE_EVIDENCE_CHANGED', str(error))
        if physical_identity(self.sim) != self.expected_physical:
            return None, self._fault('EXTERNAL_SCENE_OR_CONTROLLER_CHANGE')
        try:
            self.limits.command(self.scene.command)
            reused = (frame is not None and 0 <= time.monotonic()-frame.captured_at_s
                      <= self.scene.config['max_perception_age_s'])
            if reused:
                self.camera_reuses += 1
            else:
                self.camera_captures += 1
                frame = self.scene.observe()
        except (ValueError, RuntimeError) as error:
            return None, self._fault('PERCEPTION_OR_COMMAND_FAILURE', str(error))
        if (not frame.oriented or frame.homography is None or frame.camera_id != self.camera_id
                or frame.reference_sha256 != self.reference
                or type(frame.sequence) is not int
                or (frame.sequence != self.sequence if reused else frame.sequence <= self.sequence)
                or not 0 <= time.monotonic()-frame.captured_at_s <= self.scene.config['max_perception_age_s']):
            return None, self._fault('FRESH_MATCHING_PERCEPTION_REQUIRED')
        homography = np.asarray(frame.homography)
        if homography.shape != (3, 3) or not np.isfinite(homography).all() or np.linalg.det(homography) == 0:
            return None, self._fault('INVALID_BOARD_REFERENCE')
        if self.board_homography is not None:
            height, width = frame.rectified_rgb.shape[:2]
            corners = np.array([[0., width, width, 0.], [0., 0., height, height], [1., 1., 1., 1.]])
            mapped = homography@np.linalg.inv(self.board_homography)@corners
            delta = (mapped[:2]/mapped[2]-corners[:2])*np.array([8*self.scene.pitch/width, 8*self.scene.pitch/height])[:, None]
            if not np.isfinite(delta).all() or np.linalg.norm(delta, axis=0).max() > self.control.checker.clearance:
                return None, self._fault('BOARD_REFERENCE_MOVED')
        else:
            self.board_homography = homography.copy()
        self.sequence = frame.sequence
        self.last_frame = frame
        if not self._tracking_ok(self.scene.command):
            return None, self._fault('START_NOT_TRACKING_ISSUED_COMMAND')
        return frame, None

    def _tracking_ok(self, command):
        sim = self.sim
        error = sim.data.qpos[sim.qadr]-command
        if not np.isfinite(error).all() or not np.isfinite(sim.data.qvel).all():
            return False
        tolerance = sim.speed*sim.model.opt.timestep
        if np.any(abs(error[[0, 1, 2, 5]]) > tolerance[[0, 1, 2, 5]]):
            return False
        if np.all(abs(error[3:5]) <= tolerance[3:5]):
            return True
        gains = sim.model.actuator_gainprm[3:5, 0]
        if (not self.feedback.grip_contacts(self.task.piece_id)
                or not np.all(sim.model.actuator_forcelimited[3:5]) or np.any(gains <= 0)):
            return False
        force_caps = np.max(abs(sim.model.actuator_forcerange[3:5]), axis=1)
        return bool(np.all(error[3:5] >= 0.) and np.all(error[3:5] <= force_caps/gains)
            and np.all(abs(sim.data.actuator_force[3:5]) <= force_caps+np.finfo(float).eps*force_caps)
            and np.all(abs(sim.data.qvel[sim.vadr[3:5]]) <= sim.speed[3:5]/self.scene.dwell))

    def _validate_decoded(self, decoded):
        if decoded['status'] != 'PROPOSED':
            return None, dict(decoded, motion_applied=False, transformation='none')
        endpoint = decoded['endpoint']
        choice = MotionChoice(tuple(endpoint[:3]), endpoint[3], endpoint[4],
                              self.control.commanded_elbow_down(self.scene.command), 1, self.sim.dt)
        end, validation = self.control.validate(choice, self.scene.command, project=False)
        if end is None:
            return None, dict(status='REJECTED', category=validation['status'], detail=validation,
                              motion_applied=False, transformation='none')
        return end, validation

    def _execute(self, end, validation, *, owner, phase):
        # A slow native/sweep check must not reuse a frame captured before it.
        frame, invalid = self._preconditions(self.last_frame)
        if invalid:
            return invalid
        if owner == 'RL' and (self.handoff.owner != 'RL'
                or self.handoff.execution.state != phase
                or time.monotonic()-self.handoff.execution.started >= self.task.timeout_s):
            return self._fault('OWNERSHIP_OR_TIMEOUT_CHANGED_DURING_VALIDATION')
        sim, guard = self.sim, self.scene.contact_guard
        guard.begin_step()
        failure = None
        start = float(sim.data.time)
        trace = []

        def stop():
            nonlocal failure
            now = time.monotonic()
            if now-self.started >= self.task.timeout_s:
                failure = dict(category='TASK_TIMEOUT_DURING_EXECUTION')
                return True
            if now-frame.captured_at_s > self.scene.config['max_perception_age_s']:
                failure = dict(category='PERCEPTION_EXPIRED_DURING_EXECUTION')
                return True
            if owner == 'RL' and (self.handoff.owner != 'RL' or self.handoff.execution.state != phase):
                failure = dict(category='OWNERSHIP_CHANGED_DURING_EXECUTION')
                return True
            if phase == 'LIFTING' and not self.feedback.grip_contacts(self.task.piece_id):
                failure = dict(category='GRIP_LOST_DURING_LIFT')
                return True
            guard.observe(sim.data)
            contact = self.control.unexpected_contact()
            excess = np.maximum(sim.lower-sim.data.qpos[sim.qadr], sim.data.qpos[sim.qadr]-sim.upper)
            if guard.topple_event:
                failure = dict(category='PIECE_TOPPLED', event=guard.topple_event)
            elif contact or guard.event:
                failure = dict(category='UNEXPECTED_CONTACT', contact=contact, neighbor=guard.event)
            elif max(guard.displacements_mm().values(), default=0.) > 1000*self.feedback.limits.bystander_position_m:
                failure = dict(category='BYSTANDER_DISPLACED', displacement_mm=guard.displacements_mm())
            elif np.any(excess > sim.speed*sim.model.opt.timestep):
                failure = dict(category='DYNAMIC_JOINT_LIMIT_EXCESS', excess=excess.tolist())
            return failure is not None

        if stop():
            return self._fault(failure['category'], failure)
        for index in range(1, 2+int(np.ceil(self.settle_timeout/sim.dt))):
            try:
                state = self.scene.controller.step(end, stop_when=stop)
            except (ValueError, RuntimeError) as error:
                result = self._fault('CONTROLLER_FAILURE', str(error))
                result['motion_applied'] = True
                return result
            self.scene.command = end.copy()
            trace.append(dict(time_s=float(sim.data.time), position=state['position'].tolist(),
                              command=end.tolist(), actuator_force=state['actuator_force'].tolist(),
                              tcp_m=sim.data.site('grasp_center').xpos.tolist()))
            if self.observer is not None:
                self.observer(phase, dict(owner=owner, interval=index, validation=validation['status']))
            if failure:
                result = self._fault(failure['category'], failure)
                result.update(motion_applied=True, trace=trace)
                return result
            if (self._tracking_ok(end)
                    and np.all(abs(state['velocity']) <= sim.speed/self.scene.dwell)):
                break
        else:
            result = self._fault('SETTLING_TIMEOUT')
            result.update(motion_applied=True, trace=trace)
            return result
        self.expected_physical = physical_identity(sim)
        return dict(status='EXECUTED_SIMULATION', category='LOCAL_ACTION_SETTLED', owner=owner,
                    phase=phase, validation=validation, trace=trace, motion_applied=True,
                    requested_duration_s=sim.dt, elapsed_sim_s=float(sim.data.time)-start,
                    settling_intervals=len(trace)-1, transformation='none', training_eligible=False,
                    camera_captures=self.camera_captures, camera_reuses=self.camera_reuses,
                    finger_tracking_error_m=(state['position'][3:5]-end[3:5]).tolist(),
                    settling_mode=('position' if np.all(abs(state['position'][3:5]-end[3:5])
                        <= sim.speed[3:5]*sim.model.opt.timestep) else 'bilateral_force_limited_finger_contact'),
                    simulation_diagnostics=dict(pad_contacts=self.feedback.pad_contacts(self.task.piece_id),
                        neighbor_displacement_mm=guard.displacements_mm(),
                        source='privileged safety/evaluation; excluded from actor'))

    def step(self, proposal):
        """Learned-policy entry point: only the existing admitted lease can act."""
        if self.handoff is None:
            return dict(status='REJECTED', category='RL_LEASE_REQUIRED', motion_applied=False)
        frame, failure = self._preconditions()
        if failure:
            return failure
        decoded = self.handoff.propose(proposal, command=self.scene.command,
            commanded_tcp_m=self.control.commanded_tcp(self.scene.command), camera_id=frame.camera_id,
            reference_sha256=frame.reference_sha256, now_s=time.monotonic())
        end, validation = self._validate_decoded(decoded)
        if end is None:
            return validation
        return self._execute(end, validation, owner='RL', phase=self.handoff.execution.state)

    def qualification_step(self, action, *, phase):
        """Deterministic, individually checked action; no qualification is implied."""
        if not self.qualification:
            return dict(status='REJECTED', category='QUALIFICATION_SESSION_REQUIRED', motion_applied=False)
        if phase not in ('GRASPING', 'LIFTING'):
            return dict(status='REJECTED', category='PHASE_NOT_AUTHORIZED', motion_applied=False)
        if self.decisions >= self.max_decisions:
            return self._fault('QUALIFICATION_BUDGET_EXHAUSTED')
        frame, failure = self._preconditions()
        if failure:
            return failure
        self.decisions += 1
        decoded = decode_local_action(action, self.scene.command,
                                     self.control.commanded_tcp(self.scene.command), self.limits)
        end, validation = self._validate_decoded(decoded)
        if end is None:
            return validation
        return self._execute(end, validation, owner='DETERMINISTIC_QUALIFICATION', phase=phase)

    def screen_target(self, xyz, opening, wrist):
        """Diagnostic whole-path screen only. A result cannot be used as a ticket."""
        frame, failure = self._preconditions()
        if failure:
            return failure
        try:
            endpoint = np.asarray(vector([*xyz, wrist, opening], 5, 'target'))
            if np.any(endpoint < self.limits.local_lower) or np.any(endpoint > self.limits.local_upper):
                raise ValueError('Diagnostic target outside local envelope')
            end = self.sim.validate(self.scene.motion.solve(xyz, opening, wrist=wrist,
                elbow_down=self.control.commanded_elbow_down(self.scene.command)))
        except (ValueError, TypeError) as error:
            return dict(status='REJECTED', category='IK_LIMIT_OR_ENVELOPE', detail=str(error), motion_applied=False)
        end, validation = self.control.sweep(end, 1.)
        return dict(status='PATH_SCREENED' if end is not None else 'REJECTED',
                    category=validation['status'], detail=validation, motion_applied=False,
                    execution_authorized=False, scope='diagnostic only; no timing approval')
