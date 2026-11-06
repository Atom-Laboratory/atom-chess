"""C++ MotionPlanner/IK adapter derived from static model geometry."""
import ctypes
from pathlib import Path

import mujoco
import numpy as np

PHASES = ('APPROACH_SOURCE', 'LOWER_TO_SOURCE', 'GRASP_PIECE', 'LIFT_PIECE',
          'APPROACH_TARGET', 'LOWER_TO_TARGET', 'RELEASE_PIECE', 'RETRACT')
ACTOR_PHASES = ('APPROACH', 'APPROACH', 'GRASP', 'LIFT', 'TRANSPORT', 'PLACE', 'RELEASE', 'RETREAT')


class NativeMotion:
    def __init__(self, library, sim):
        self.library_path = Path(library).resolve(strict=True)
        self.native = ctypes.CDLL(str(self.library_path))
        pointer = ctypes.POINTER(ctypes.c_double)
        self.native.acmotion_error.restype = ctypes.c_char_p
        self.native.acmotion_plan.argtypes = [pointer, pointer, ctypes.c_double, ctypes.c_double, pointer]
        self.native.acmotion_solve.argtypes = [pointer, pointer, ctypes.c_int, pointer]
        if self.native.acmotion_version() != 1:
            raise ValueError('Incompatible motion ABI')
        scratch = mujoco.MjData(sim.model)
        scratch.qpos[sim.qadr] = 0
        mujoco.mj_forward(sim.model, scratch)
        shoulder = scratch.xanchor[sim.joint_ids[0]]
        elbow = scratch.xanchor[sim.joint_ids[2]]
        tool = scratch.site('grasp_center').xpos
        first = elbow[:2]-shoulder[:2]
        second = tool[:2]-elbow[:2]
        if first[0] <= 0 or abs(first[1]) > 1e-8:
            raise ValueError('Unsupported neutral planar base rotation')
        offset = np.arctan2(second[1], second[0])
        self.geometry = np.array([
            np.linalg.norm(first)*1000, np.linalg.norm(second)*1000,
            sim.lower[0], sim.upper[0], sim.lower[2]+offset, sim.upper[2]+offset,
            sim.lower[1]*1000, sim.upper[1]*1000, offset,
            shoulder[0]*1000, shoulder[1]*1000, tool[2]*1000,
            sim.lower[3], sim.upper[3]], dtype=np.float64)
        # Verify the derived mapping on explicit robot configurations, without piece poses.
        for pose in ([.2, .05, -.5, 0, 0], [-.3, .1, .5, 0, 0]):
            scratch.qpos[sim.qadr] = pose
            mujoco.mj_forward(sim.model, scratch)
            xyz = scratch.site('grasp_center').xpos.copy()
            solved = self.solve(xyz, 0)
            scratch.qpos[sim.qadr] = solved
            mujoco.mj_forward(sim.model, scratch)
            if np.linalg.norm(scratch.site('grasp_center').xpos-xyz) > 1e-6:
                raise ValueError('Native IK/scene mapping mismatch')

    @staticmethod
    def pointer(value):
        return value.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

    def _check(self, status):
        if status:
            raise ValueError(self.native.acmotion_error().decode('utf-8'))

    def solve(self, xyz, opening):
        low, high = self.geometry[12:14]
        pose = np.array([*(np.asarray(xyz)*1000), (opening-low)/(high-low)*100], dtype=np.float64)
        output = np.empty(5, dtype=np.float64)
        self._check(self.native.acmotion_solve(self.pointer(self.geometry), self.pointer(pose),
                                              1, self.pointer(output)))
        return output

    def plan(self, source, target, safe_z, pick_z):
        source = np.asarray(source[:2], dtype=np.float64)*1000
        target = np.asarray(target[:2], dtype=np.float64)*1000
        poses = np.empty((8, 4), dtype=np.float64)
        self._check(self.native.acmotion_plan(self.pointer(source), self.pointer(target),
                                             safe_z*1000, pick_z*1000, self.pointer(poses)))
        poses[:, :3] /= 1000
        return poses
