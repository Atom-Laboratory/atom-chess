"""Strict URDF serial-chain kinematics; geometry is read, never guessed.

Only fixed/revolute/prismatic joints are supported. Xacro with executable macros
must be expanded first. The current repository's .xacro contains plain URDF.
"""

from dataclasses import dataclass
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np


def vector(value, size):
    result = np.asarray(value, dtype=float)
    if result.shape != (size,) or not np.all(np.isfinite(result)):
        raise ValueError(f"Expected {size} finite numbers")
    return result


def rotation(axis, angle):
    x, y, z = axis
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3) + np.sin(angle) * skew + (1 - np.cos(angle)) * (skew @ skew)


def rotation_error(target, current):
    """World-frame rotation vector, including a stable near-pi branch."""
    delta = target @ current.T
    angle = np.arccos(np.clip((np.trace(delta) - 1) / 2, -1, 1))
    skew = np.array([delta[2, 1] - delta[1, 2], delta[0, 2] - delta[2, 0],
                     delta[1, 0] - delta[0, 1]])
    if angle < 1e-7:
        return skew / 2
    if np.pi - angle < 1e-5:
        values, axes = np.linalg.eigh((delta + delta.T) / 2)
        axis = axes[:, np.argmax(values)]
        if axis @ skew < 0:
            axis = -axis
        return angle * axis
    return angle / (2 * np.sin(angle)) * skew


@dataclass(frozen=True)
class Joint:
    name: str
    kind: str
    parent: str
    child: str
    origin: np.ndarray
    axis: np.ndarray
    lower: float = 0.0
    upper: float = 0.0
    velocity: float = 0.0


