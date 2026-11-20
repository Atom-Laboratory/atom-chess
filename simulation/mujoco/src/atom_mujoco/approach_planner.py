"""Model-scoped native approach proposals with complete swept validation."""
import hashlib
import itertools
import json
import time

import mujoco
import numpy as np

from .board_piece_localization import configuration_from_offsets, square_offsets
from .collision import SweptChecker
from .native_motion import commanded_elbow_down


def geometry_bounds(model, data, indices):
    """World AABBs of the compiled collision geometry, including mesh rotation."""
    indices = np.asarray(indices, dtype=int)
    rotation = data.geom_xmat[indices].reshape(-1, 3, 3)
    bounds = model.geom_aabb[indices]
    center = data.geom_xpos[indices]+np.einsum('ijk,ik->ij', rotation, bounds[:, :3])
    extent = np.einsum('ijk,ik->ij', abs(rotation), bounds[:, 3:])
    return center-extent, center+extent


def model_identity(sim):
    digest = hashlib.sha256(sim.manifest['model_sha256'].encode())
    digest.update(np.asarray([sim.model.opt.timestep, sim.dt], dtype=float).tobytes())
    digest.update(sim.model.opt.gravity.tobytes())
    for array in (sim.model.geom_pos, sim.model.geom_quat, sim.model.geom_size,
                  sim.model.body_pos, sim.model.body_quat, sim.model.jnt_range,
                  sim.model.jnt_pos, sim.model.jnt_axis, sim.model.geom_aabb,
                  sim.model.geom_contype, sim.model.geom_conaffinity,
                  sim.model.actuator_gainprm, sim.model.actuator_biasprm,
                  sim.model.actuator_ctrlrange, sim.model.actuator_forcerange,
                  sim.model.dof_damping, sim.model.dof_armature,
                  sim.model.body_mass, sim.model.body_inertia,
                  sim.model.geom_friction, sim.model.geom_solref, sim.model.geom_solimp,
                  sim.model.geom_margin, sim.model.geom_gap, sim.lower, sim.upper, sim.speed):
        digest.update(array.tobytes())
    return digest.hexdigest()


def physical_identity(sim):
    digest = hashlib.sha256()
    for array in (sim.data.qpos, sim.data.qvel, sim.data.act, sim.data.ctrl,
                  sim.data.qacc_warmstart, sim.reference, sim.target):
        digest.update(array.tobytes())
    return digest.hexdigest()


def plan_identity(plan):
    fields = {key: value for key, value in plan.items() if key != 'signature'}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, allow_nan=False).encode()).hexdigest()


