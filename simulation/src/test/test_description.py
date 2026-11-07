"""Validate the installed description without claiming mechanical accuracy."""

import math
from pathlib import Path
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
import xacro


def test_description_is_a_connected_tree_with_resolvable_meshes():
    share = Path(get_package_share_directory('atom_description'))
    robot = ET.fromstring(xacro.process_file(str(share / 'urdf/atom.urdf.xacro')).toxml())
    links = [link.attrib['name'] for link in robot.findall('link')]
    joints = robot.findall('joint')
    assert len(links) == len(set(links)), 'Duplicate link names'
    assert len(joints) == len({joint.attrib['name'] for joint in joints})
    parents = {}
    for joint in joints:
        parent = joint.find('parent').attrib['link']
        child = joint.find('child').attrib['link']
        assert parent in links and child in links
        assert child not in parents, 'A link has multiple parent joints'
        parents[child] = parent
        if joint.attrib['type'] in ('revolute', 'prismatic'):
            limit = joint.find('limit')
            assert limit is not None, 'Moving joint lacks limits'
            values = {key: float(limit.attrib[key])
                      for key in ('lower', 'upper', 'effort', 'velocity')}
            assert all(math.isfinite(value) for value in values.values())
            assert values['lower'] < values['upper']
            assert values['effort'] > 0 and values['velocity'] > 0
            axis = [float(value) for value in joint.find('axis').attrib['xyz'].split()]
            assert len(axis) == 3
            assert math.isclose(sum(value * value for value in axis), 1.0, abs_tol=1e-9)
    roots = set(links) - set(parents)
    assert roots == {'world'}, f'Unexpected roots: {roots}'
    for link in links:
        visited = set()
        current = link
        while current in parents:
            assert current not in visited, 'Cycle in link tree'
            visited.add(current)
            current = parents[current]
        assert current == 'world', f'Disconnected link: {link}'
    meshes = robot.findall('.//mesh')
    assert meshes, 'Description has no visual meshes'
    for mesh in meshes:
        uri = mesh.attrib['filename']
        assert uri.startswith('package://'), f'Nonportable mesh path: {uri}'
        package, relative = uri.removeprefix('package://').split('/', 1)
        resource = Path(get_package_share_directory(package)) / relative
        assert resource.is_file() and resource.stat().st_size > 84, uri
        scale = [float(value) for value in mesh.attrib.get('scale', '1 1 1').split()]
        assert len(scale) == 3 and all(math.isfinite(v) and v > 0 for v in scale)


def test_rviz_configuration_is_installed():
    share = Path(get_package_share_directory('atom_description'))
    assert (share / 'rviz/atom.rviz').is_file()
