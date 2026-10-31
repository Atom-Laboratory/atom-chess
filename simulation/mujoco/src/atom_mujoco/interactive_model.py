"""Experimental interactive profile; synthetic physics, not CAD calibration."""
import xml.etree.ElementTree as ET


def configure(root, metadata, profile):
    profile.update(name='interactive-gravity-v2', gravity=[0, 0, -9.81], contacts=True,
                   collision_model='robot convex hulls vs static environment; no self collision',
                   gripper_model='coupled parallel slides with fingertip pads; not the Fusion linkage')
    root.find('option').set('gravity', '0 0 -9.81')
    root.find('option/flag').set('contact', 'enable')
    visual = root.find('visual')
    ET.SubElement(visual, 'map', znear='.001', zfar='20')
    ET.SubElement(visual, 'quality', shadowsize='2048', offsamples='4')
    ET.SubElement(visual, 'headlight', ambient='.45 .45 .45', diffuse='.6 .6 .6')
    world = root.find('worldbody')
    board = world.find('body[@name="chessboard"]')
    # Free joints must be world children. Preserve original board-relative poses.
    board_position = [float(x) for x in board.get('pos').split()]
    for piece in list(board.findall('body')):
        board.remove(piece)
        world.append(piece)
        piece.set('pos', ' '.join(str(a+float(b)) for a,b in zip(board_position, piece.get('pos').split())))
        ET.SubElement(piece, 'freejoint', name=piece.get('name')+'_free')
        ET.SubElement(piece, 'inertial', pos='0 0 .015', mass='.02',
                      diaginertia='.000004 .000004 .000002')
        for geom in piece.findall('geom'):
            geom.set('contype', '4')
            geom.set('conaffinity', '7')
            geom.set('condim', '4')
            geom.set('friction', '1.2 .01 .001')
            geom.set('solref', '.01 1')
    # Environment collision is enabled on existing primitives. Static pieces
    # remain anchored; dynamic chess manipulation is a separate model change.
    for geom in world.findall('./geom') + world.findall('./body[@name="chessboard"]//geom'):
        if geom.get('name', '').startswith('square_'):
            continue  # One board collider avoids seams between 64 tiles.
        geom.set('contype', '2')
        geom.set('conaffinity', '5')
        geom.set('friction', '.8 .01 .001')
    arm = root.find('.//body[@name="arm2_link"]')
    actuators = root.find('actuator')
    equality = ET.SubElement(root, 'equality')
    ET.SubElement(equality, 'joint', joint1='finger_1', joint2='finger_2',
                  polycoef='0 1 0 0 0', solref='.002 1')
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
        # Mesh convex hulls fill gaps in the CAD finger and produce false contact.
        # Use a localized, explicit pad proxy at each inward-facing fingertip.
        ET.SubElement(finger, 'geom', name=name+'_pad', type='box',
                      pos='.113 -.009 '+('.105' if index == 0 else '.076'),
                      size='.015 .008 .003', rgba='.15 .15 .15 1',
                      contype='1', conaffinity='6', condim='4',
                      friction='1.2 .01 .001', solref='.01 1')
        ET.SubElement(actuators, 'position', name=name+'_position', joint=name,
                      kp='150', kv='5', ctrlrange='-.01 .02', forcerange='-8 8')
        metadata.append(dict(name=name, kind='prismatic', lower=-.01, upper=.02, velocity=.025))
    for body in world.iter('body'):
        for i, geom in enumerate(list(body.findall('geom'))):
            if geom.get('type') != 'mesh':
                continue
            if body.get('name', '').startswith('gripper_hand'):
                continue
            # Separate invisible convex collision mesh from visual triangles.
            attributes = dict(geom.attrib)
            attributes.update(name=body.get('name')+'_collision_'+str(i),
                              group='3', rgba='0 0 0 0', contype='1', conaffinity='6',
                              friction='.8 .01 .001', solref='.02 1')
            ET.SubElement(body, 'geom', **attributes)
    # A stronger experimental vertical servo holds the synthetic load against gravity.
    for actuator in list(actuators)[:3]:
        actuator.set('kp', '500')
        actuator.set('kv', '30')
    profile['actuator_kp'] = 500.
    profile['actuator_kv'] = 30.
    ET.SubElement(arm, 'site', name='grasp_center', pos='.113 -.009 .0905',
                  size='.002', rgba='0 0 0 0')
    return dict(name='interactive-chess-v5', gripper_visual_only=False,
                gripper_calibrated=False, self_collision=False,
                camera=dict(lookat=[.20, -.08, .20], distance=1.35, azimuth=135, elevation=-25))
