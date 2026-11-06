"""Render explicit experimental ArUco supports; native vision receives images/layout only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from PIL import Image
from validate_native_perception import project


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--executable',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    layout=json.loads((args.assets/'layout.json').read_text())
    manifest=json.loads((args.bundle/'manifest.json').read_text())
    side=manifest['scene']['square_size_m']*8
    if not np.isclose(side*1000,layout['board_side_mm']):
        raise ValueError('Reference layout must match scene board dimensions')
    root=ET.parse(args.bundle/'model.xml').getroot()
    for asset in root.findall('./asset/*'):
        if asset.get('file'): asset.set('file',str((args.bundle/asset.get('file')).resolve()))
    visual=root.find('./visual/global')
    visual.set('offwidth','1920'); visual.set('offheight','1440')
    assets=root.find('asset'); world=root.find('worldbody')
    board=np.array(manifest['scene']['board_center_m'])
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
    camera=mujoco.MjvCamera(); mujoco.mjv_defaultCamera(camera)
    camera.lookat[:]=board; camera.distance=1.05
    records=[]
    with mujoco.Renderer(model,height=1440,width=1920) as renderer:
        for arrangement in ('initial','empty','offset'):
            mujoco.mj_resetData(model,data)
            data.qpos[model.jnt_qposadr[model.joint('joint_z_axis_arm1').id]]=.12
            for i,piece in enumerate(manifest['pieces']):
                body=model.body(piece['name']).id
                adr=model.jnt_qposadr[model.body_jntadr[body]]
                if arrangement=='empty': data.qpos[adr+2]=-10
                if arrangement=='offset': data.qpos[adr:adr+2]+=[.004*(-1)**i,.003*(-1)**(i//2)]
            mujoco.mj_forward(model,data)
            points=[]
            for name in names:
                g=model.geom('square_'+name).id
                pt=data.geom_xpos[g].copy(); pt[2]+=model.geom_size[g,2]; points.append(pt)
            for azimuth in (265,270,275):
                for elevation in (-35,-45,-55):
                    camera.azimuth=azimuth; camera.elevation=elevation
                    renderer.update_scene(data,camera=camera)
                    rgb=renderer.render().copy()
                    case=f'{arrangement}-{azimuth}-{abs(elevation)}'
                    image=args.output/f'{case}.png'; Image.fromarray(rgb).save(image)
                    output=args.output/case
                    subprocess.run([str(args.executable.resolve()),str(image.resolve()),str(output.resolve()),
                                    '--reference',str((args.assets/'layout.json').resolve())],check=True)
                    obs=json.loads((output/'observation.json').read_text())
                    result=dict(case=case,orientation=obs['orientation'],detected=obs['homography'] is not None,
                                image_sha256=hashlib.sha256(image.read_bytes()).hexdigest())
                    if result['detected']:
                        pixels=project(np.array(points),renderer.scene.camera,1920,1440)
                        transformed=np.column_stack((pixels,np.ones(64)))@np.array(obs['homography']).T
                        transformed=transformed[:,:2]/transformed[:,2:]
                        expected=np.array([(c+.5,7-r+.5) for r in range(8) for c in range(8)])*100
                        error=np.linalg.norm(transformed-expected,axis=1)/100*side/8*1000
                        result.update(mean_error_mm=float(error.mean()),max_error_mm=float(error.max()),
                                      correct_squares=int(np.sum(np.all(transformed//100==expected//100,axis=1))))
                    records.append(result)
    report=dict(schema=1,mujoco_version=mujoco.__version__,image_size=[1920,1440],camera_distance_m=1.05,
                executable_sha256=hashlib.sha256(args.executable.read_bytes()).hexdigest(),layout_provenance=layout['provenance'],geometry_only=True,
                layout_sha256=hashlib.sha256((args.assets/'layout.json').read_bytes()).hexdigest(),
                source_model_sha256=hashlib.sha256((args.bundle/'model.xml').read_bytes()).hexdigest(),results=records)
    (args.output/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(records,indent=2))


if __name__=='__main__': main()
