"""Experimental interactive profile; synthetic physics, not CAD calibration."""
import xml.etree.ElementTree as ET


def configure(root, metadata, profile):
    profile.update(name='interactive-gravity-v1', gravity=[0, 0, -9.81], contacts=True,
                   collision_model='robot convex hulls vs static environment; no self collision',
                   gripper_model='independent parallel slides, not the Fusion linkage')
    root.find('option').set('gravity', '0 0 -9.81')
    root.find('option/flag').set('contact', 'enable')
    visual = root.find('visual')
    ET.SubElement(visual, 'map', znear='.001', zfar='20')
    ET.SubElement(visual, 'quality', shadowsize='2048', offsamples='4')
    ET.SubElement(visual, 'headlight', ambient='.45 .45 .45', diffuse='.6 .6 .6')
    world = root.find('worldbody')
    # Environment collision is enabled on existing primitives. Static pieces
    # remain anchored; dynamic chess manipulation is a separate model change.
    for geom in world.findall('./geom') + world.findall('./body[@name="chessboard"]//geom'):
        if geom.get('name', '').startswith('square_'):
            continue  # One board collider avoids seams between 64 tiles.
        geom.set('contype', '2')
        geom.set('conaffinity', '1')
        geom.set('friction', '.8 .01 .001')
    arm = root.find('.//body[@name="arm2_link"]')
    actuators = root.find('actuator')
    for index, (part, direction) in enumerate((('gripper_hand1', '0 0 1'),
                                               ('gripper_hand2', '0 0 -1'))):
        geom = arm.find(f'geom[@name="{part}_visual"]')
        arm.remove(geom)
        finger = ET.SubElement(arm, 'body', name=part+'_moving')
        ET.SubElement(finger, 'inertial', pos='.11 .03 .09', mass='.03',
                      diaginertia='.00005 .00005 .00005')
        name = 'finger_'+str(index+1)
        ET.SubElement(finger, 'joint', name=name, type='slide', axis=direction,
                      range='-.01 .02', damping='2', armature='.001')
        finger.append(geom)
        ET.SubElement(actuators, 'position', name=name+'_position', joint=name,
                      kp='150', kv='5', ctrlrange='-.01 .02', forcerange='-8 8')
        metadata.append(dict(name=name, kind='prismatic', lower=-.01, upper=.02, velocity=.025))
    for body in world.iter('body'):
        for i, geom in enumerate(list(body.findall('geom'))):
            if geom.get('type') != 'mesh':
                continue
            # Separate invisible convex collision mesh from visual triangles.
            attributes = dict(geom.attrib)
            attributes.update(name=body.get('name')+'_collision_'+str(i),
                              group='3', rgba='0 0 0 0', contype='1', conaffinity='2',
                              friction='.8 .01 .001', solref='.02 1')
            ET.SubElement(body, 'geom', **attributes)
    # A stronger experimental vertical servo holds the synthetic load against gravity.
    for actuator in list(actuators)[:3]:
        actuator.set('kp', '500')
        actuator.set('kv', '30')
    profile['actuator_kp'] = 500.
    profile['actuator_kv'] = 30.
    return dict(name='interactive-chess-v4', gripper_visual_only=False,
                gripper_calibrated=False, self_collision=False,
                camera=dict(lookat=[.20, -.08, .20], distance=1.35, azimuth=135, elevation=-25))
