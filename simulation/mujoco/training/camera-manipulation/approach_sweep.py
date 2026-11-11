"""Offline P038 pickup feasibility. Simulator state is evaluator data only."""
import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from itertools import product
import json
import math
from pathlib import Path
import subprocess

import mujoco
import numpy as np
from PIL import Image

from atom_mujoco.camera_only_env import CameraOnlyEnv
from atom_mujoco.collision import SweptChecker
from atom_mujoco.scene_feedback import SceneFeedback
from atom_mujoco.board_piece_localization import configuration_from_offsets
from run import provenance, sha


@dataclass(frozen=True)
class Strategy:
    wrist_deg: float
    entry_xy_m: tuple
    grasp_xy_m: tuple
    entry_height_m: float
    aperture_delta_m: float


def strategies(env):
    dx, dy, dz, opening = env.residual_bounds
    center = (0., 0.)
    # Use the existing arm travel and calibrated residual increments as grid units.
    angles = np.unique(np.r_[np.degrees(env.motion.default_wrist),
                             np.linspace(*np.degrees([env.sim.lower[-1], env.sim.upper[-1]]), 25)])
    entries = [center, (4*dx, 0.), (-4*dx, 0.), (0., 4*dy), (0., -4*dy)]
    grips = [center, (dx, 0.), (-dx, 0.), (0., dy), (0., -dy)]
    # First isolate wrist, then alter the individual families and their combinations.
    shapes = sorted(product(entries, grips, (0., dz), (0., -opening)),
                    key=lambda row: sum(value != zero for value, zero in zip(row, (center, center, 0., 0.))))
    for (entry, grip, height, aperture), angle in product(shapes, angles):
        yield Strategy(float(angle), entry, grip, height, aperture)


def waypoints(env, strategy):
    wrist = math.radians(strategy.wrist_deg)
    x, y = env.source[:2] + strategy.grasp_xy_m
    sx, sy = np.array([x, y]) + strategy.entry_xy_m
    high = env.safe_z + strategy.entry_height_m
    opening = env.aperture + strategy.aperture_delta_m
    # Oblique paths first reach an offset high point, then an offset point
    # above the stem. The final leg brings the TCP onto the grasp point.
    near = env.pick_z + env.piece_height/2
    phases = [('approach', (sx, sy, high), opening),
              ('descend', (sx, sy, near), opening),
              ('align', (x, y, env.pick_z), opening),
              ('close', (x, y, env.pick_z), env.grasp),
              ('lift', (x, y, high), env.grasp)]
    return [(label, env.sim.validate(env.motion.solve(xyz, aperture, wrist=wrist)))
            for label, xyz, aperture in phases]


