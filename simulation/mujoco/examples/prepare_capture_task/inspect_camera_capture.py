"""Inspect the camera evidence available for a two-piece capture."""
import argparse
import json
from pathlib import Path

import mujoco
from PIL import Image

from atom_mujoco.backend import Simulation
from atom_mujoco.virtual_camera import add_camera_override, make_camera
from atom_mujoco.native_vision import NativeVision


LABELS = {-1: 'unknown', 0: 'empty_candidate', 1: 'white_candidate', 2: 'black_candidate'}


def square_candidate(frame, square):
    if frame.homography is None or not frame.oriented:
        return 'unknown'
    return LABELS[int(frame.candidates[8-int(square[1]), ord(square[0])-ord('a')])]


def capture_evidence(frames, task):
    """Inspect three fresh observations. Candidate color never authorizes motion."""
    frames = tuple(frames)
    if len(frames) != 3 or any(a.sequence >= b.sequence for a, b in zip(frames, frames[1:])):
        raise ValueError('Expected three distinct ordered camera observations')
    squares = (task['attacker']['source'], task['captured']['source'])
    return dict(
        status='BLOCKED_BEFORE_MOTION',
        evidence_source='native_acvision_rgb',
        candidates={square: [square_candidate(frame, square) for frame in frames]
                    for square in squares},
        oriented_frames=sum(frame.oriented and frame.homography is not None for frame in frames),
        graveyard_slot=task['captured']['target']['slot'],
        missing=['validated_grasp_pose', 'visual_grasp_and_release',
                 'visual_graveyard_slot_occupancy'],
        completed_transfers=0,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--library', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    resolve_camera = add_camera_override(parser)
    args = parser.parse_args()

    task = json.loads((args.bundle/'capture_task.json').read_text(encoding='utf-8'))
    sim = Simulation(args.bundle)
    if sim.manifest.get('fixture_kind') != 'two_piece_capture':
        parser.error('Expected a prepare_capture_task bundle')
    args.output.mkdir(parents=True, exist_ok=False)

    # P037 observation pose and fixed camera. Acquisition only.
    pose = [-1.5, .12, -1.5, 0., 0.]
    sim.reset(pose)
    settings = resolve_camera(args, sim.manifest['scene']['board_center_m'])
    camera = make_camera(settings)

    frames = []
    with mujoco.Renderer(sim.model, width=settings['width'], height=settings['height']) as renderer, NativeVision(
            args.library, layout=args.bundle/'reference-layout.json') as vision:
        for index in range(3):
            renderer.update_scene(sim.data, camera=camera)
            rgb = renderer.render().copy()
            frame = vision.observe(rgb)
            frames.append(frame)
            Image.fromarray(rgb).save(args.output/f'camera-{index}.png')
            if frame.homography is not None:
                Image.fromarray(frame.rectified_rgb).save(args.output/f'board-{index}.png')

    report = capture_evidence(frames, task)
    report['sampling'] = 'static observation pose; repeated renders are not independent trials'
    (args.output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
