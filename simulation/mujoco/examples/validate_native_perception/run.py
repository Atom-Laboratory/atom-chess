"""Offline lateral RGB -> real acvision; simulator truth is evaluation-only.

No policy, motor command or physical-state update is performed.
"""
import argparse
import json
import hashlib
from pathlib import Path
import subprocess

import mujoco
import numpy as np
from PIL import Image
from atom_mujoco.backend import Simulation


def project(points, cameras, width, height):
    """Project planar evaluator points through the actual render GL camera."""
    position = np.mean([c.pos for c in cameras], axis=0)
    forward = np.mean([c.forward for c in cameras], axis=0)
    forward /= np.linalg.norm(forward)
    up = np.mean([c.up for c in cameras], axis=0)
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    near = float(cameras[0].frustum_near)
    top, bottom = float(cameras[0].frustum_top), float(cameras[0].frustum_bottom)
    focal = height * near / (top-bottom)
    relative = points-position
    depth = relative @ forward
    if np.any(depth <= 0):
        raise ValueError('Evaluation points behind camera')
    return np.column_stack((width/2 + focal*(relative @ right)/depth,
                            height*top/(top-bottom) - focal*(relative @ up)/depth))


def evaluate(observation, pixels, pitch, truth_colors=None):
    if observation['homography'] is None:
        return {'status': 'no_detection', 'motion_ready': False}
    H = np.array(observation['homography'])
    mapped = np.column_stack((pixels,np.ones(len(pixels)))) @ H.T
    mapped = mapped[:,:2]/mapped[:,2:]
    # Best D4 alignment is an ORACLE evaluation convention, never perception output.
    centers = np.array([(c+.5,r+.5) for r in range(8) for c in range(8)])*100
    variants = []
    for swap in (False,True):
        for flipx in (False,True):
            for flipy in (False,True):
                candidate = centers[:,::-1].copy() if swap else centers.copy()
                if flipx: candidate[:,0] = 800-candidate[:,0]
                if flipy: candidate[:,1] = 800-candidate[:,1]
                variants.append(candidate)
    expected = min(variants,key=lambda x: np.mean(np.linalg.norm(mapped-x,axis=1)))
    errors = np.linalg.norm(mapped-expected,axis=1)/100*pitch*1000
    accuracy = np.mean(np.all(np.floor(mapped/100)==np.floor(expected/100),axis=1))
    confusion = None
    if truth_colors is not None:
        candidates = {(cell['row'],cell['column']):cell['candidate'] for cell in observation['cells']}
        confusion = {actual:{predicted:0 for predicted in ('empty','white','black','unknown')}
                     for actual in ('empty','white','black')}
        for point, actual in zip(expected,truth_colors):
            col,row = (point//100).astype(int)
            predicted = candidates.get((row,col),'unknown')
            confusion[actual][predicted] += 1
    return dict(candidate_color_confusion=confusion, status='oracle_aligned_diagnostic', motion_ready=False,
                orientation_estimated_by_vision=False, squares_evaluated=64,
                square_assignment_accuracy=float(accuracy),
                nominal_board_equivalent_error_mm=dict(mean=float(errors.mean()),median=float(np.median(errors)),
                                     p95=float(np.percentile(errors,95)),max=float(errors.max())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--executable',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--azimuths',type=float,nargs='+',default=[270],help='Provisional fixed-view sweep, degrees')
    args = parser.parse_args()
    if not np.isfinite(args.azimuths).all():
        parser.error('Finite azimuths required')
    executable = args.executable.resolve(strict=True)
    args.output.mkdir(parents=True,exist_ok=False)
    sim = Simulation(args.bundle)
    names = [f'{c}{r}' for r in range(1,9) for c in 'abcdefgh']
    initial_colors = {p['initial_square']:p['color'] for p in sim.manifest['pieces']}
    truth_colors = [initial_colors.get(name,'empty') for name in names]
    points = []
    for name in names:
        geom = sim.model.geom('square_'+name).id
        point = sim.data.geom_xpos[geom].copy()
        point[2] += sim.model.geom_size[geom,2]
        points.append(point)
    points = np.array(points)
    camera = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(camera)
    camera.lookat[:] = sim.manifest['scene']['board_center_m']
    camera.distance = .85
    camera.azimuth = 270
    # Provisional camera inclination sweep, not a measured hardware mount.
    records = []
    with mujoco.Renderer(sim.model,height=600,width=800) as renderer:
        for azimuth,elevation in ((a,e) for a in args.azimuths for e in (-35,-45,-55)):
            camera.azimuth = azimuth
            case = f'{azimuth:g}-{abs(elevation)}'
            camera.elevation = elevation
            renderer.update_scene(sim.data,camera=camera)
            frame = renderer.render().copy()
            image = args.output/f'lateral-{case}.png'
            Image.fromarray(frame,'RGB').save(image)
            pixels = project(points,renderer.scene.camera,800,600)
            output = args.output/f'acvision-{case}'
            subprocess.run([str(executable),str(image.resolve()),str(output.resolve())],check=True,timeout=60)
            observation = json.loads((output/'observation.json').read_text())
            result = evaluate(observation,pixels,sim.manifest['scene']['square_size_m'],truth_colors)
            if observation.get('schema_version') != 2 or not observation['processing_completed']:
                raise RuntimeError('Native schema 2 completed diagnostic required')
            records.append(dict(elevation=elevation,azimuth=azimuth,distance_m=.85,
                image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                observation_path=str(output.relative_to(args.output)/'observation.json'),
                source_sha256=observation['source_sha256'], **result))
            (args.output/f'evaluator-only-{case}.json').write_text(json.dumps(
                dict(source='MuJoCo ground truth; NOT perception input',squares=names,
                     projected_centers_px=pixels.tolist()),indent=2))
    report = dict(schema=2, mujoco_version=mujoco.__version__,
                  camera_lookat=camera.lookat.tolist(), image_size=[800,600],
                  model_fovy_degrees=float(sim.model.vis.global_.fovy), model_sha256=hashlib.sha256((args.bundle/'model.xml').read_bytes()).hexdigest(),
                  executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
                  camera_status='experimental_ideal_pinhole',
                  calibration_status='unvalidated',training_gate='closed',results=records)
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
