"""Headless manipulation playground using the existing MuJoCo physics backend."""
import time
import uuid

import mujoco
import numpy as np

from .backend import Simulation
from .recording import provenance, save_record
from .physical_state import PhysicalBoardState, Observation
from .scene_feedback import SceneFeedback
from .supervision import TaskLedger, Execution, Evidence
from .motion_controller import MotionController
from .task_plan import validate_plan
from .collision import SceneCollision


class Playground:
    def __init__(self, bundle, on_step=None, *, diagnostic_unchecked=False):
        self.sim = Simulation(bundle)
        self.history = []
        self.on_step = on_step
        self.diagnostic_unchecked = diagnostic_unchecked
        self.planned_trajectory = []
        self.feedback = SceneFeedback(self.sim)
        self.controller = MotionController(self.sim)
        self.ledger = TaskLedger(':memory:')
        self.physical = None
        self.observation_sequence = 0
        self.reset()

    def reset(self, seed=0):
        self.history = []
        state = self.sim.reset(seed=seed)
        for _ in range(60):
            state = self.sim.advance(self.sim.target)
        snapshot = self.feedback.snapshot(0)
        limits = self.feedback.limits
        self.physical = PhysicalBoardState(snapshot, position_tolerance_m=limits.bystander_position_m,
                                           angle_tolerance_rad=limits.bystander_angle_rad)
        return state

    def execute_request(self, request):
        """Consume the same schema produced by the C++ Chess Core adapter."""
        if isinstance(request, dict) and request.get('schema') == 2:
            reservations = validate_plan(request, self.physical.confirmed)
            results = []
            for transfer in request['transfers']:
                result = self.execute(operation='TRANSFER', **transfer)
                results.append(result)
                if result['status'] != 'COMPLETED_SIMULATION_ORACLE':
                    break
            completed = sum(r['status'] == 'COMPLETED_SIMULATION_ORACLE' for r in results)
            return dict(schema=2, status='COMPLETED_SIMULATION_ORACLE' if completed == len(reservations) else 'FAILED',
                        completed_transfers=completed, results=results,
                        error_code=results[-1]['error_code'], physical_revision=self.physical.confirmed.revision,
                        reconciliation_required=self.physical.reconciliation_required)
        if (not isinstance(request, dict) or set(request) != {'schema', 'operation', 'source', 'target'}
                or type(request['schema']) is not int or request['schema'] != 1
                or request['operation'] != 'MOVE'
                or not all(isinstance(request[k], str) for k in ('source', 'target'))):
            raise ValueError('Unsupported movement envelope')
        return self.execute(operation='MOVE', source=request['source'], target=request['target'])

    def solve(self, point, initial=None):
        """Damped numerical IK on a separate MjData; never mutate live physics."""
        sim = self.sim
        site = mujoco.mj_name2id(sim.model, mujoco.mjtObj.mjOBJ_SITE, 'grasp_center')
        if site < 0:
            raise ValueError('The bundle has no grasp_center site')
        data = mujoco.MjData(sim.model)
        best = None
        starts = [sim.observe()['position'] if initial is None else initial]
        starts += [np.array([a, .08, b, 0, 0]) for a in (-1., 0., 1.) for b in (-1., 1., 3.)]
        for start in starts:
            q = np.clip(np.array(start, copy=True), sim.lower, sim.upper)
            for _ in range(120):
                data.qpos[:] = sim.data.qpos
                data.qpos[sim.qadr] = q
                mujoco.mj_forward(sim.model, data)
                error = np.asarray(point)-data.site_xpos[site]
                distance = float(np.linalg.norm(error))
                if best is None or distance < best[0]:
                    best = (distance, q.copy())
                if distance < .001:
                    return q
                jac = np.zeros((3, sim.model.nv))
                mujoco.mj_jacSite(sim.model, data, jac, None, site)
                j = jac[:, sim.vadr[:3]]
                delta = j.T@np.linalg.solve(j@j.T+.0001*np.eye(3), error)
                q[:3] = np.clip(q[:3]+np.clip(delta, -.08, .08), sim.lower[:3], sim.upper[:3])
        raise ValueError(f'Unreachable grasp point: best residual {best[0]:.4f} m')

    def execute(self, *, operation, source, target, piece_id=None, controller='baseline', seed=0):
        started = time.perf_counter()
        sim = self.sim
        self.history = []
        self.planned_trajectory = []
        execution = task = None
        result = dict(schema=1, task_id=uuid.uuid4().hex, operation=operation,
                      piece_id=piece_id, source=source.lower(), target=target.lower(),
                      controller=controller, checkpoint=None, seed=seed, status='FAILED',
                      grasp_confirmed=False, release_confirmed=False, visual_confirmed=False,
                      verification_source='simulation_oracle', error_code=None,
                      collision_checked=False, training_eligible=False,
                      reward=None, provenance=provenance(), manifest=sim.manifest)
        try:
            if controller != 'baseline':
                raise ValueError('RL_POLICY_UNAVAILABLE: no trained validated checkpoint')
            if operation not in ('MOVE', 'TRANSFER'):
                raise ValueError('UNSUPPORTED_OPERATION')
            if source.lower() == target.lower():
                raise ValueError('INVALID_DESTINATION')
            if sim.manifest['pieces_physics'] != 'free-rigid-bodies':
                raise ValueError('DYNAMIC_PIECES_REQUIRED')
            request_transfer = self.physical.request_move if operation == 'MOVE' else self.physical.request_transfer
            task = request_transfer(source.lower(), target.lower(), operation_id=result['task_id'],
                                             expected_revision=self.physical.confirmed.revision, timeout_s=120.)
            if piece_id is not None and piece_id != task.piece_id:
                raise ValueError('SOURCE_IDENTITY_MISMATCH')
            piece_id = result['piece_id'] = task.piece_id
            piece = next(p for p in sim.manifest['pieces'] if p['name'] == piece_id)
            self.physical.start(task.task_id)
            execution = Execution(task, self.ledger, now_s=float(sim.data.time), max_age_s=.1, allow_oracle=True)
            def gate(signals):
                before = execution.state
                role, _ = execution.GATES[before]
                execution.advance(Evidence('simulation_oracle:'+role, float(sim.data.time),
                                          len(self.history)+list(execution.GATES).index(before),
                                          frozenset(signals), task.expected_board_revision), now_s=float(sim.data.time))
                if execution.state == before or execution.state in ('FAILED', 'ABORTED'):
                    raise ValueError('SUPERVISION_GATE_FAILED: '+before)
            observed = self.feedback.snapshot(self.physical.confirmed.revision)
            if observed.occupancy != self.physical.confirmed.occupancy:
                raise ValueError('PHYSICAL_STATE_CHANGED: reconciliation required')
            gate({'preconditions_valid'})
            body = sim.model.body(piece_id).id
            source_position = self.feedback.endpoint_position(source.lower())
            origin = sim.data.xpos[body].copy()
            if np.linalg.norm(origin[:2]-source_position[:2]) > .015:
                raise ValueError('SOURCE_MISMATCH')
            destination = self.feedback.endpoint_position(target.lower())
            for other in sim.manifest['pieces']:
                if other['name'] != piece_id:
                    pos = sim.data.xpos[sim.model.body(other['name']).id]
                    if np.linalg.norm(pos[:2]-destination[:2]) < .02:
                        raise ValueError('DESTINATION_OCCUPIED')
            # Experimental waypoint for gripping the simulated pawn stem.
            stem = sim.model.geom(piece_id+'_stem').id
            grip = origin+np.array([0, 0, sim.model.geom_pos[stem, 2]-sim.model.geom_size[stem, 1]/4])
            support_delta = destination[2]-source_position[2]
            # Board sites are 3 mm above its physical support; Graveyard sites are on support.
            support_delta += (.003 if not source.startswith('graveyard:') else 0)
            support_delta -= (.003 if not target.startswith('graveyard:') else 0)
            place = np.array([destination[0], destination[1], grip[2]+support_delta])
            waypoints = [('source approach', grip+[0,0,.07]), ('grasp', grip),
                         ('lift', grip+[0,0,.07]), ('destination approach', place+[0,0,.07]),
                         ('placement', place)]
            solutions = []
            for waypoint, point in waypoints:
                try:
                    solutions.append(self.solve(point, solutions[-1] if solutions else None))
                except ValueError as error:
                    result['failed_waypoint'] = waypoint
                    square = source.upper() if len(solutions) < 3 else target.upper()
                    raise ValueError(f'{error} ({waypoint} at {square}). Check board placement against the arm workspace.') from error
            if not self.diagnostic_unchecked:
                collision = SceneCollision(sim)
                result['collision_report'] = collision.check_plan(
                    solutions, piece_id, np.array([destination[0], destination[1], origin[2]+support_delta]))
                result['collision_checked'] = True
                self.planned_trajectory = result['collision_report']['trajectory']
                if not result['collision_report']['valid']:
                    raise ValueError('COLLISION_PREFLIGHT_FAILED: '+str(result['collision_report']['failure']))
            gate({'plan_valid'})
            def move(q, phase, opening, steps=180):
                goal = q.copy()
                goal[3:] = opening
                settled = False
                for step in range(max(steps, 600)):
                    state = self.controller.step(goal)
                    if not self.diagnostic_unchecked:
                        unexpected = collision.unexpected_contacts(piece_id, phase)
                        if unexpected:
                            result['runtime_collision'] = unexpected
                            raise ValueError('UNEXPECTED_RUNTIME_CONTACT')
                    if phase in ('LIFTING', 'TRANSPORTING') and not self.feedback.grip_contacts(piece_id):
                        raise ValueError('GRIP_LOST_DURING_'+phase)
                    self.history.append(dict(phase=phase, time_s=state['time_s'],
                                             position=state['position'].tolist(),
                                             target=goal.tolist(), piece_position=sim.data.xpos[body].tolist()))
                    if self.on_step:
                        self.on_step(phase, state)
                    settled = (np.max(np.abs(state['position'][:3]-goal[:3])) <= .005
                               and np.max(np.abs(state['velocity'][:3])) <= .01)
                    if step+1 >= steps and settled:
                        break
                if not settled:
                    raise ValueError('ROBOT_NOT_SETTLED: '+phase)
                return state
            move(solutions[0], 'APPROACHING', sim.upper[3])
            gate({'approach_settled'})
            move(solutions[1], 'GRASPING', sim.upper[3])
            move(solutions[1], 'VERIFYING_GRASP', sim.lower[3], 100)
            gate({'close_acknowledged'})
            result['grasp_confirmed'] = self.feedback.grip_contacts(piece_id)
            if not result['grasp_confirmed'] or not self.feedback.settled(piece_id):
                raise ValueError('GRASP_FAILED')
            gate({'contact', 'piece_stable'})
            move(solutions[2], 'LIFTING', sim.lower[3])
            if sim.data.xpos[body,2] < origin[2]+.04 or not self.feedback.grip_contacts(piece_id):
                raise ValueError('LIFT_FAILED')
            gate({'lift_confirmed', 'grip_stable'})
            move(solutions[3], 'TRANSPORTING', sim.lower[3])
            if not self.feedback.grip_contacts(piece_id):
                raise ValueError('TRANSPORT_GRIP_LOST')
            gate({'destination_reached', 'grip_stable'})
            move(solutions[4], 'PLACING', sim.lower[3])
            gate({'placement_settled'})
            if (np.linalg.norm(sim.data.xpos[body,:2]-destination[:2]) > .012
                    or abs(sim.data.xpos[body,2]-origin[2]-support_delta) > .004):
                raise ValueError('PLACEMENT_NOT_SUPPORTED_OR_ALIGNED')
            gate({'supported', 'aligned'})
            move(solutions[4], 'RELEASING', sim.upper[3], 100)
            gate({'open_acknowledged'})
            move(solutions[3], 'VERIFYING_RELEASE', sim.upper[3])
            final = sim.data.xpos[body].copy()
            result['position_error_m'] = float(np.linalg.norm(final[:2]-destination[:2]))
            result['release_confirmed'] = self.feedback.released(piece_id)
            if result['position_error_m'] > .015 or abs(final[2]-origin[2]-support_delta) > .01 or not result['release_confirmed']:
                raise ValueError('PLACEMENT_FAILED')
            snapshot = self.feedback.snapshot(task.expected_board_revision)
            self.physical.verify_candidate(task.task_id, snapshot)
            gate({'released', 'whole_board_matches'})
            self.observation_sequence += 1
            telemetry = self.feedback.observation(task.task_id, task.expected_board_revision)
            self.physical.observe(Observation(task.task_id, telemetry.sequence,
                                               telemetry.timestamp_s, telemetry.snapshot))
            result['feedback'] = dict(operation_id=telemetry.operation_id, sequence=telemetry.sequence,
                                      timestamp_s=telemetry.timestamp_s,
                                      frames={name: dict(position_m=pose.position, orientation_wxyz=pose.orientation)
                                              for name,pose in telemetry.frames.items()},
                                      joints=dict(telemetry.joints), gripper=dict(telemetry.gripper))
            self.physical.commit(task.task_id, execution, now_s=float(sim.data.time))
            result['status'] = 'COMPLETED_SIMULATION_ORACLE'
            result['training_eligible'] = False  # Qualification suite and calibrated coverage still required.
        except (ValueError, RuntimeError, KeyError) as error:
            result['error_code'] = str(error)
            if execution is not None:
                execution.fault(str(error))
            if task is not None and self.physical.operations[task.task_id].status in ('pending', 'executing'):
                self.physical.fail(task.task_id, str(error))
        result['physical_revision'] = self.physical.confirmed.revision
        result['reconciliation_required'] = self.physical.reconciliation_required
        result.update(wall_time_s=time.perf_counter()-started, history=self.history)
        return result

    @staticmethod
    def save(path, result):
        save_record(path, result)
