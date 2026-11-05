"""Conservative nominal swept-geometry checks, independent of contact masks."""
import itertools
import math

import mujoco
import numpy as np


class SweptChecker:
    def __init__(self, model, qpos, joint_ids, pairs, *, clearance_m=.001, max_depth=16):
        self.model = model
        self.data = mujoco.MjData(model)
        self.initial = np.array(qpos, copy=True)
        self.joints = np.asarray(joint_ids)
        self.addresses = model.jnt_qposadr[self.joints]
        self.pairs = tuple(pairs)
        self.clearance = clearance_m
        self.max_depth = max_depth
        self.samples = 0
        self.coefficients = np.zeros((model.ngeom, len(joint_ids)))
        for geom in range(model.ngeom):
            body = int(model.geom_bodyid[geom])
            chain = []
            while body:
                chain.append(body)
                body = int(model.body_parentid[body])
            radius = float(np.linalg.norm(model.geom_pos[geom])+model.geom_rbound[geom])
            radius += sum(float(np.linalg.norm(model.body_pos[b])) for b in chain)
            for joint in range(model.njnt):
                if model.jnt_bodyid[joint] in chain:
                    radius += 2*float(np.linalg.norm(model.jnt_pos[joint]))
                    if model.jnt_type[joint] == mujoco.mjtJoint.mjJNT_SLIDE:
                        radius += float(np.max(np.abs(model.jnt_range[joint])))
            for index, joint in enumerate(self.joints):
                if model.jnt_bodyid[joint] in chain:
                    self.coefficients[geom,index] = (1. if model.jnt_type[joint] == mujoco.mjtJoint.mjJNT_SLIDE
                                                     else 2*radius)

    def interval(self, start, end, *, allowed=(), configure=None, extra_coefficients=None):
        allowed = {frozenset(pair) for pair in allowed}
        pairs = [p for p in self.pairs if frozenset(p) not in allowed]
        coefficients = self.coefficients if extra_coefficients is None else extra_coefficients

        def check(a, b, depth):
            if self.samples >= 4096:
                return dict(status='unresolved', reason='preflight sample budget exceeded')
            self.data.qpos[:] = self.initial
            self.data.qpos[self.addresses] = (a+b)/2
            mujoco.mj_forward(self.model, self.data)
            if configure:
                configure(self.data)
                mujoco.mj_forward(self.model, self.data)
            self.samples += 1
            travel = coefficients @ (np.abs(b-a)/2)
            uncertain = None
            for first, second in pairs:
                limit = float(travel[first]+travel[second]+self.clearance)
                distance = float(mujoco.mj_geomDistance(self.model, self.data, first, second, limit+1e-6, None))
                if not math.isfinite(distance) or distance <= self.clearance:
                    return dict(status='collision', geoms=[self.model.geom(first).name, self.model.geom(second).name],
                                distance_m=distance, joint_position=((a+b)/2).tolist())
                if distance <= limit:
                    uncertain = (first, second)
            if uncertain is None:
                return None
            if depth >= self.max_depth:
                return dict(status='unresolved', geoms=[self.model.geom(g).name for g in uncertain],
                            joint_position=((a+b)/2).tolist())
            middle = (a+b)/2
            return check(a, middle, depth+1) or check(middle, b, depth+1)

        return check(np.asarray(start), np.asarray(end), 0)


