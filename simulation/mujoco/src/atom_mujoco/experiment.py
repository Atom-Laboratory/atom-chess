"""Episode plumbing only. The researcher supplies every task-specific choice.

This is deliberately not a Gymnasium Env: spaces and their semantics must be
chosen first. No policy, optimizer, default reward or hardware transport exists.
"""
from copy import deepcopy
from typing import Protocol

import numpy as np

from .backend import Simulation


class Task(Protocol):
    def reset(self, state: dict, rng: np.random.Generator) -> None:
        """Initialize task state/goals using the provided episode RNG."""
        ...

    def observation(self, state: dict):
        """Choose observations, units and normalization explicitly."""
        ...

    def target(self, action, state: dict):
        """Map the chosen action space to SI joint position targets."""
        ...

    def evaluate(self, before: dict, after: dict) -> tuple[float, bool, dict]:
        """Return finite reward, task termination and diagnostics."""
        ...


class Episode:
    def __init__(self, simulation: Simulation, task: Task, *, max_steps: int):
        if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps <= 0:
            raise ValueError('max_steps must be a positive integer')
        self.simulation, self.task, self.max_steps = simulation, task, max_steps
        self.finished = True
        self.steps = 0

    def reset(self, *, seed: int, position=None, randomize=False):
        self.finished = True
        # Independent streams avoid coupling task randomness to reset sampling.
        children = np.random.SeedSequence(seed).spawn(2)
        state = self.simulation.reset(position, seed=children[0], randomize=randomize)
        self.task.reset(deepcopy(state), np.random.default_rng(children[1]))
        observation = self.task.observation(deepcopy(state))
        self.steps = 0
        self.finished = False
        return observation, {'seed': seed, 'state': state}

    def step(self, action):
        if self.finished:
            raise RuntimeError('Call reset before stepping a new or finished episode')
        before = self.simulation.observe()
        target = self.task.target(action, deepcopy(before))
        self.simulation.validate(target)  # Bad actions do not consume a step.
        # Any physics/task exception after mutation invalidates the episode.
        self.finished = True
        after = self.simulation.advance(target)
        reward, terminated, diagnostics = self.task.evaluate(deepcopy(before), deepcopy(after))
        if not np.isscalar(reward) or not np.isfinite(reward):
            raise ValueError('Task reward must be a finite scalar; reset required')
        if not isinstance(terminated, (bool, np.bool_)) or not isinstance(diagnostics, dict):
            raise ValueError('Task must return a boolean termination and dict diagnostics')
        observation = self.task.observation(deepcopy(after))
        self.steps += 1
        truncated = self.steps >= self.max_steps
        self.finished = bool(terminated or truncated)
        return observation, float(reward), bool(terminated), truncated, {
            'state': after, 'task': diagnostics, 'steps': self.steps}
