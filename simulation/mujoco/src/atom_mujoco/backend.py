"""Reset/advance/observe API independent from ROS and future RL decisions."""
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np


class Simulation:
    def __init__(self, bundle):
        bundle = Path(bundle)
        self.manifest = json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
        if self.manifest['schema'] != 1 or self.manifest['profile']['name'] != 'uncalibrated-zero-gravity-v1':
            raise ValueError('Unsupported bundle schema/profile')
        for name, digest in dict(self.manifest['assets_sha256'], **{'model.xml': self.manifest['model_sha256']}).items():
            path = (bundle/name).resolve()
            if not path.is_relative_to(bundle.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('Bundle integrity check failed')
        self.model = mujoco.MjModel.from_xml_path(str((bundle/'model.xml').resolve()))
        self.data = mujoco.MjData(self.model)
        self.names = [j['name'] for j in self.manifest['joints']]
        self.lower = np.array([j['lower'] for j in self.manifest['joints']])
        self.upper = np.array([j['upper'] for j in self.manifest['joints']])
        self.speed = np.array([j['velocity'] for j in self.manifest['joints']])
        if self.model.nq != len(self.names) or self.model.nu != len(self.names):
            raise ValueError('Unsupported model dimensions')
        actual_names = [mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_JOINT, i)
                        for i in range(self.model.njnt)]
        if actual_names != self.names:
            raise ValueError('Model/manifest joint order mismatch')
        self.substeps = int(self.manifest['profile']['control_substeps'])
        if self.substeps <= 0:
            raise ValueError('Control substeps must be positive')
        self.dt = self.model.opt.timestep * self.substeps
        self.site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, 'arm2_frame')
        if self.site_id < 0:
            raise ValueError('Missing arm2_frame site')
        self.reset()

    def validate(self, position):
        value = np.array(position, dtype=float)
        if value.shape != self.lower.shape or not np.isfinite(value).all():
            raise ValueError('Expected one finite position per joint')
        if np.any(value < self.lower) or np.any(value > self.upper):
            raise ValueError('Position outside prototype joint limits')
        return value

    def reset(self, position=None, *, seed=None, randomize=False):
        if position is not None and randomize:
            raise ValueError('Choose explicit position or randomized reset')
        if randomize:
            rng = np.random.default_rng(seed)
            center = (self.lower+self.upper)/2
            half_width = (self.upper-self.lower)*.2
            position = rng.uniform(center-half_width, center+half_width)
        elif position is None:
            position = np.clip(np.zeros_like(self.lower), self.lower, self.upper)
        value = self.validate(position)
        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[:] = value
        self.reference = value.copy()
        self.target = value.copy()
        self.data.ctrl[:] = value
        mujoco.mj_forward(self.model, self.data)
        return self.observe()

    def advance(self, target):
        """One control interval of physics; target is SI joint position, not normalized action."""
        value = self.validate(target)  # Reject invalid input before changing state.
        self.target = value
        for _ in range(self.substeps):
            delta = self.speed * self.model.opt.timestep
            self.reference += np.clip(value-self.reference, -delta, delta)
            self.data.ctrl[:] = self.reference
            mujoco.mj_step(self.model, self.data)
        mujoco.mj_forward(self.model, self.data)
        if not np.isfinite(self.data.qpos).all() or not np.isfinite(self.data.qvel).all():
            raise RuntimeError('Nonfinite physics state; reset required')
        if np.any(self.data.warning.number):
            raise RuntimeError('MuJoCo warning; inspect model and reset')
        return self.observe()

    def observe(self):
        return dict(time_s=float(self.data.time), position=self.data.qpos.copy(),
                    velocity=self.data.qvel.copy(), reference=self.reference.copy(),
                    target=self.target.copy(), actuator_force=self.data.actuator_force.copy(),
                    arm2_position=self.data.site_xpos[self.site_id].copy(),
                    arm2_rotation=self.data.site_xmat[self.site_id].reshape(3, 3).copy(),
                    joint_limit_excess=np.maximum(0, np.maximum(self.lower-self.data.qpos, self.data.qpos-self.upper)),
                    tool_pose=(self.frame_pose('experimental_tool')
                               if self.manifest.get('experimental_tool_offset_m') is not None else None),
                    contacts=None, profile=self.manifest['profile']['name'])

    def frame_pose(self, site='arm2_frame'):
        """World position (m) and rotation matrix of a named site, not a calibrated TCP."""
        index = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, site)
        if index < 0:
            raise ValueError(f'Unknown site: {site}')
        return {'site': site, 'position_m': self.data.site_xpos[index].copy(),
                'rotation': self.data.site_xmat[index].reshape(3, 3).copy(),
                'tcp_calibrated': False}