class SceneCollision:
    def __init__(self, sim):
        self.sim = sim
        model = sim.model
        self.robot = []
        self.environment = []
        self.structural_exclusions = []
        for geom in range(model.ngeom):
            name = model.geom(geom).name or ''
            if ('_collision_' in name or name.startswith('finger_')
                    or name in ('gripper_hand1_visual', 'gripper_hand2_visual')):
                self.robot.append(geom)
            elif model.geom_contype[geom] and model.geom_bodyid[geom] not in {
                    model.geom_bodyid[g] for g in self.robot}:
                self.environment.append(geom)
        self.environment = [g for g in self.environment if g not in self.robot]
        self.pairs = []
        for a in self.robot:
            for b in self.environment:
                if model.body_weldid[model.geom_bodyid[a]] == model.body_weldid[model.geom_bodyid[b]]:
                    self.structural_exclusions.append([model.geom(a).name, model.geom(b).name])
                else:
                    self.pairs.append((a,b))
        for a,b in itertools.combinations(self.robot, 2):
            ba, bb = int(model.geom_bodyid[a]), int(model.geom_bodyid[b])
            wa, wb = int(model.body_weldid[ba]), int(model.body_weldid[bb])
            if (wa == wb or model.body_weldid[model.body_parentid[wa]] == wb
                    or model.body_weldid[model.body_parentid[wb]] == wa):
                self.structural_exclusions.append([model.geom(a).name, model.geom(b).name])
            else:
                self.pairs.append((a,b))

    def check_plan(self, solutions, identity, destination):
        sim, model = self.sim, self.sim.model
        body = model.body(identity).id
        selected = [g for g in self.environment if model.geom_bodyid[g] == body]
        others = [g for g in self.environment if model.geom_bodyid[g] != body]
        pairs = self.pairs + [(g,h) for g in selected for h in others]
        checker = SweptChecker(model, sim.data.qpos, sim.joint_ids, pairs)
        pads = [g for g in self.robot if model.geom(g).name.startswith(('finger_', 'gripper_hand'))]
        support = [g for g in others if model.geom(g).name == 'board_frame'
                   or model.geom(g).name.startswith('graveyard_support_')]
        # Selected piece resting support is allowed; support collision during transport is not.
        pad_pairs = [(a,b) for a in pads for b in selected]
        support_pairs = [(a,b) for a in support for b in selected]
        site = model.site('grasp_center').id
        scratch = mujoco.MjData(model)
        scratch.qpos[:] = sim.data.qpos
        scratch.qpos[sim.qadr] = solutions[1]
        mujoco.mj_forward(model, scratch)
        rotation = scratch.site_xmat[site].reshape(3,3)
        offset = rotation.T @ (sim.data.xpos[body]-scratch.site_xpos[site])
        relative_rotation = rotation.T @ sim.data.xmat[body].reshape(3,3)
        address = model.jnt_qposadr[model.body_jntadr[body]]
        held_coefficients = checker.coefficients.copy()
        for g in selected:
            # A carried piece inherits the arm chain plus its offset and radius.
            held_coefficients[g] = np.max(checker.coefficients[self.robot],axis=0)
            for j,joint in enumerate(sim.joint_ids):
                if model.jnt_type[joint] == mujoco.mjtJoint.mjJNT_HINGE:
                    held_coefficients[g,j] += 2*(np.linalg.norm(offset)+model.geom_rbound[g])
        def held(data):
            rot = data.site_xmat[site].reshape(3,3)
            data.qpos[address:address+3] = data.site_xpos[site]+rot@offset
            mujoco.mju_mat2Quat(data.qpos[address+3:address+7], (rot@relative_rotation).reshape(-1))
        def placed(data):
            data.qpos[address:address+3] = destination
        def q(index, opening):
            value = solutions[index].copy()
            value[3:] = opening
            return value
        opened, closed = sim.upper[3], sim.lower[3]
        phases = [('approach',q(0,opened),None,support_pairs),
                  ('descend',q(1,opened),None,support_pairs+pad_pairs),
                  ('close',q(1,closed),None,support_pairs+pad_pairs),
                  ('lift',q(2,closed),held,support_pairs+pad_pairs),
                  ('transport',q(3,closed),held,pad_pairs),
                  ('place',q(4,closed),held,support_pairs+pad_pairs),
                  ('open',q(4,opened),placed,support_pairs+pad_pairs),
                  ('retreat',q(3,opened),placed,support_pairs+pad_pairs)]
        start = sim.observe()['position']
        trajectory = []
        cursor = start
        for phase,end,_,_ in phases:
            trajectory.append(dict(phase=phase, start=cursor.tolist(), end=end.tolist()))
            cursor = end
        for phase,end,configure,allowed in phases:
            failure = checker.interval(start,end,allowed=allowed,configure=configure,
                                       extra_coefficients=held_coefficients if configure == held else None)
            if failure:
                return dict(valid=False, phase=phase, failure=failure, samples=checker.samples,
                            trajectory=trajectory, structural_exclusions=self.structural_exclusions)
            start = end
        return dict(valid=True, samples=checker.samples, trajectory=trajectory,
                    structural_exclusions=self.structural_exclusions,
                    scope='nominal joint-linear path with rigid held object; experimental convex geometry')

    def unexpected_contacts(self, identity, phase):
        """Inspect live contacts; selected pad/support contacts are phase-specific."""
        model, data = self.sim.model, self.sim.data
        selected_body = model.body(identity).id
        result = []
        for contact in data.contact:
            if contact.dist >= 0:
                continue
            a,b = int(contact.geom1), int(contact.geom2)
            names = [model.geom(g).name or '' for g in (a,b)]
            bodies = [int(model.geom_bodyid[g]) for g in (a,b)]
            robot = a in self.robot or b in self.robot
            selected = selected_body in bodies
            pad = any(n.startswith('finger_') for n in names)
            support = any(n == 'board_frame' or n.startswith('graveyard_support_') for n in names)
            if selected and pad and phase != 'APPROACHING':
                continue
            if selected and support and phase != 'TRANSPORTING':
                continue
            if robot or (selected and phase in ('LIFTING','TRANSPORTING')):
                if model.body_weldid[bodies[0]] == model.body_weldid[bodies[1]]:
                    continue
                result.append(dict(geoms=names, distance_m=float(contact.dist)))
        return result
