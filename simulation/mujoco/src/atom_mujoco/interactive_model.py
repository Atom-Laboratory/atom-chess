"""Experimental interactive profile; synthetic physics, not CAD calibration."""
import xml.etree.ElementTree as ET
import math
import numpy as np

# Shared planar face normals and fingertip projections from the exported STL.
# Values are geometric evidence in the assembly frame, not servo calibration.
RAIL_AXIS = np.array([-.60609, 0., .79539])
RAIL_AXIS /= np.linalg.norm(RAIL_AXIS)
RAIL_TANGENT = np.cross([0, 1, 0], RAIL_AXIS)
TIP_INNER_PROJECTIONS_MM = (-130.07879, -178.17435)
TIP_TANGENT_MM = 351.30023
FINGER_LOWER = -.021
FINGER_UPPER = 0.
WRIST_PIVOT = (.112837063, .13339837, .090329263)
WRIST_RANGE = (0., math.tau)


def pad_center(index):
    projection = TIP_INNER_PROJECTIONS_MM[index]/1000
    projection += -.0015 if index == 0 else .0015
    position = RAIL_AXIS*projection + RAIL_TANGENT*(TIP_TANGENT_MM/1000)
    position += [-.26, -.018, 0]
    return position


def vector_text(value):
    return ' '.join(str(float(x)) for x in value)


def configure(root, metadata, profile, *, wrist=False):
    profile.update(name='interactive-gravity-v3', gravity=[0, 0, -9.81], contacts=True,
                   collision_model='robot convex hulls vs static environment; no self collision',
                   gripper_model='mesh-aligned coupled slides; servo linkage not reconstructed',
                   gripper_geometry=dict(rail_axis_in_arm2=RAIL_AXIS.tolist(),
                       inner_face_gap_at_zero_m=.04809556,
                       finger_range_m=[FINGER_LOWER, FINGER_UPPER]))
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
    # Enable environment contacts; pieces are independent free bodies above.
    for geom in world.findall('./geom') + world.findall('./body[@name="chessboard"]//geom'):
        if geom.get('name', '').startswith('square_'):
            continue  # One board collider avoids seams between 64 tiles.
        geom.set('contype', '2')
        geom.set('conaffinity', '5')
        geom.set('friction', '.8 .01 .001')
    arm = root.find('.//body[@name="arm2_link"]')
    actuators = root.find('actuator')
    gripper = arm
    if wrist:
        profile['name'] = 'interactive-wrist-v1'
        gripper = ET.SubElement(arm, 'body', name='gripper_wrist')
        ET.SubElement(gripper, 'inertial', pos=vector_text(WRIST_PIVOT), mass='.08',
                      diaginertia='.0001 .0001 .0001')
        ET.SubElement(gripper, 'joint', name='wrist_joint', type='hinge',
                      pos=vector_text(WRIST_PIVOT), axis='0 1 0', limited='true',
                      range=vector_text(WRIST_RANGE), damping='1', armature='.01')
        back = arm.find('geom[@name="gripper_back_visual"]')
        arm.remove(back)
        gripper.append(back)
    equality = ET.SubElement(root, 'equality')
    ET.SubElement(equality, 'joint', joint1='finger_1', joint2='finger_2',
                  polycoef='0 1 0 0 0', solref='.002 1')
    for index, part in enumerate(('gripper_hand1', 'gripper_hand2')):
        direction = vector_text(RAIL_AXIS if index == 0 else -RAIL_AXIS)
        geom = arm.find(f'geom[@name="{part}_visual"]')
        arm.remove(geom)
        finger = ET.SubElement(gripper, 'body', name=part+'_moving')
        ET.SubElement(finger, 'inertial', pos='.11 .03 .09', mass='.03',
                      diaginertia='.00005 .00005 .00005')
        name = 'finger_'+str(index+1)
        ET.SubElement(finger, 'joint', name=name, type='slide', axis=direction,
                      range=f'{FINGER_LOWER} {FINGER_UPPER}', damping='2', armature='.001')
        finger.append(geom)
        # Mesh convex hulls fill gaps in the CAD finger and produce false contact.
        # Use a localized, explicit pad proxy at each inward-facing fingertip.
        ET.SubElement(finger, 'geom', name=name+'_pad', type='box',
                      pos=vector_text(pad_center(index)),
                      euler=f'0 {math.atan2(RAIL_AXIS[0], RAIL_AXIS[2])} 0',
                      size='.012 .006 .0015', rgba='.15 .15 .15 1',
                      contype='1', conaffinity='6', condim='4',
                      friction='1.2 .01 .001', solref='.01 1')
        ET.SubElement(actuators, 'position', name=name+'_position', joint=name,
                      kp='150', kv='5', ctrlrange=f'{FINGER_LOWER} {FINGER_UPPER}', forcerange='-8 8')
        metadata.append(dict(name=name, kind='prismatic', lower=FINGER_LOWER, upper=FINGER_UPPER, velocity=.025))
    if wrist:
        ET.SubElement(actuators, 'position', name='wrist_position', joint='wrist_joint',
                      kp='50', kv='2', ctrllimited='true', ctrlrange=vector_text(WRIST_RANGE))
        metadata.append(dict(name='wrist_joint', kind='revolute', lower=WRIST_RANGE[0],
                             upper=WRIST_RANGE[1], velocity=math.pi))
    for body in world.iter('body'):
        for i, geom in enumerate(list(body.findall('geom'))):
            if geom.get('type') != 'mesh':
                continue
            if body.get('name', '').startswith('gripper_hand') or geom.get('name') == 'gripper_back_visual':
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
    ET.SubElement(gripper, 'site', name='grasp_center', pos=vector_text((pad_center(0)+pad_center(1))/2),
                  size='.002', rgba='0 0 0 0')
    return dict(name='interactive-wrist-v1' if wrist else 'interactive-chess-v6',
                gripper_visual_only=False,
                gripper_calibrated=False, self_collision=False,
                camera=dict(lookat=[.20, -.08, .20], distance=1.35, azimuth=135, elevation=-25))
