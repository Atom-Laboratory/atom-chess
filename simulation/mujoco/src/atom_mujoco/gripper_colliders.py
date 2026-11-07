"""Build the explicit full-gripper profile from preserved convex mesh assets."""
import hashlib
import json
import xml.etree.ElementTree as ET


def add_full_gripper(root, mesh_bytes, mesh_directory):
    directory = mesh_directory/'gripper_collision'
    manifest = json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    assets = root.find('asset')
    count = 0
    for part, record in manifest.items():
        digest = hashlib.sha256((mesh_directory/(part+'.stl')).read_bytes()).hexdigest()
        if digest != record['source_sha256']:
            raise ValueError('Gripper decomposition source differs from visual mesh')
        for body in root.iter('body'):
            visual = body.find(f"geom[@name='{part}_visual']")
            if visual is not None:
                break
        else:
            raise ValueError('Missing gripper visual for collision attachment')
        for filename in record['hulls']:
            mesh_name = 'collision_'+filename.removesuffix('.obj')
            mesh_bytes[filename] = (directory/filename).read_bytes()
            ET.SubElement(assets, 'mesh', name=mesh_name, file=filename, scale='.001 .001 .001')
            ET.SubElement(body, 'geom', name=mesh_name+'_collision_hull',
                          type='mesh', mesh=mesh_name, pos=visual.get('pos', '0 0 0'),
                          quat=visual.get('quat', '1 0 0 0'), group='3', rgba='0 0 0 0',
                          contype='1', conaffinity='6', density='0', condim='4',
                          friction='1.2 .01 .001', solref='.01 1')
            count += 1
    return count