class UrdfModel:
    """A single rooted serial chain ending at an explicitly named link frame."""

    def __init__(self, path, tip):
        self.path = Path(path).resolve()
        raw = self.path.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        root = ET.fromstring(raw)
        if root.tag != 'robot' or any('}' in element.tag for element in root.iter()):
            raise ValueError('Supply expanded URDF; executable Xacro is not supported')
        links = [link.attrib['name'] for link in root.findall('link')]
        if len(set(links)) != len(links) or tip not in links:
            raise ValueError('Duplicate links or missing tip')
        by_child, names = {}, set()
        for element in root.findall('joint'):
            name, kind = element.attrib['name'], element.attrib['type']
            if name in names or kind not in ('fixed', 'revolute', 'prismatic'):
                raise ValueError('Duplicate or unsupported joint')
            names.add(name)
            if element.find('mimic') is not None:
                raise ValueError('Mimic joints require a separate coupling model')
            parent = element.find('parent').attrib['link']
            child = element.find('child').attrib['link']
            if child in by_child or parent not in links or child not in links:
                raise ValueError('Invalid parent/child topology')
            origin = np.eye(4)
            source = element.find('origin')
            if source is not None:
                xyz = vector([float(x) for x in source.get('xyz', '0 0 0').split()], 3)
                rpy = vector([float(x) for x in source.get('rpy', '0 0 0').split()], 3)
                origin[:3, 3] = xyz
                origin[:3, :3] = (rotation([0, 0, 1], rpy[2]) @
                                  rotation([0, 1, 0], rpy[1]) @ rotation([1, 0, 0], rpy[0]))
            axis = np.array([1., 0., 0.])
            lower = upper = velocity = 0.0
            if kind != 'fixed':
                source = element.find('axis')
                if source is not None:
                    axis = vector([float(x) for x in source.attrib['xyz'].split()], 3)
                if not np.isclose(np.linalg.norm(axis), 1, atol=1e-8):
                    raise ValueError('Joint axis must be unit length')
                limit = element.find('limit')
                if limit is None:
                    raise ValueError('Missing joint limits')
                lower, upper, velocity = vector(
                    [float(limit.attrib[key]) for key in ('lower', 'upper', 'velocity')], 3)
                if not lower < upper or velocity <= 0:
                    raise ValueError('Invalid joint limits')
            by_child[child] = Joint(name, kind, parent, child, origin, axis, lower, upper, velocity)
        roots = set(links) - set(by_child)
        if len(roots) != 1:
            raise ValueError('Expected one root')
        self.root = roots.pop()
        for link in links:
            visited = set()
            current = link
            while current in by_child:
                if current in visited:
                    raise ValueError('Cyclic chain')
                visited.add(current)
                current = by_child[current].parent
            if current != self.root:
                raise ValueError('Disconnected tree')
        self.tip = tip
        chain = []
        while tip in by_child:
            chain.append(by_child[tip])
            tip = by_child[tip].parent
        self.chain = list(reversed(chain))
        if len(self.chain) != len(by_child):
            raise ValueError('This backend supports one serial chain, not branches')
        self.moving = [joint for joint in self.chain if joint.kind != 'fixed']
        if not self.moving:
            raise ValueError('No actuated joints')
        self.names = [joint.name for joint in self.moving]
        self.lower = np.array([joint.lower for joint in self.moving])
        self.upper = np.array([joint.upper for joint in self.moving])
        self.velocity = np.array([joint.velocity for joint in self.moving])
        self.span = self.upper - self.lower
        self.center = (self.upper + self.lower) / 2

    @property
    def dof(self):
        return len(self.moving)

    def validate(self, q):
        q = vector(q, self.dof)
        if np.any(q < self.lower - 1e-12) or np.any(q > self.upper + 1e-12):
            raise ValueError('Joint limit violation')
        return q

    def frames(self, q):
        q = self.validate(q)
        transforms = {self.root: np.eye(4)}
        index = 0
        for joint in self.chain:
            motion = np.eye(4)
            if joint.kind == 'revolute':
                motion[:3, :3] = rotation(joint.axis, q[index])
                index += 1
            elif joint.kind == 'prismatic':
                motion[:3, 3] = joint.axis * q[index]
                index += 1
            transforms[joint.child] = transforms[joint.parent] @ joint.origin @ motion
        return transforms

    def fk(self, q):
        return self.frames(q)[self.tip]

    def pose_error(self, target, q):
        actual = self.fk(q)
        return np.r_[target[:3, 3] - actual[:3, 3],
                     rotation_error(target[:3, :3], actual[:3, :3])]

    def ik(self, target, initial=None, iterations=150):
        """Bounded damped least squares; returns None for an unsolved pose.

        This is a local solver, not proof of global unreachability. It uses all
        six pose residuals, so unavailable orientation/translation is rejected.
        """
        target = np.asarray(target, dtype=float)
        if (target.shape != (4, 4) or not np.isfinite(target).all()
                or not np.allclose(target[3], [0, 0, 0, 1])
                or not np.allclose(target[:3, :3].T @ target[:3, :3], np.eye(3), atol=1e-7)
                or not np.isclose(np.linalg.det(target[:3, :3]), 1)):
            raise ValueError('Invalid target transform')
        q = self.center.copy() if initial is None else self.validate(initial).copy()
        for _ in range(iterations):
            error = self.pose_error(target, q)
            if np.linalg.norm(error[:3]) < 1e-7 and np.linalg.norm(error[3:]) < 1e-7:
                return q
            columns = []
            for i in range(self.dof):
                perturbed = q.copy()
                step = min(1e-6, self.upper[i] - q[i])
                if step < 1e-9:
                    step = -min(1e-6, q[i] - self.lower[i])
                perturbed[i] += step
                columns.append((error - self.pose_error(target, perturbed)) / step)
            jacobian = np.array(columns).T
            update = jacobian.T @ np.linalg.solve(jacobian @ jacobian.T + 1e-6 * np.eye(6), error)
            update = np.clip(update, -0.1 * self.span, 0.1 * self.span)
            q = np.clip(q + update, self.lower, self.upper)
        return None