class PickupSweep:
    def __init__(self, env):
        self.env = env
        self.sim = sim = env.sim
        self.model = model = sim.model
        self.piece = env.config['piece']
        self.body = model.body(self.piece).id
        joint = model.body_jntadr[self.body]
        self.address = model.jnt_qposadr[joint]
        self.site = model.site('grasp_center').id
        self.feedback = SceneFeedback(sim)
        self.pads = {model.geom(f'finger_{index}_pad').id for index in (1, 2)}
        selected = [g for g in env.collision.environment if model.geom_bodyid[g] == self.body]
        other = [g for g in env.collision.environment if model.geom_bodyid[g] != self.body]
        self.pairs = env.collision.pairs + list(product(selected, other))
        self.support = list(product(selected, [g for g in other if model.geom(g).name == 'board_frame']))
        self.pad_pairs = list(product(self.pads, selected))
        self.king = list(product(env.collision.robot,
                                 [g for g in other if model.geom_bodyid[g] == model.body('white_king_e1').id]))
        self.scene = mujoco.MjData(model)
        self.park = env.command.copy()
        self.checker = SweptChecker(model, model.qpos0, sim.joint_ids, self.pairs)
        self.pair_indices = np.asarray(self.pairs)
        geom_type = model.geom_type[self.pair_indices]
        self.unbounded_pairs = np.any(np.isin(
            geom_type, [mujoco.mjtGeom.mjGEOM_PLANE, mujoco.mjtGeom.mjGEOM_HFIELD]), axis=1)
        self.pair_radii = model.geom_rbound[self.pair_indices].sum(axis=1)

    def visual_scene(self):
        self.checker.initial[:] = configuration_from_offsets(
            self.model, self.sim.manifest['pieces'], self.sim.qadr, self.park,
            self.env.observed_offsets, self.env.occupied)

    def allowed(self, phase):
        # Match the established preflight exemption for selected pads during
        # descent and closure. Bystanders and non-pad robot geoms stay checked.
        return self.support + (self.pad_pairs if phase != 'approach' else [])

    def screen(self, path):
        """Cheap endpoint rejection. Admission always requires full swept checking."""
        self.scene.qpos[:] = self.checker.initial
        min_king = .05
        for phase, command in path[:-1]:
            self.scene.qpos[self.sim.qadr] = command
            mujoco.mj_forward(self.model, self.scene)
            distance, pair = min((self.distance(a, b), (a, b)) for a, b in self.king)
            min_king = min(min_king, distance)
            if distance <= self.checker.clearance:
                return dict(status='endpoint_rejected', phase=phase, clearance_m=min_king,
                            geoms=[self.model.geom(g).name for g in pair])
            # Bounding spheres skip distant pairs only. Signed geom distance
            # determines rejection, and the continuous checker still gates motion.
            centers = self.scene.geom_xpos[self.pair_indices]
            near = (np.linalg.norm(centers[:, 0]-centers[:, 1], axis=1)
                    <= self.pair_radii+self.checker.clearance+1e-9)
            allowed = {frozenset(pair) for pair in self.allowed(phase)}
            for a, b in self.pair_indices[near | self.unbounded_pairs]:
                if frozenset((a, b)) in allowed:
                    continue
                distance = self.distance(a, b)
                if distance <= self.checker.clearance:
                    return dict(status='endpoint_rejected', phase=phase, clearance_m=min_king,
                                endpoint_distance_m=distance,
                                geoms=[self.model.geom(g).name for g in (a, b)])
        return dict(status='screened', clearance_m=min_king)

    def distance(self, a, b):
        return float(mujoco.mj_geomDistance(self.model, self.scene, a, b, .05, None))

    def preflight(self, path):
        sim, model, checker = self.sim, self.model, self.checker
        self.scene.qpos[:] = checker.initial
        self.scene.qpos[sim.qadr] = path[-2][1]
        mujoco.mj_forward(model, self.scene)
        rotation = self.scene.site_xmat[self.site].reshape(3, 3)
        offset = rotation.T @ (self.scene.xpos[self.body]-self.scene.site_xpos[self.site])
        relative_rotation = rotation.T @ self.scene.xmat[self.body].reshape(3, 3)

        def held(data):
            rot = data.site_xmat[self.site].reshape(3, 3)
            data.qpos[self.address:self.address+3] = data.site_xpos[self.site]+rot@offset
            mujoco.mju_mat2Quat(data.qpos[self.address+3:self.address+7],
                               (rot@relative_rotation).reshape(-1))

        coefficients = checker.coefficients.copy()
        hinge = model.jnt_type[sim.joint_ids] == mujoco.mjtJoint.mjJNT_HINGE
        for geom in range(model.ngeom):
            if model.geom_bodyid[geom] == self.body:
                coefficients[geom] = np.max(coefficients[self.env.collision.robot], axis=0)
                coefficients[geom, hinge] += 2*(np.linalg.norm(offset)+model.geom_rbound[geom])

        checker.samples = 0
        start = self.park
        for phase, end in path:
            lifting = phase == 'lift'
            failure = checker.interval(start, end, allowed=self.allowed(phase),
                                       configure=held if lifting else None,
                                       extra_coefficients=coefficients if lifting else None)
            if failure:
                return dict(status='sweep_rejected', phase=phase, failure=failure, samples=checker.samples)
            start = end
        return dict(status='sweep_accepted', samples=checker.samples,
                    nominal_swept_clearance_m=checker.clearance)

    def execute(self, path):
        env, sim = self.env, self.sim
        start = self.park
        height = float(sim.data.xpos[self.body, 2])
        grip = False
        held_intervals = 0
        unexpected = None
        phase = 'approach'
        started = float(sim.data.time)
        guard = env.contact_guard

        def stop():
            nonlocal unexpected
            guard.observe(sim.data)
            phase_label = 'APPROACHING' if phase == 'approach' else 'LIFTING'
            contacts = env.collision.unexpected_contacts(self.piece, phase_label)
            if contacts:
                unexpected = contacts[0]
            return bool(unexpected or guard.event or guard.topple_event)

        for phase, end in path:
            duration = np.max(np.abs(end-start)/sim.speed)
            intervals = max(1, math.ceil(duration/sim.dt))
            for index in range(1, intervals+env.dwell+1):
                command = start+(end-start)*min(index/intervals, 1.)
                env.controller.step(command, stop_when=stop)
                if unexpected or guard.event or guard.topple_event:
                    break
                if phase == 'close' and index == intervals+env.dwell:
                    grip = self.feedback.grip_contacts(self.piece)
                if phase == 'lift' and index > intervals:
                    stable = (self.feedback.grip_contacts(self.piece) and self.feedback.settled(self.piece)
                              and sim.data.xpos[self.body, 2]-height > env.piece_height)
                    held_intervals = held_intervals+1 if stable else 0
            if unexpected or guard.event or guard.topple_event or phase == 'close' and not grip:
                break
            start = end

        rise = float(sim.data.xpos[self.body, 2]-height)
        offsets = guard.displacements_mm()
        peak = max(offsets.values(), default=0.)
        approved = (grip and held_intervals == env.dwell and peak <= .25 and not
                    (unexpected or guard.event or guard.topple_event))
        return dict(status='physical_pass' if approved else 'physical_failure', phase=phase,
                    bilateral_grip=grip, lift=rise > env.piece_height, rise_m=rise,
                    stable_hold_intervals=held_intervals, peak_neighbor_mm=peak,
                    neighbor_displacements_mm=offsets, forbidden_contact=guard.event,
                    unexpected_contact=unexpected, topple=guard.topple_event,
                    simulated_duration_s=float(sim.data.time)-started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--seed', type=int, default=100007)
    parser.add_argument('--max-screen', type=int, default=312)
    parser.add_argument('--max-sweep', type=int, default=24)
    parser.add_argument('--max-execute', type=int, default=8)
    args = parser.parse_args()
    if min(args.max_screen, args.max_sweep, args.max_execute) <= 0:
        parser.error('Search budgets must be positive')
    args.output.mkdir(parents=True, exist_ok=False)
    env = CameraOnlyEnv(args.config)
    try:
        if (not env.localize_source_rgb or not env.motion.has_wrist
                or not env.displacement_penalty_per_mm or env.config['source'] != 'e2'
                or env.occupied.get('e1') != 'K'):
            raise ValueError('Expected the full-board RGB-localized wrist E2/E1 fixture with displacement supervision')
        env.reset(seed=args.seed)
        search = PickupSweep(env)
        search.visual_scene()
        manifest = dict(date_utc=datetime.now(timezone.utc).isoformat(),
                        revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                        source_sha256=sha(Path(__file__)), environment=provenance(env),
                        seed=args.seed, budgets=[args.max_screen, args.max_sweep, args.max_execute],
                        observed_offsets_m=env.observed_offsets,
                        scope='RGB-derived nominal preflight; simulator-only physical outcomes')
        (args.output/'protocol.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        records = []

        def save_report():
            result = dict(screen_counts=dict(Counter(r['status'] for r in records)),
                          swept_counts=dict(Counter(r['preflight']['status'] for r in records if 'preflight' in r)),
                          physical_counts=dict(Counter(r['physical']['status'] for r in records if 'physical' in r)),
                          records=records)
            (args.output/'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
            return {key: value for key, value in result.items() if key != 'records'}

        for index, strategy in enumerate(strategies(env)):
            if index >= args.max_screen:
                break
            record = dict(id=index, strategy=asdict(strategy))
            try:
                path = waypoints(env, strategy)
                record.update(search.screen(path))
                record['waypoints'] = [[label, q.tolist()] for label, q in path]
            except ValueError as error:
                record.update(status='ik_rejected', reason=str(error))
            records.append(record)
        print('Endpoint screening:', save_report()['screen_counts'], flush=True)
        candidates = [record for record in records if record['status'] == 'screened']
        # Keep deterministic grid order for equal margins.
        candidates.sort(key=lambda record: -record['clearance_m'])
        executed = 0
        for record in candidates[:args.max_sweep]:
            path = [(label, np.asarray(q)) for label, q in record['waypoints']]
            checked = record['preflight'] = search.preflight(path)
            if checked['status'] == 'sweep_accepted' and executed < args.max_execute:
                env.reset(seed=args.seed)
                search.visual_scene()
                before = env.last_camera_frame
                record['physical'] = search.execute(path)
                after = env.vision.observe(env.render())
                prefix = f"candidate-{record['id']}"
                for label, frame in (('before', before), ('after', after)):
                    Image.fromarray(frame.raw_rgb).save(args.output/f'{prefix}-{label}-rgb.png')
                    if frame.oriented:
                        Image.fromarray(frame.rectified_rgb).save(args.output/f'{prefix}-{label}-board.png')
                record['visual'] = dict(oriented_after=after.oriented, lift_confirmed=None,
                                        scope='RGB recorded; no calibrated visual hold detector')
                executed += 1
            print(f"Candidate {record['id']}: {checked['status']} "
                  f"{checked.get('phase', '')} {checked.get('failure', '')}", flush=True)
            save_report()
        print(save_report())
    finally:
        env.close()


if __name__ == '__main__':
    main()
