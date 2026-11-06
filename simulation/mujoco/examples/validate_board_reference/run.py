"""Render explicit experimental ArUco supports; native vision receives images/layout only."""
import argparse
import sys
from atom_mujoco.paths import MODULE_ROOT
sys.path.insert(0, str(MODULE_ROOT / "examples"))
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from PIL import Image
from validate_native_perception.run import project
from atom_mujoco.virtual_camera import add_camera_override, make_camera, DEFAULT_REFERENCE_LAYOUT


def foreground_metrics(observation, truth, board, side):
    candidates = {cell['square']: cell['foreground_centroid_rectified_px']
                  for cell in observation['cells']
                  if cell['foreground_centroid_rectified_px'] is not None}
    errors = {}
    for square in truth.keys() & candidates.keys():
        x, y = truth[square]
        expected = np.array([x - board[0] + side/2, board[1] + side/2 - y]) * 800/side
        errors[square] = float(np.linalg.norm(candidates[square] - expected) * side/800 * 1000)
    return dict(expected=len(truth), matched=len(errors),
                unmatched_squares=sorted(candidates.keys() - truth.keys()),
                error_mm_by_square=dict(sorted(errors.items())))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--layout', type=Path, help='Alternative measured or experimental marker layout')
    p.add_argument('--executable',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--save-evaluator', action='store_true',
                   help='Save independent projected board points after native execution')
    p.add_argument('--evaluate-foreground', action='store_true')
    p.add_argument('--elevations', type=float, nargs='+')
    p.add_argument('--azimuths', type=float, nargs='+')
    resolve_camera = add_camera_override(p)
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    layout_path = args.layout or DEFAULT_REFERENCE_LAYOUT
    layout = json.loads(layout_path.read_text())
    manifest=json.loads((args.bundle/'manifest.json').read_text())
    side=manifest['scene']['square_size_m']*8
    if not np.isclose(side*1000,layout['board_side_mm']):
        raise ValueError('Reference layout must match scene board dimensions')
    root=ET.parse(args.bundle/'model.xml').getroot()
    for asset in root.findall('./asset/*'):
        if asset.get('file'): asset.set('file',str((args.bundle/asset.get('file')).resolve()))
    visual=root.find('./visual/global')
    board=np.array(manifest['scene']['board_center_m'])
    settings = resolve_camera(args, board)
    width, height = settings['width'], settings['height']
    visual.set('offwidth', str(width)); visual.set('offheight', str(height))
    assets=root.find('asset'); world=root.find('worldbody')
    # Existing model square visual top: board z + .007 center + .001 halfheight.
    z=board[2]+.008
    half=(layout['marker_black_side_mm']+2*layout['marker_white_margin_mm'])/2000
    for marker in layout['markers']:
        ident=marker['id']
        xy=np.mean(marker['corners_rectified_px'],axis=0)/800*side
        center=board[:2]+[xy[0]-side/2,side/2-xy[1]]
        name=f'reference_{ident}'
        ET.SubElement(assets,'texture',name=name,type='2d',file=str((args.assets/f'marker-{ident}.png').resolve()))
        ET.SubElement(assets,'material',name=name,texture=name,texuniform='false',rgba='1 1 1 1',specular='0',shininess='0')
        ET.SubElement(assets,'mesh',name=name,vertex=f'{-half} {-half} 0 {half} {-half} 0 {half} {half} 0 {-half} {half} 0',
                      inertia='shell',face='0 1 2 0 2 3',texcoord='0 1 1 1 1 0 0 0')
        ET.SubElement(world,'geom',name=name,type='mesh',mesh=name,material=name,
                      pos=f'{center[0]} {center[1]} {z}',contype='0',conaffinity='0',group='0')
    xml=args.output/'reference-scene.xml'
    ET.ElementTree(root).write(xml,encoding='utf-8')
    model=mujoco.MjModel.from_xml_path(str(xml.resolve()))
    data=mujoco.MjData(model)
    names=[f'{c}{r}' for r in range(1,9) for c in 'abcdefgh']
    camera=make_camera(settings)
    records=[]
    with mujoco.Renderer(model,height=height,width=width) as renderer:
        arrangements = ('empty', 'initial', 'offset', 'relocated') if args.evaluate_foreground else ('initial','empty','offset')
        for arrangement in arrangements:
            mujoco.mj_resetData(model,data)
            data.qpos[model.jnt_qposadr[model.joint('joint_z_axis_arm1').id]]=.12
            addresses = {}
            for i,piece in enumerate(manifest['pieces']):
                body=model.body(piece['name']).id
                adr=model.jnt_qposadr[model.body_jntadr[body]]
                if arrangement=='empty': data.qpos[adr+2]=-10
                if arrangement=='offset': data.qpos[adr:adr+2]+=[.004*(-1)**i,.003*(-1)**(i//2)]
                if arrangement == 'relocated':
                    if piece['initial_square'] not in ('e2', 'd7'):
                        data.qpos[adr+2] = -10
                        continue
                    target = 'f4' if piece['initial_square'] == 'e2' else 'b5'
                    file, rank = target
                    data.qpos[adr:adr+2] = board[:2] + np.array(
                        [ord(file)-ord('a')-3.5, int(rank)-4.5]) * side/8 + [.004, -.003]
                else:
                    target = piece['initial_square']
                if arrangement != 'empty':
                    addresses[target] = body
            mujoco.mj_forward(model,data)
            truth = {square: data.xpos[body, :2].copy() for square, body in addresses.items()}
            points=[]
            for name in names:
                g=model.geom('square_'+name).id
                pt=data.geom_xpos[g].copy(); pt[2]+=model.geom_size[g,2]; points.append(pt)
            for azimuth in (args.azimuths or [settings['azimuth']]):
                for elevation in (args.elevations or [settings['elevation']]):
                    camera.azimuth=azimuth; camera.elevation=elevation
                    renderer.update_scene(data,camera=camera)
                    rgb=renderer.render().copy()
                    case=f'{arrangement}-{azimuth:g}-{abs(elevation):g}'
                    image=args.output/f'{case}.png'; Image.fromarray(rgb).save(image)
                    output=args.output/case
                    command = [str(args.executable.resolve()), str(image.resolve()), str(output.resolve()),
                               '--reference', str(layout_path.resolve())]
                    if args.evaluate_foreground:
                        empty = args.output/f'empty-{azimuth:g}-{abs(elevation):g}.png'
                        command.extend(['--empty-board', str(empty.resolve())])
                    subprocess.run(command, check=True)
                    obs=json.loads((output/'observation.json').read_text())
                    if args.save_evaluator:
                        evaluator = dict(
                            source='MuJoCo ground truth; evaluation only',
                            image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                            squares=names, square_pitch_m=side/8,
                            projected_centers_px=project(
                                np.array(points), renderer.scene.camera, width, height).tolist(),
                            canonical_centers_px=[
                                [(c+.5)*100, (7-r+.5)*100]
                                for r in range(8) for c in range(8)],
                            camera=dict(lookat=settings["lookat"], distance_m=settings["distance"],
                                        azimuth=azimuth, elevation=elevation,
                                        image_size=[width, height],
                                        fovy_degrees=float(model.vis.global_.fovy)),
                            candidate_truth_colors=[
                                next((piece['color'] for piece in manifest['pieces']
                                      if addresses.get(name) == model.body(piece['name']).id),
                                     'empty') for name in names])
                        (args.output/f'evaluator-only-{case}.json').write_text(
                            json.dumps(evaluator, indent=2), encoding='utf-8')
                    result=dict(case=case,orientation=obs['orientation'],detected=obs['homography'] is not None,
                                image_sha256=hashlib.sha256(image.read_bytes()).hexdigest())
                    if result['detected']:
                        pixels=project(np.array(points),renderer.scene.camera,width,height)
                        transformed=np.column_stack((pixels,np.ones(64)))@np.array(obs['homography']).T
                        transformed=transformed[:,:2]/transformed[:,2:]
                        expected=np.array([(c+.5,7-r+.5) for r in range(8) for c in range(8)])*100
                        error=np.linalg.norm(transformed-expected,axis=1)/100*side/8*1000
                        result.update(mean_error_mm=float(error.mean()),max_error_mm=float(error.max()),
                                      correct_squares=int(np.sum(np.all(transformed//100==expected//100,axis=1))))
                    if args.evaluate_foreground:
                        result['foreground_status'] = obs['foreground_status']
                        result['foreground'] = foreground_metrics(obs, truth, board, side)
                        result['empty_board_image_id'] = obs['empty_board_image_id']
                    records.append(result)
    report=dict(schema=1,mujoco_version=mujoco.__version__,image_size=[width,height],camera_distance_m=settings["distance"],
                camera_lookat=settings["lookat"], model_fovy_degrees=float(model.vis.global_.fovy),
                evaluator_export=args.save_evaluator,
                executable_sha256=hashlib.sha256(args.executable.read_bytes()).hexdigest(),layout_provenance=layout['provenance'],geometry_only=not args.evaluate_foreground,
                layout_sha256=hashlib.sha256(layout_path.read_bytes()).hexdigest(),
                source_model_sha256=hashlib.sha256((args.bundle/'model.xml').read_bytes()).hexdigest(),results=records)
    (args.output/'report.json').write_text(json.dumps(report,indent=2))
    print(args.output/'report.json')


if __name__=='__main__': main()
