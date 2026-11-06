"""Measure slot evidence on empty, occupied and adjacent-slot RGB fixtures."""
import argparse
import json
from pathlib import Path
import sys

import mujoco
import numpy as np
from PIL import Image

from atom_mujoco.backend import Simulation
from atom_mujoco.virtual_camera import add_camera_override, make_camera
from atom_mujoco.graveyard_vision import GraveyardEvidence
from atom_mujoco.native_vision import NativeVision

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_native_perception.run import project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'library', 'output'):
        parser.add_argument('--'+name, required=True, type=Path)
    resolve_camera = add_camera_override(parser)
    args = parser.parse_args()
    sim = Simulation(args.bundle)
    task = json.loads((args.bundle/'capture_task.json').read_text(encoding='utf-8'))
    slot = task['captured']['target']['slot']
    slots = sim.manifest['scene']['graveyard_slots']
    neighbor = min((name for name in slots if name != slot),
                   key=lambda name: np.linalg.norm(np.subtract(slots[name], slots[slot])))
    sim.reset([-1.5, .12, -1.5, 0., 0.])
    settings = resolve_camera(args, sim.manifest['scene']['board_center_m'])
    camera = make_camera(settings)
    args.output.mkdir(parents=True, exist_ok=False)
    width, height = settings['width'], settings['height']
    model = sim.model
    support = model.geom('graveyard_support_'+slot)
    center = model.site('graveyard_center_'+slot).pos
    hx, hy = support.size[:2]/2
    points = center + np.array([[-hx,-hy,0], [hx,-hy,0], [hx,hy,0], [-hx,hy,0]])

    # Explicit fixture setup is isolated from the detector. It receives only RGB.
    scratch = mujoco.MjData(model)
    scratch.qpos[:] = sim.data.qpos
    body = model.body(task['captured']['piece']).id
    address = model.jnt_qposadr[model.body_jntadr[body]]
    with mujoco.Renderer(model, width=width, height=height) as renderer, NativeVision(
            args.library, layout=args.bundle/'reference-layout.json') as vision:
        mujoco.mj_forward(model, scratch)
        renderer.update_scene(scratch, camera=camera)
        baseline = renderer.render().copy()
        Image.fromarray(baseline).save(args.output/'empty-slot-reference.png')
        # Known virtual camera extrinsics and static support geometry are calibration.
        # Dynamic body poses are not used to compute the pixel region.
        polygon = project(points, renderer.scene.camera, width, height)
        detector = GraveyardEvidence(vision.observe(baseline), polygon, channel_delta=35,
                                    min_fraction=.25, max_drift_px=2.)
        results = {}
        for name, location in [('empty', None), ('occupied', slot), ('adjacent', neighbor)]:
            scratch.qpos[:] = sim.data.qpos
            if location:
                scratch.qpos[address:address+3] = model.site('graveyard_center_'+location).pos
            mujoco.mj_forward(model, scratch)
            frames = []
            for _ in range(3):
                renderer.update_scene(scratch, camera=camera)
                rgb = renderer.render().copy()
                frames.append(vision.observe(rgb))
            Image.fromarray(rgb).save(args.output/f'{name}.png')
            results[name] = detector.summarize(frames)
    report = dict(slot=slot, neighbor=neighbor, polygon_px=polygon.tolist(),
                  channel_delta=35, min_fraction=.25, max_drift_px=2., results=results)
    (args.output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    expected = ['background_candidate', 'foreground_candidate', 'background_candidate']
    return int([record['candidate'] for record in results.values()] != expected)


if __name__ == '__main__':
    raise SystemExit(main())
