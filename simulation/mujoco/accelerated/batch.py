"""Complete integration-state batch contract; Warp is an optional backend."""
from dataclasses import dataclass

import mujoco
import numpy as np


SIGNATURE = int(mujoco.mjtState.mjSTATE_INTEGRATION)


def pack(model, states):
    result = np.empty((len(states),mujoco.mj_stateSize(model,SIGNATURE)))
    for index,data in enumerate(states): mujoco.mj_getState(model,data,result[index],SIGNATURE)
    return result


def checked_states(model, states, worlds):
    states = np.asarray(states,dtype=np.float64)
    if states.shape != (worlds,mujoco.mj_stateSize(model,SIGNATURE)) or not np.isfinite(states).all():
        raise ValueError('Complete finite integration state required for every world')
    return states


def checked_active(active, worlds):
    if active is None: return np.ones(worlds,dtype=bool)
    active = np.asarray(active)
    if active.shape != (worlds,) or active.dtype != np.bool_:
        raise ValueError('Boolean reset mask required for every world')
    return active


@dataclass(frozen=True)
class Limits:
    worlds: int = 1
    max_worlds: int = 64
    max_gpu_mib: int = 2048
    nconmax: int = 64
    njmax: int = 256

    def __post_init__(self):
        values=(self.worlds,self.max_worlds,self.max_gpu_mib,self.nconmax,self.njmax)
        if any(type(value) is not int or value <= 0 for value in values):
            raise ValueError('Positive integer resource limits required')
        if not self.worlds <= self.max_worlds <= 1024 or not 128 <= self.max_gpu_mib <= 8192:
            raise ValueError('World/GPU allocation budget exceeded')


class CpuBatch:
    def __init__(self, model, limits):
        self.model,self.limits=model,limits
        self.data=[mujoco.MjData(model) for _ in range(limits.worlds)]

    def reset(self, states, active=None):
        states=checked_states(self.model,states,self.limits.worlds)
        active=checked_active(active,self.limits.worlds)
        for index in np.flatnonzero(active): mujoco.mj_setState(self.model,self.data[index],states[index],SIGNATURE)

    def state(self): return pack(self.model,self.data)

    def forward(self):
        for data in self.data: mujoco.mj_forward(self.model,data)

    def step(self, controls=None):
        if controls is not None:
            controls=np.asarray(controls)
            if controls.shape != (self.limits.worlds,self.model.nu) or not np.isfinite(controls).all():
                raise ValueError('Finite batched actuator controls required')
            for index,data in enumerate(self.data): data.ctrl[:]=controls[index]
        for data in self.data: mujoco.mj_step(self.model,data)

    def arrays(self,names):
        return {name:np.stack([getattr(data,name).copy() for data in self.data]) for name in names}


class WarpBatch:
    def __init__(self, model, limits, *, device='cuda:0'):
        import mujoco_warp as mjw
        import warp as wp
        self.model,self.limits,self.mjw,self.wp=model,limits,mjw,wp
        wp.init();self.device=wp.get_device(device)
        if not self.device.is_cuda: raise ValueError('Explicit CUDA backend required')
        if self.device.free_memory < (limits.max_gpu_mib+1024)*1024**2:
            raise MemoryError('GPU budget plus 1 GiB free-device headroom unavailable')
        with wp.ScopedDevice(self.device):
            self.gpu_model=mjw.put_model(model)
            self.data=mjw.make_data(model,nworld=limits.worlds,nconmax=limits.nconmax,njmax=limits.njmax)
        self.check_memory()

    def check_memory(self):
        allocated=self.wp.get_mempool_used_mem_current(self.device)
        if allocated > self.limits.max_gpu_mib*1024**2:
            raise MemoryError(f'Warp allocation pool {allocated} exceeds declared budget')
        return int(allocated)

    def reset(self,states,active=None):
        states=checked_states(self.model,states,self.limits.worlds)
        active=checked_active(active,self.limits.worlds)
        with self.wp.ScopedDevice(self.device):
            self.mjw.set_state(self.gpu_model,self.data,self.wp.array(states.astype(np.float32)),
                               SIGNATURE,active=self.wp.array(active,dtype=self.wp.bool))

    def state(self):
        with self.wp.ScopedDevice(self.device):
            result=self.wp.empty((self.limits.worlds,mujoco.mj_stateSize(self.model,SIGNATURE)),dtype=self.wp.float32)
            self.mjw.get_state(self.gpu_model,self.data,result,SIGNATURE)
        return result.numpy()

    def forward(self):
        with self.wp.ScopedDevice(self.device): self.mjw.forward(self.gpu_model,self.data)

    def step(self,controls=None):
        with self.wp.ScopedDevice(self.device):
            if controls is not None:
                controls=np.asarray(controls,dtype=np.float32)
                if controls.shape != (self.limits.worlds,self.model.nu) or not np.isfinite(controls).all():
                    raise ValueError('Finite batched actuator controls required')
                self.wp.copy(self.data.ctrl,self.wp.array(controls))
            self.mjw.step(self.gpu_model,self.data)

    def arrays(self,names):return {name:getattr(self.data,name).numpy().copy() for name in names}

    def health(self):
        overflow=self.data.overflow.numpy()
        if np.any(overflow):raise RuntimeError(f'GPU overflow/convergence flags: {overflow.tolist()}')
        nacon=int(self.data.nacon.numpy()[0]);nefc=self.data.nefc.numpy()
        if nacon > self.data.naconmax or np.any(nefc > self.data.njmax):raise RuntimeError('GPU contact/constraint capacity exceeded')
        if not all(np.isfinite(value).all() for value in self.arrays(('qpos','qvel')).values()):
            raise RuntimeError('Nonfinite GPU state')
        return dict(overflow=overflow.tolist(),nacon=nacon,nefc=nefc.tolist(),
                    naconmax=self.data.naconmax,njmax=self.data.njmax,warp_pool_bytes=self.check_memory())
