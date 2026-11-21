"""MuJoCo low-level position execution; contains no chess or task planning."""
import mujoco
import numpy as np


class MotionController:
    def __init__(self, simulation):
        self.sim = simulation
        self.scratch = mujoco.MjData(simulation.model)

    def command(self, desired):
        """Static model feedforward from issued coordinates, never live state."""
        sim = self.sim
        command = sim.validate(desired).copy()
        mujoco.mj_resetData(sim.model, self.scratch)
        self.scratch.qpos[sim.qadr] = command
        mujoco.mj_forward(sim.model, self.scratch)
        # Static gravity hypothesis only; this is not measured hardware force.
        gains = sim.model.actuator_gainprm[:3, 0]
        if np.any(gains <= 0):
            raise ValueError('Positive arm servo gains required')
        command[:3] += self.scratch.qfrc_bias[sim.vadr[:3]] / gains
        return np.clip(command, sim.lower, sim.upper)

    def step(self, desired, *, stop_when=None):
        sim = self.sim
        command = self.command(desired)
        if stop_when is not None:
            return sim.advance(command, stop_when=stop_when)
        return sim.advance(command)
