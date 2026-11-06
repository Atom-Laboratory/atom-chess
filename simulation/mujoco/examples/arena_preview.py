"""Inspect up to 100 ATOM stations in one static MuJoCo scene."""
import argparse
import copy
import math
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import mujoco
import mujoco.viewer
import numpy as np

from atom_mujoco.backend import Simulation
from atom_mujoco.controls import clean_view_options


def build_arena(bundle, arms, live=False):
    sim = Simulation(bundle)
    source = ET.parse(bundle/'model.xml').getroot()
    assets = ET.Element('asset')
    meshes = {}
    for index, asset in enumerate(source.findall('asset/mesh')):
        if asset.get('name').startswith('official_'):
            continue
        item = copy.deepcopy(asset)
        item.set('file', str((bundle/item.get('file')).resolve()))
        assets.append(item)
        meshes[index] = item.get('name')

    root = ET.Element('mujoco', model=f'ATOM Arena - {arms} stations')
    root.append(assets)
    visual = ET.SubElement(root, 'visual')
    ET.SubElement(visual, 'map', zfar='100')
    world = ET.SubElement(root, 'worldbody')
    ET.SubElement(world, 'geom', type='plane', size='0 0 .1', rgba='.23 .26 .30 1')
    columns = math.ceil(math.sqrt(arms))
    rows = math.ceil(arms/columns)
    spacing = .76

    def vector(values):
        return ' '.join(str(float(value)) for value in values)

    model, data = sim.model, sim.data
    mirrors = []
    for station in range(arms):
        x = (station % columns - (columns-1)/2)*spacing
        y = (station // columns - (rows-1)/2)*spacing
        body = ET.SubElement(world, 'body', pos=vector([x,y,0]))
        pose = sim.target.copy()
        pose[0] = .28*math.sin(station*.82)
        pose[2] = -.65 + .22*math.cos(station*.67)
        sim.reset(pose)
        for index in range(model.ngeom):
            name = model.geom(index).name
            kind = mujoco.mjtGeom(model.geom_type[index]).name.removeprefix('mjGEOM_').lower()
            if kind == 'plane' or name.endswith('_official_visual'):
                continue
            color = model.geom_rgba[index].copy()
            if color[3] == 0:
                if not name.startswith(('black_', 'white_')):
                    continue
                color = [.09,.10,.13,1] if name.startswith('black_') else [.92,.89,.78,1]
            if kind == 'mesh':
                mesh = meshes.get(int(model.geom_dataid[index]))
                if mesh is None:
                    continue
                attributes = {'mesh':mesh}
            elif kind in ('sphere','box','capsule','cylinder','ellipsoid'):
                size_count = {'sphere':1,'capsule':2,'cylinder':2}.get(kind,3)
                attributes = {'size':vector(model.geom_size[index,:size_count])}
            else:
                continue
            rotation = np.empty(4)
            mujoco.mju_mat2Quat(rotation,data.geom_xmat[index])
            parent = body
            if live and model.body_rootid[model.geom_bodyid[index]] != 0:
                name = f'mirror_{station}_{index}'
                parent = ET.SubElement(world, 'body', name=name, mocap='true', pos=vector([x,y,0]))
                mirrors.append((name, station, index, np.array([x,y,0]),
                                data.geom_xpos[index].copy(), data.geom_xmat[index].reshape(3,3).copy()))
            ET.SubElement(parent,'geom', type=kind, pos=vector(data.geom_xpos[index]),
                          quat=vector(rotation), rgba=vector(color),
                          contype='0', conaffinity='0', **attributes)
    arena = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding='unicode'))
    return arena, columns, mirrors


class LiveArena:
    def __init__(self, bundle, workers, source):
        self.model, columns, mirrors = build_arena(bundle, workers, live=True)
        self.data = mujoco.MjData(self.model)
        self.source = source
        self.scratch = mujoco.MjData(source)
        self.stations = [[] for _ in range(workers)]
        for name, station, index, offset, position, rotation in mirrors:
            slot = self.model.body(name).mocapid[0]
            self.stations[station].append((slot, index, offset, position, rotation.T))
        self.next_frame = 0.
        self.viewer = mujoco.viewer.launch_passive(
            self.model, self.data, show_left_ui=False, show_right_ui=False)
        with self.viewer.lock():
            self.viewer.cam.lookat[:] = [.2,0,.12]
            self.viewer.cam.distance = max(1.1, columns*.95)
            self.viewer.cam.azimuth = 125
            self.viewer.cam.elevation = -50
            clean_view_options(self.viewer.opt)

    @property
    def stopped(self):
        return not self.viewer.is_running()

    def update(self, infos):
        now = time.monotonic()
        if self.stopped or now < self.next_frame:
            return
        self.next_frame = now + .2
        with self.viewer.lock():
            for station, info in zip(self.stations, infos):
                self.scratch.qpos[:] = info['mirror_qpos']
                mujoco.mj_kinematics(self.source, self.scratch)
                for slot, index, offset, position, inverse_rotation in station:
                    rotation = self.scratch.geom_xmat[index].reshape(3,3) @ inverse_rotation
                    self.data.mocap_pos[slot] = offset + self.scratch.geom_xpos[index] - rotation @ position
                    mujoco.mju_mat2Quat(self.data.mocap_quat[slot], rotation.ravel())
            mujoco.mj_forward(self.model, self.data)
        self.viewer.sync(state_only=True)

    def close(self):
        self.viewer.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--arms', type=int, default=100)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.arms <= 100:
        parser.error('Choose between 1 and 100 stations')
    model, columns, _ = build_arena(args.bundle, args.arms)
    print(f'Compiled {args.arms} stations with {model.ngeom} visual geoms', flush=True)
    if args.check:
        return
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    with mujoco.viewer.launch_passive(model, data, show_left_ui=False, show_right_ui=False) as viewer:
        with viewer.lock():
            viewer.cam.lookat[:] = [.2,0,.12]
            viewer.cam.distance = max(1.1, columns*.95)
            viewer.cam.azimuth = 125
            viewer.cam.elevation = -50
            clean_view_options(viewer.opt)
            viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_STATIC] = True
            viewer.user_scn.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = False
        while viewer.is_running():
            viewer.sync(state_only=True)
            time.sleep(.04)


if __name__ == '__main__':
    main()
