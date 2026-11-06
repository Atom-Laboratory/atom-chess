"""Create an exclusive one-piece camera-RL fixture from preserved ATOM scene assets."""
import argparse
from atom_mujoco.virtual_camera import DEFAULT_REFERENCE_LAYOUT
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from atom_mujoco.virtual_camera import add_camera_override, camera_settings


def prepare(bundle, reference_scene, layout, output, *, piece, source, target, camera=None, obstacles=()):
    output = Path(output)
    if source == target or any(len(s) != 2 or s[0] not in 'abcdefgh' or s[1] not in '12345678'
                               for s in (source, target)):
        raise ValueError('Distinct algebraic squares required')
    manifest = json.loads((Path(bundle)/'manifest.json').read_text())
    selected = next(p for p in manifest['pieces'] if p['name'] == piece)
    neighbors = []
    for spec in obstacles:
        name, square = spec.split('@')
        if (name == piece or square in (source, target) or len(square) != 2
                or square[0] not in 'abcdefgh' or square[1] not in '12345678'
                or any(p['name'] == name or p['initial_square'] == square for p in neighbors)):
            raise ValueError('Obstacle must have a distinct identity and square')
        record = next(p for p in manifest['pieces'] if p['name'] == name)
        neighbors.append(dict(record, initial_square=square))
    retained = {piece, *(p['name'] for p in neighbors)}
    tree = ET.parse(reference_scene)
    root = tree.getroot()
    world = root.find('worldbody')
    for body in list(world.findall('body')):
        if body.find('freejoint') is not None and body.get('name') not in retained:
            world.remove(body)
    scene = manifest['scene']
    pitch = scene['square_size_m']
    center = np.array(scene['board_center_m'])
    selected_body = world.find(f"body[@name='{piece}']")
    initial = [float(v) for v in selected_body.get('pos').split()]
    initial[:2] = center[:2] + [
        (ord(source[0])-ord('a')-3.5)*pitch, (int(source[1])-4.5)*pitch]
    for neighbor in neighbors:
        body = world.find(f"body[@name='{neighbor['name']}']")
        position = [float(v) for v in body.get('pos').split()]
        square = neighbor['initial_square']
        position[:2] = center[:2]+[(ord(square[0])-97-3.5)*pitch, (int(square[1])-4.5)*pitch]
        body.set('pos', ' '.join(map(str, position)))
    selected_body.set('pos', ' '.join(map(str, initial)))
    output.mkdir(parents=True, exist_ok=False)
    # Explicit assets make the derived fixture independent of temporary source paths.
    assets = {}
    for node in root.findall('./asset/*'):
        if node.get('file'):
            path = Path(node.get('file'))
            if not path.is_absolute():
                path = Path(reference_scene).parent/path
            name = path.name
            destination = output/name
            if destination.exists() and destination.read_bytes() != path.read_bytes():
                raise ValueError('Asset filename collision')
            if not destination.exists():
                shutil.copyfile(path, destination)
            node.set('file', name)
            assets[name] = hashlib.sha256(destination.read_bytes()).hexdigest()
    tree.write(output/'model.xml', encoding='utf-8')
    manifest['pieces'] = [dict(selected, initial_square=source), *neighbors]
    manifest['assets_sha256'] = assets
    manifest['model_sha256'] = hashlib.sha256((output/'model.xml').read_bytes()).hexdigest()
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    shutil.copyfile(layout, output/'reference-layout.json')
    config = dict(schema=1, bundle=str(output.resolve()),
                  vision_library=str(Path('build/p038-core/bin/Release/acvision_runtime.dll').resolve()),
                  motion_library=str(Path('build/p038-core/bin/Release/motion_runtime.dll').resolve()),
                  layout=str((output/'reference-layout.json').resolve()), piece=piece,
                  source=source, target=target, obstacle_pieces=[p['name'] for p in neighbors],
                  initial_command=[-1.5, .12, -1.5, 0, 0] + ([np.pi] if any(
                      j['name'] == 'wrist_joint' for j in manifest['joints']) else []),
                  camera=camera_settings(center, camera),
                  control_repeat=5, dwell_steps=10, horizon=240, max_perception_age_s=1.,
                  model_status='experimental model geometry; fingertip contact proxies',
                  reward_weights=dict(approach=.2, grasp=2., lift=3., transport=2.,
                                      placement=3., success=10., failure=-5., time=-.01, action=-.001))
    (output/'environment.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    mujoco.MjModel.from_xml_path(str((output/'model.xml').resolve()))
    print(output/'environment.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--reference-scene', type=Path, required=True)
    parser.add_argument('--layout', type=Path, default=DEFAULT_REFERENCE_LAYOUT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--piece', default='white_pawn_e2')
    parser.add_argument('--source', default='e4')
    parser.add_argument('--target', default='d5')
    parser.add_argument('--obstacle', action='append', default=[], help='Physical piece@initial_square, repeatable')
    resolve_camera = add_camera_override(parser)
    args = parser.parse_args()
    manifest = json.loads((args.bundle / "manifest.json").read_text())
    prepare(args.bundle, args.reference_scene, args.layout, args.output,
            piece=args.piece, source=args.source, target=args.target,
            camera=resolve_camera(args, manifest["scene"]["board_center_m"]), obstacles=args.obstacle)


if __name__ == '__main__':
    main()
