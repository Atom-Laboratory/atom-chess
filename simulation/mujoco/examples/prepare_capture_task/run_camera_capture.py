"""Execute the fixed P039 capture with RGB transition gates and nominal geometry."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import mujoco
import numpy as np
from PIL import Image

from atom_mujoco.backend import Simulation
from atom_mujoco.virtual_camera import add_camera_override, make_camera
from atom_mujoco.collision import SceneCollision, SweptChecker, pregrasp_opening
from atom_mujoco.graveyard_vision import GraveyardEvidence
from atom_mujoco.motion_controller import MotionController
from atom_mujoco.native_motion import NativeMotion
from atom_mujoco.native_vision import NativeVision
from validate_graveyard_camera import project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'library', 'motion-library', 'output'):
        parser.add_argument('--'+name, required=True, type=Path)
    parser.add_argument('--preview', action='store_true', help='Show live RGB and rectified board')
    parser.add_argument('--fixture-offset-mm', type=float, nargs=4, default=[0.]*4,
                        metavar=('WHITE_X', 'WHITE_Y', 'BLACK_X', 'BLACK_Y'),
                        help='Simulation test setup only; offsets never enter camera inference')
    resolve_camera = add_camera_override(parser)
    args = parser.parse_args()
    if not np.isfinite(args.fixture_offset_mm).all() or max(map(abs, args.fixture_offset_mm)) > 3:
        parser.error('Fixture offsets must be within the experimental Ã‚Â±3 mm search range')
    args.resolve_camera = resolve_camera
    if args.preview:
        from camera_preview import show
        return show(lambda publish: execute(args, publish))
    return execute(args)


def execute(args, publish=None):
    task = json.loads((args.bundle/'capture_task.json').read_text(encoding='utf-8'))
    sim = Simulation(args.bundle)
    if sim.manifest.get('fixture_kind') != 'two_piece_capture':
        raise ValueError('Expected a two-piece capture bundle')
    args.output.mkdir(parents=True, exist_ok=False)
    model = sim.model
    park = np.array([-1.5, .12, -1.5, 0., 0.])
    sim.reset(park)
    controller = MotionController(sim)
    motion = NativeMotion(args.motion_library, sim)
    attacker, victim = task['attacker'], task['captured']
    source, contested, slot = attacker['source'], victim['source'], victim['target']['slot']
    pieces = {source: attacker['piece'], contested: victim['piece']}
    if attacker['target'] != contested or any(
            p['kind'] != 'pawn' for p in sim.manifest['pieces']):
        raise ValueError('This experimental executor expects the two-pawn capture fixture')
    board = model.body('chessboard').pos
    board_support = board[2] + model.geom('board_frame').size[2]
    centers = {square: (board + model.site('square_center_'+square).pos).copy()
               for square in pieces}
    for point in centers.values():
        point[2] = board_support
    centers[slot] = model.site('graveyard_center_'+slot).pos.copy()

    settings = args.resolve_camera(args, sim.manifest['scene']['board_center_m'])
    camera = make_camera(settings)
    width, height = settings['width'], settings['height']
    report = dict(status='FAILED', evidence_source='rgb_only', completed_transfers=0,
                  observations={}, preflight=[], grasp_position='RGB match against calibrated pawn templates',
                  scope='fixed two-pawn fixture; experimental camera evidence')

    # Synthetic empty RGB calibration: independent scratch state, never read live piece poses.
    scratch = mujoco.MjData(model)
    scratch.qpos[sim.qadr] = park
    addresses = {}
    for name in pieces.values():
        body = model.body(name).id
        address = model.jnt_qposadr[model.body_jntadr[body]]
        addresses[name] = address
        scratch.qpos[address+2] = -10.
    for name, offset in zip(pieces.values(), np.reshape(args.fixture_offset_mm, (2, 2))):
        address = addresses[name]
        sim.data.qpos[address:address+2] += offset/1000
    mujoco.mj_forward(model, sim.data)
    mujoco.mj_forward(model, scratch)
    with mujoco.Renderer(model, width=width, height=height) as renderer, NativeVision(
            args.library, layout=args.bundle/'reference-layout.json') as vision:
        def capture(data, label=None):
            renderer.update_scene(data, camera=camera)
            frame = vision.observe(renderer.render().copy())
            if publish is not None and label is not None:
                publish(frame, label)
            return frame

        if publish is not None:
            capture(sim.data, 'Preparing camera calibration')

        empty = capture(scratch)
        Image.fromarray(empty.raw_rgb).save(args.output/'empty-calibration.png')
        regions = {}
        for location, center in centers.items():
            geom = model.geom(('graveyard_support_' if location == slot else 'square_')+location)
            hx, hy = geom.size[:2]/2
            points = center + np.array([[-hx,-hy,0], [hx,-hy,0], [hx,hy,0], [-hx,hy,0]])
            polygon = project(points, renderer.scene.camera, width, height)
            regions[location] = GraveyardEvidence(
                empty, polygon, channel_delta=35, min_fraction=.25 if location == slot else .07, max_drift_px=2.)

        # Camera calibration for this fixture: isolated upright pawn rendered at
        # known offsets. Runtime matching reads RGB, never the live body state.
        templates = {}
        crops = {}
        offsets_by_key = {}
        for location, name in [*pieces.items(), (slot, victim["piece"]),
                               (contested, attacker["piece"])]:
            center = centers[location]
            half = sim.manifest['scene']['square_size_m']/2
            corners = np.array([[x, y, z] for x in (-half, half) for y in (-half, half)
                                for z in (0., .032)])+center
            uv = project(corners, renderer.scene.camera, width, height)
            left, top = np.floor(uv.min(axis=0)).astype(int)
            right, bottom = np.ceil(uv.max(axis=0)).astype(int)
            if min(left, top) < 0 or right > width or bottom > height:
                raise ValueError('Pawn template crop outside image')
            key = (location, name)
            crop = crops[key] = np.s_[top:bottom, left:right]
            address = addresses[name]
            radius = model.geom(name+'_base').size[0]
            support_half = min(model.geom('graveyard_support_'+slot).size[:2]) if location == slot else half
            limit = int(np.floor((support_half-radius)*1000+1e-9))
            offsets = np.array([(x, y) for x in range(-limit, limit+1)
                                for y in range(-limit, limit+1)])/1000
            offsets_by_key[key] = offsets
            samples = []
            for offset in offsets:
                scratch.qpos[address:address+3] = center + [*offset, 0.]
                mujoco.mj_forward(model, scratch)
                renderer.update_scene(scratch, camera=camera)
                samples.append(renderer.render()[crop].astype(np.float32))
            scratch.qpos[address+2] = -10.
            templates[key] = np.array(samples)

        def locate(location, name, frames):
            key = (location, name)
            offsets = offsets_by_key[key]
            estimates = []
            errors = []
            for frame in frames:
                rgb = frame.raw_rgb[crops[key]].astype(np.float32)
                rms = np.sqrt(np.mean(np.square(templates[key]-rgb), axis=(1, 2, 3)))
                best = int(np.argmin(rms))
                estimates.append(offsets[best])
                errors.append(float(rms[best]))
            report.setdefault('grasp_estimates', {})[f'{location}:{name}'] = dict(
                offsets_mm=(np.array(estimates)*1000).tolist(), rms=errors)
            if max(errors) > 18 or np.max(np.ptp(estimates, axis=0)) > .00101:
                raise RuntimeError('RGB_GRASP_MATCH_UNCERTAIN: '+location)
            return centers[location] + [*np.median(estimates, axis=0), 0.]

        def check(label, occupied):
            frames = []
            for _ in range(3):
                for _ in range(5):
                    controller.step(park)
                frames.append(capture(sim.data, label))
            Image.fromarray(frames[-1].raw_rgb).save(args.output/f'{label}.png')
            readings = {name: region.summarize(frames) for name, region in regions.items()}
            report['observations'][label] = readings
            if any(value['candidate'] != ('foreground_candidate' if key in occupied
                                          else 'background_candidate')
                   for key, value in readings.items()):
                raise RuntimeError('VISUAL_TRANSITION_UNVERIFIED: '+label)
            return frames

        def advance_preview(goal, label):
            for step in range(180):
                controller.step(goal)
                if publish is not None and step % 20 == 0:
                    capture(sim.data, label)

        def transfer(piece, end, observed_positions):
            # Preflight uses a nominal scene reconstructed from accepted camera
            # regions and static pawn geometry, without live simulator truth.
            scratch.qpos[sim.qadr] = park
            for name, position in observed_positions.items():
                scratch.qpos[addresses[name]:addresses[name]+3] = position
            pick = observed_positions[piece]
            mujoco.mj_forward(model, scratch)
            proxy = SimpleNamespace(model=model, data=scratch, qadr=sim.qadr,
                                    joint_ids=sim.joint_ids, lower=sim.lower, upper=sim.upper,
                                    observe=lambda: {'position': park.copy()})
            stem = model.geom(piece+'_stem')
            grip = stem.pos[2]-stem.size[1]/4
            start_z = pick[2]+grip
            end_z = centers[end][2]+grip
            safe_z = max(start_z, end_z)+.07  # Existing Playground clearance.
            poses = motion.plan(pick, centers[end], safe_z, start_z)
            poses[5:7, 2] = end_z
            aperture = pregrasp_opening(proxy, piece)
            grasp = pregrasp_opening(proxy, piece, side_gap_m=-.0005)
            solutions = [motion.solve(poses[i, :3], aperture) for i in (0, 1, 3, 4, 5)]
            collision = SceneCollision(proxy)
            checked = collision.check_plan(solutions, piece, centers[end],
                                           aperture=aperture, grasp=grasp)
            report['preflight'].append(checked)
            if not checked['valid']:
                raise RuntimeError('NOMINAL_COLLISION_PREFLIGHT: '+checked['phase'])
            scratch.qpos[addresses[piece]:addresses[piece]+3] = centers[end]
            retreat = SweptChecker(model, scratch.qpos, sim.joint_ids, collision.pairs)
            last = np.array(checked['trajectory'][-1]['end'])
            if failure := retreat.interval(last, park):
                report['return_preflight_failure'] = failure
                raise RuntimeError('RETURN_TO_CAMERA_POSE_PREFLIGHT')
            for waypoint in checked['trajectory']:
                advance_preview(waypoint['end'], f"{piece} / {waypoint['phase']}")
            advance_preview(park, 'Returning to observation pose')

        try:
            frames = check('before', {source, contested})
            transfer(victim['piece'], slot, {
                victim['piece']: locate(contested, victim['piece'], frames),
                attacker['piece']: locate(source, attacker['piece'], frames),
            })
            frames = check('removed', {source, slot})
            removed = locate(slot, victim['piece'], frames)
            report['completed_transfers'] = 1
            transfer(attacker['piece'], contested, {
                attacker['piece']: locate(source, attacker['piece'], frames),
                victim['piece']: removed,
            })
            frames = check('placed', {contested, slot})
            locate(contested, attacker['piece'], frames)
            locate(slot, victim['piece'], frames)
            report['completed_transfers'] = 2
            report['status'] = 'COMPLETED_RGB_TRANSITIONS'
        except (RuntimeError, ValueError) as error:
            report['failure'] = str(error)

    (args.output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(report['status'], report.get('failure', ''), args.output)
    return int(report['completed_transfers'] != 2)


if __name__ == '__main__':
    raise SystemExit(main())
