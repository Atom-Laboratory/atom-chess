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
        self.sim = sim
        self.has_wrist = "wrist_joint" in sim.names
        self.default_wrist = float((sim.lower[-1]+sim.upper[-1])/2) if self.has_wrist else None
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
            scratch.qpos[sim.qadr] = [*pose, np.pi] if self.has_wrist else pose
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

    def solve(self, xyz, opening, wrist=None, *, elbow_down=True):
        geometry = self.geometry.copy()
        if self.has_wrist:
            wrist = self.default_wrist if wrist is None else float(wrist)
            if not np.isfinite(wrist) or not self.sim.lower[-1] <= wrist <= self.sim.upper[-1]:
                raise ValueError('Wrist outside bounded revolution')
            scratch = mujoco.MjData(self.sim.model)
            scratch.qpos[self.sim.qadr] = 0
            scratch.qpos[self.sim.qadr[-1]] = wrist
            mujoco.mj_forward(self.sim.model, scratch)
            elbow = scratch.xanchor[self.sim.joint_ids[2]]
            tool = scratch.site('grasp_center').xpos
            second = tool[:2]-elbow[:2]
            offset = np.arctan2(second[1], second[0])
            geometry[1] = np.linalg.norm(second)*1000
            geometry[4:6] = [self.sim.lower[2]+offset, self.sim.upper[2]+offset]
            geometry[8] = offset
            geometry[11] = tool[2]*1000
        elif wrist is not None:
            raise ValueError('Wrist target requires a wrist model')
        low, high = self.geometry[12:14]
        pose = np.array([*(np.asarray(xyz)*1000), (opening-low)/(high-low)*100], dtype=np.float64)
        output = np.empty(5, dtype=np.float64)
        self._check(self.native.acmotion_solve(self.pointer(geometry), self.pointer(pose),
                                              int(elbow_down), self.pointer(output)))
        return np.append(output, wrist) if self.has_wrist else output

    def plan(self, source, target, safe_z, pick_z):
        source = np.asarray(source[:2], dtype=np.float64)*1000
        target = np.asarray(target[:2], dtype=np.float64)*1000
        poses = np.empty((8, 4), dtype=np.float64)
        self._check(self.native.acmotion_plan(self.pointer(source), self.pointer(target),
                                             safe_z*1000, pick_z*1000, self.pointer(poses)))
        poses[:, :3] /= 1000
        return poses
