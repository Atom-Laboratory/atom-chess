"""Continuous MuJoCo RGB -> native acvision -> task-conditioned policy input preview."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import mujoco
import numpy as np
from PIL import Image

from atom_mujoco.native_vision import NativeVision
from atom_mujoco.camera_policy import policy_observation
from atom_mujoco.virtual_camera import add_camera_override, make_camera


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', type=Path, required=True,
                        help='Preserved reference-scene.xml from a marker capture')
    parser.add_argument('--layout', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', default='e2')
    parser.add_argument('--target', default='e4')
    parser.add_argument('--frames', type=int, default=30)
    parser.add_argument('--empty-fixture', action='store_true',
                        help='Render a synthetic empty-board RGB calibration before restoring pieces')
    parser.add_argument('--preview', action='store_true')
    resolve_camera = add_camera_override(parser)
    args = parser.parse_args()
    if args.frames <= 0:
        parser.error('Positive frame count required')
    args.output.mkdir(parents=True, exist_ok=False)
    model = mujoco.MjModel.from_xml_path(str(args.scene.resolve()))
    data = mujoco.MjData(model)
    joints = ['joint_base_to_link1', 'joint_z_axis_arm1', 'joint_arm1_link_arm2_link',
              'finger_1', 'finger_2']
    # An experimental initial observation pose, explicitly configured without piece truth.
    command = np.array([-1.5, .12, -1.5, 0., 0.])
    for name, value in zip(joints, command):
        joint = model.joint(name).id
        if not model.jnt_range[joint, 0] <= value <= model.jnt_range[joint, 1]:
            raise ValueError('Observation pose outside model limits')
        data.qpos[model.jnt_qposadr[joint]] = value
    mujoco.mj_forward(model, data)
    settings = resolve_camera(args, model.body('chessboard').pos)
    camera = make_camera(settings)
    records = []
    with mujoco.Renderer(model, height=settings['height'], width=settings['width']) as renderer, NativeVision(
            args.library, layout=args.layout) as vision:
        background_ready = False
        if args.empty_fixture:
            initial = data.qpos.copy()
            try:
                for joint in range(model.njnt):
                    body = model.body(int(model.jnt_bodyid[joint])).name
                    if (model.jnt_type[joint] == mujoco.mjtJoint.mjJNT_FREE
                            and body.startswith(('white_', 'black_'))):
                        data.qpos[model.jnt_qposadr[joint]+2] = -10.
                mujoco.mj_forward(model, data)
                renderer.update_scene(data, camera=camera)
                empty = renderer.render().copy()
                Image.fromarray(empty).save(args.output/'empty-reference.png')
                background_ready = vision.set_empty(empty)
            finally:
                data.qpos[:] = initial
                mujoco.mj_forward(model, data)
        for index in range(args.frames):
            renderer.update_scene(data, camera=camera)
            rgb = renderer.render().copy()
            captured = time.monotonic()
            frame = vision.observe(rgb, captured_at_s=captured)
            features = None
            error = None
            try:
                observation = policy_observation(
                    frame, source=args.source, target=args.target,
                    previous_action=np.zeros(4), commanded_joints=command,
                    max_age_s=1.)
                features = observation.features()
            except ValueError as exception:
                error = str(exception)
            records.append(dict(sequence=frame.sequence, geometry=frame.homography is not None,
                                oriented=frame.oriented, policy_input_available=features is not None,
                                processing_ms=frame.processing_ms, error=error,
                                foreground_candidates=(
                                    int(np.isfinite(frame.foreground_centroids[:, :, 0]).sum())
                                    if frame.foreground_centroids is not None else None)))
            if index == 0:
                Image.fromarray(rgb).save(args.output/'camera.png')
                Image.fromarray(frame.rectified_rgb).save(args.output/'rectified.png')
                if features is not None:
                    Image.fromarray(features['image'].transpose(1, 2, 0)).save(args.output/'actor-input.png')
            if args.preview:
                import tkinter as tk
                from PIL import ImageTk
                if index == 0:
                    window = tk.Tk()
                    window.title('ATOM native camera-to-policy preview')
                    label = tk.Label(window)
                    label.pack()
                canvas = np.concatenate((
                    np.array(Image.fromarray(rgb).resize((800, 600))),
                    np.array(Image.fromarray(frame.rectified_rgb).resize((600, 600)))), axis=1)
                photo = ImageTk.PhotoImage(Image.fromarray(canvas))
                label.configure(image=photo)
                label.image = photo
                window.update()
        if args.preview:
            window.mainloop()
    report = dict(schema=1, native_source_sha256=vision.source_sha256,
                  library_sha256=hashlib.sha256(args.library.read_bytes()).hexdigest(),
                  scene_sha256=hashlib.sha256(args.scene.read_bytes()).hexdigest(),
                  layout_sha256=hashlib.sha256(args.layout.read_bytes()).hexdigest(),
                  observation_pose=command.tolist(), source=args.source, target=args.target,
                  camera=settings,
                  actor_features=['image', 'task', 'previous_action', 'commanded_joints', 'phase'],
                  background_ready=background_ready,
                  background_source='synthetic empty RGB fixture' if args.empty_fixture else None,
                  training_ready=False, records=records)
    (args.output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(frames=len(records),
                         policy_inputs=sum(r['policy_input_available'] for r in records),
                         mean_processing_ms=float(np.mean([r['processing_ms'] for r in records])))))


if __name__ == '__main__':
    main()
