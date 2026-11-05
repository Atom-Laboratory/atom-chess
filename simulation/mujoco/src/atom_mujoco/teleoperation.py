"""Held-key joint teleoperation through the existing motion controller."""
import math
import numpy as np


class ManualControl:
    DEFAULT_KEYS = {'left': (0, -1), 'right': (0, 1), 'up': (1, 1), 'down': (1, -1),
                    'prior': (2, -1), 'next': (2, 1), 'home': (3, 1), 'end': (3, -1)}

    def __init__(self, playground, keys=None, speed_fraction=.25):
        if not math.isfinite(speed_fraction) or not 0 < speed_fraction <= 1:
            raise ValueError('Speed fraction must be in (0, 1]')
        self.playground = playground
        self.keys = dict(self.DEFAULT_KEYS if keys is None else keys)
        for axis, sign in self.keys.values():
            if axis not in range(4) or sign not in (-1, 1):
                raise ValueError('Unsupported key mapping')
        self.speed_fraction = speed_fraction
        self.pressed = set()
        self.active = self.paused = self.stopped = False
        self.target = playground.sim.observe()['position'].copy()
        self.latest = None
        self.observation_error = None

    def enter(self):
        if any(op.status in ('pending', 'executing') for op in self.playground.physical.operations.values()):
            raise ValueError('Autonomous task owns the robot')
        if self.stopped:
            raise ValueError('Simulation stop is latched; reset required')
        self.active = True
        self.target = self.playground.sim.observe()['position'].copy()
        self.target[3:] = np.mean(self.target[3:])
        self.target = np.clip(self.target, self.playground.sim.lower, self.playground.sim.upper)

    def leave(self):
        self.pressed.clear()
        self.active = False

    def key(self, name, down):
        if name in self.keys:
            self.pressed.add(name) if down else self.pressed.discard(name)

    def stop(self):
        self.stopped = True
        self.pressed.clear()

    def tick(self):
        if not self.active or self.paused or self.stopped:
            return None
        sim = self.playground.sim
        direction = np.zeros(len(sim.names))
        for key in self.pressed:
            axis, sign = self.keys[key]
            direction[axis] += sign
        direction = np.clip(direction, -1, 1)
        direction[4] = direction[3]
        self.target = np.clip(self.target + direction*sim.speed*sim.dt*self.speed_fraction,
                              sim.lower, sim.upper)
        self.playground.physical.invalidate()
        state = self.playground.controller.step(self.target)
        try:
            self.latest = self.playground.feedback.observation('manual', self.playground.physical.confirmed.revision)
            self.observation_error = None
        except ValueError as error:
            self.latest = None
            self.observation_error = str(error)
        return state
