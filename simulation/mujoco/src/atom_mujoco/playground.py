"""Headless manipulation playground using the existing MuJoCo physics backend."""
import time
import uuid

import mujoco
import numpy as np

from .backend import Simulation
from .recording import provenance, save_record


class Playground:
    def __init__(self, bundle, on_step=None):
        self.sim = Simulation(bundle)
        self.history = []
        self.on_step = on_step

    def reset(self, seed=0):
        self.history = []
        return self.sim.reset(seed=seed)

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

    def execute(self, *, operation, piece_id, source, target, controller='baseline', seed=0):
        started = time.perf_counter()
        sim = self.sim
        result = dict(schema=1, task_id=uuid.uuid4().hex, operation=operation,
                      piece_id=piece_id, source=source.lower(), target=target.lower(),
                      controller=controller, checkpoint=None, seed=seed, status='FAILED',
                      grasp_confirmed=False, release_confirmed=False, visual_confirmed=False,
                      verification_source='simulation_oracle', error_code=None,
                      reward=None, provenance=provenance(), manifest=sim.manifest)
        try:
            if controller != 'baseline':
                raise ValueError('RL_POLICY_UNAVAILABLE: no trained validated checkpoint')
            if operation != 'MOVE':
                raise ValueError('UNSUPPORTED_OPERATION')
            if source.lower() == target.lower():
                raise ValueError('INVALID_DESTINATION')
            piece = next((p for p in sim.manifest['pieces'] if p['name'] == piece_id), None)
            if piece is None:
                raise ValueError('UNKNOWN_PIECE')
            if sim.manifest['pieces_physics'] != 'free-rigid-bodies':
                raise ValueError('DYNAMIC_PIECES_REQUIRED')
            self.reset(seed)
            for _ in range(60):
                sim.advance(sim.target)
            body = sim.model.body(piece_id).id
            source_site = sim.model.site('square_center_'+source.lower()).id
            target_site = sim.model.site('square_center_'+target.lower()).id
            origin = sim.data.xpos[body].copy()
            if np.linalg.norm(origin[:2]-sim.data.site_xpos[source_site, :2]) > .015:
                raise ValueError('SOURCE_MISMATCH')
            destination = sim.data.site_xpos[target_site].copy()
            for other in sim.manifest['pieces']:
                if other['name'] != piece_id:
                    pos = sim.data.xpos[sim.model.body(other['name']).id]
                    if np.linalg.norm(pos[:2]-destination[:2]) < .02:
                        raise ValueError('DESTINATION_OCCUPIED')
            # Experimental waypoint for gripping the simulated pawn stem.
            if piece['kind'] != 'pawn':
                raise ValueError('PIECE_GEOMETRY_NOT_VALIDATED: baseline currently supports pawns')
            grip = origin+np.array([0, 0, .018])
            place = np.array([destination[0], destination[1], grip[2]])
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
            def move(q, phase, opening, steps=180):
                goal = q.copy()
                goal[3:] = opening
                for _ in range(steps):
                    state = sim.advance(goal)
                    self.history.append(dict(phase=phase, time_s=state['time_s'],
                                             position=state['position'].tolist(),
                                             target=goal.tolist(), piece_position=sim.data.xpos[body].tolist()))
                    if self.on_step:
                        self.on_step(phase, state)
                return state
            move(solutions[0], 'APPROACHING', sim.upper[3])
            move(solutions[1], 'GRASPING', sim.upper[3])
            move(solutions[1], 'VERIFYING_GRASP', sim.lower[3], 100)
            contacts = sim.contact_report()
            result['grasp_confirmed'] = all(any(f'finger_{i}_pad' in str(c) and piece_id in str(c) for c in contacts) for i in (1,2))
            if not result['grasp_confirmed']:
                raise ValueError('GRASP_FAILED')
            move(solutions[2], 'LIFTING', sim.lower[3])
            if sim.data.xpos[body,2] < origin[2]+.04:
                raise ValueError('LIFT_FAILED')
            move(solutions[3], 'TRANSPORTING', sim.lower[3])
            move(solutions[4], 'PLACING', sim.lower[3])
            move(solutions[4], 'RELEASING', sim.upper[3], 100)
            move(solutions[3], 'VERIFYING_RELEASE', sim.upper[3])
            final = sim.data.xpos[body].copy()
            result['position_error_m'] = float(np.linalg.norm(final[:2]-destination[:2]))
            result['release_confirmed'] = not any('finger_' in str(c) and piece_id in str(c) for c in sim.contact_report())
            if result['position_error_m'] > .015 or abs(final[2]-origin[2]) > .01 or not result['release_confirmed']:
                raise ValueError('PLACEMENT_FAILED')
            result['status'] = 'COMPLETED_SIMULATION_ORACLE'
        except (ValueError, RuntimeError, KeyError) as error:
            result['error_code'] = str(error)
        result.update(wall_time_s=time.perf_counter()-started, history=self.history)
        return result

    @staticmethod
    def save(path, result):
        save_record(path, result)