class ApproachPlanner:
    def __init__(self, scene):
        self.scene = scene
        self.sim = sim = scene.sim
        self.scratch = mujoco.MjData(sim.model)
        self.checker = SweptChecker(sim.model, sim.model.qpos0, sim.joint_ids, scene.collision.pairs)
        self.region_checker = SweptChecker(sim.model, sim.model.qpos0, sim.joint_ids,
                                           scene.collision.pairs, max_depth=0)
        self.tool = [geom for geom in scene.collision.robot if 'gripper' in sim.model.geom(geom).name
                     or sim.model.geom(geom).name.startswith('finger_')]
        if not self.tool:
            raise ValueError('No tool collision geometry for approach planning')

    def tool_position(self, command):
        self.scratch.qpos[:] = self.sim.model.qpos0
        self.scratch.qpos[self.sim.qadr] = command
        mujoco.mj_kinematics(self.sim.model, self.scratch)
        return self.scratch.site('grasp_center').xpos.copy()

    def _scene(self, frame, command):
        scene = self.scene
        if (not frame.oriented or frame.homography is None
                or not 0 <= time.monotonic()-frame.captured_at_s <= scene.config['max_perception_age_s']):
            raise ValueError('FRESH_BOARD_REFERENCE_REQUIRED')
        offsets = square_offsets(scene.empty_reference, scene.centered_reference, frame,
                                 scene.occupied, scene.pitch)
        configuration = configuration_from_offsets(self.sim.model, self.sim.manifest['pieces'],
                                                   self.sim.qadr, command, offsets, scene.occupied)
        return configuration, offsets

    def _edge(self, start, end, phase):
        self.checker.samples = 0
        failure = self.checker.interval(start, end, prune_spheres=True)
        return dict(phase=phase, start=start.tolist(), end=end.tolist(),
                    valid=failure is None, samples=self.checker.samples, failure=failure)

    def _region(self, command):
        # A depth-zero certificate covers the complete independent joint box,
        # not just a collection of sampled corner poses.
        for factor in (1., .5, .25, .125, .0625, .03125, .015625, .0078125):
            half = self.sim.speed*self.sim.dt*factor
            lower = np.maximum(self.sim.lower, command-half)
            upper = np.minimum(self.sim.upper, command+half)
            self.region_checker.samples = 0
            failure = self.region_checker.interval(lower, upper, prune_spheres=True)
            if failure is None:
                return dict(lower=lower.tolist(), upper=upper.tolist(), control_interval_scale=factor,
                            certificate='single conservative joint-box certificate',
                            scope='initial collision-free neighborhood; contact workspace not qualified')
        return None

    def plan(self, *, max_candidates=48, require_visible_target=False, entry_offsets_squares=None):
        if type(max_candidates) is not int or max_candidates <= 0:
            raise ValueError('Positive integer candidate budget required')
        entry_offsets = np.asarray([[0., 0.]] if entry_offsets_squares is None else entry_offsets_squares,
                                   dtype=float)
        if (entry_offsets.ndim != 2 or entry_offsets.shape[1] != 2
                or not 1 <= len(entry_offsets) <= 9 or not np.isfinite(entry_offsets).all()):
            raise ValueError('Use one to nine finite XY entry offsets in board squares')
        scene, sim, model = self.scene, self.sim, self.sim.model
        command = sim.validate(scene.command).copy()
        frame = scene.observe()
        observed, offsets = self._scene(frame, command)
        self.checker.initial[:] = observed
        self.region_checker.initial[:] = observed
        self.scratch.qpos[:] = observed
        mujoco.mj_kinematics(model, self.scratch)
        start_position = self.scratch.site('grasp_center').xpos.copy()
        lower, _ = geometry_bounds(model, self.scratch, self.tool)
        drop = float(start_position[2]-lower[:, 2].min())
        bounded = [g for g in scene.collision.environment if model.geom_type[g]
                   not in (mujoco.mjtGeom.mjGEOM_PLANE, mujoco.mjtGeom.mjGEOM_HFIELD)]
        _, top = geometry_bounds(model, self.scratch, bounded)
        highest = float(top[:, 2].max())
        selected = [g for g in bounded if model.geom_bodyid[g] == model.body(scene.config['piece']).id]
        _, selected_top = geometry_bounds(model, self.scratch, selected)
        minimum = float(selected_top[:, 2].max()+drop+self.checker.clearance+sim.speed[1]*sim.dt)
        zero = command.copy()
        zero[1] = 0.
        maximum = float(self.tool_position(zero)[2]+sim.upper[1])
        heights = sorted(set(np.r_[np.arange(minimum, maximum, scene.pitch),
                                   highest+drop+self.checker.clearance+sim.speed[1]*sim.dt]))
        heights = [height for height in heights if height <= maximum]
        wrists = list(dict.fromkeys([float(command[-1]), *np.linspace(sim.lower[-1], sim.upper[-1], 5)]))
        source = scene.square_source[:2]+offsets[scene.config['source']]
        preview_reference = None
        if require_visible_target:
            # Match two renders of the same RGB-estimated scene. The original
            # centered template can differ after quantized pose re-rendering.
            self.scratch.qpos[:] = observed
            mujoco.mj_forward(model, self.scratch)
            preview_reference = scene.observe(self.scratch)
        result = dict(schema=1, status='REJECTED', piece=scene.config['piece'], source=scene.config['source'],
                      model_identity=model_identity(sim), initial_physical_identity=physical_identity(sim),
                      model_sha256=sim.manifest['model_sha256'], joint_names=sim.names,
                      initial_command=command.tolist(), initial_measured=sim.data.qpos[sim.qadr].tolist(),
                      source_xy_m=source.tolist(), offsets_m=offsets,
                      frame_sequence=frame.sequence, camera_id=frame.camera_id,
                      reference_sha256=frame.reference_sha256, homography=frame.homography.tolist(),
                      derived_geometry=dict(tool_drop_m=drop, highest_obstacle_m=highest,
                          minimum_candidate_tcp_z_m=minimum, maximum_tcp_z_m=maximum,
                          height_step_m=scene.pitch, clearance_m=self.checker.clearance),
                      candidates=[], require_visible_target=require_visible_target,
                      entry_offsets_squares=entry_offsets.tolist(),
                      preview_reference='estimated_scene_at_issued_command' if require_visible_target else None,
                      scope='native six-command simulation approach qualification',
                      local_manipulation_workspace_qualified=False, training_eligible=False)
        initial_check = self._edge(command, command, 'INITIAL_CONFIGURATION')
        if not initial_check['valid']:
            result.update(reason='INITIAL_COLLISION_OR_UNRESOLVED', initial_check=initial_check)
            return result
        for height, entry_offset, wrist, elbow in itertools.product(heights, entry_offsets, wrists, (True, False)):
            candidate = dict(id=len(result['candidates']), tcp_z_m=height,
                             wrist_rad=wrist, elbow_down=elbow,
                             entry_offset_squares=entry_offset.tolist())
            result['candidates'].append(candidate)
            try:
                # Reuse the C++ MotionPlanner's high-clearance source
                # and destination rows, without running its grasp phases.
                poses = scene.motion.plan(start_position, source+entry_offset*scene.pitch, height,
                                          height-scene.pitch)
                target = sim.validate(scene.motion.solve(poses[4, :3], 0., wrist=wrist,
                                                         elbow_down=elbow))
                paths = [('DIRECT', [target])]
            except ValueError as error:
                candidate.update(status='IK_OR_LIMIT_REJECTED', reason=str(error))
                if len(result['candidates']) >= max_candidates:
                    result['reason'] = 'CANDIDATE_BUDGET_EXHAUSTED'
                    return result
                continue
            if require_visible_target:
                self.scratch.qpos[:] = observed
                self.scratch.qpos[sim.qadr] = target
                mujoco.mj_forward(model, self.scratch)
                preview = scene.observe(self.scratch)
                estimate = square_offsets(scene.empty_reference, preview_reference,
                                          preview, [scene.config['source']], scene.pitch)
                offset = estimate.get(scene.config['source'])
                shift = None if offset is None else float(np.linalg.norm(offset))
                candidate['visual_preview'] = dict(oriented=preview.oriented, shift_m=shift)
                if shift is None or shift > self.checker.clearance:
                    candidate['status'] = 'VISUAL_TARGET_REJECTED'
                    if len(result['candidates']) >= max_candidates:
                        result['reason'] = 'CANDIDATE_BUDGET_EXHAUSTED'
                        return result
                    continue
            endpoint = self._edge(target, target, 'APPROACH_ENDPOINT')
            candidate['endpoint'] = endpoint
            if not endpoint['valid']:
                candidate['status'] = 'ENDPOINT_REJECTED'
                if len(result['candidates']) >= max_candidates:
                    result['reason'] = 'CANDIDATE_BUDGET_EXHAUSTED'
                    return result
                continue
            try:
                staging = sim.validate(scene.motion.solve(poses[0, :3], 0., wrist=command[-1],
                    elbow_down=commanded_elbow_down(sim, command, self.scratch)))
                paths.append(('STAGED', [staging, target]))
            except ValueError as error:
                candidate['staging_rejection'] = str(error)
            candidate['paths'] = []
            for route, points in paths:
                cursor, edges = command, []
                for index, end in enumerate(points):
                    edge = self._edge(cursor, end, f'{route}_{index}')
                    edges.append(edge)
                    if not edge['valid']:
                        break
                    cursor = end
                candidate['paths'].append(dict(route=route, edges=edges))
                if not all(edge['valid'] for edge in edges):
                    continue
                region = self._region(target)
                if region is None:
                    candidate['status'] = 'REGION_NOT_CERTIFIED'
                    continue
                retreat = []
                for edge in reversed(edges):
                    reverse = self._edge(np.array(edge['end']), np.array(edge['start']), 'RETREAT')
                    retreat.append(reverse)
                    if not reverse['valid']:
                        break
                if not all(edge['valid'] for edge in retreat):
                    candidate['status'] = 'RETREAT_REJECTED'
                    continue
                candidate['status'] = 'PLANNED'
                result.update(status='PLANNED', selected_candidate=candidate['id'], route=route,
                              approach=edges, retreat=retreat, entry_region=region,
                              target_command=target.tolist(), target_tcp_m=self.tool_position(target).tolist())
                result['signature'] = plan_identity(result)
                return result
            candidate.setdefault('status', 'SWEEP_REJECTED')
            if len(result['candidates']) >= max_candidates:
                result['reason'] = 'CANDIDATE_BUDGET_EXHAUSTED'
                return result
        result['reason'] = 'NO_VALID_CANDIDATE_IN_BOUNDED_FAMILY'
        return result
