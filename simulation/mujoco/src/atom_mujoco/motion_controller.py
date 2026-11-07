"""MuJoCo low-level position execution; contains no chess or task planning."""
import numpy as np


class MotionController:
    def __init__(self, simulation):
        self.sim = simulation

    def step(self, desired, *, stop_when=None):
        sim = self.sim
        command = sim.validate(desired).copy()
        # Model-based bias feedforward for the three arm position actuators.
        # This compensates simulated gravity sag; it is not hardware calibration.
        gains = sim.model.actuator_gainprm[:3, 0]
        if np.any(gains <= 0):
            raise ValueError('Positive arm servo gains required')
        command[:3] += sim.data.qfrc_bias[sim.vadr[:3]] / gains
        command = np.clip(command, sim.lower, sim.upper)
        if stop_when is not None:
            return sim.advance(command, stop_when=stop_when)
        return sim.advance(command)
