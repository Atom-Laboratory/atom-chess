#!/usr/bin/env python3
"""Diagnostic position servo; no physics, learned policy or hardware transport."""

import json
import math
import time
import xml.etree.ElementTree as ET

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from std_srvs.srv import Trigger


class PositionServo:
    """Small deterministic control core using only limits from the supplied URDF."""

    def __init__(self, description):
        self.names, self.limits, self.speeds = [], [], []
        for joint in ET.fromstring(description).findall('joint'):
            if joint.attrib['type'] == 'fixed':
                continue
            if joint.attrib['type'] not in ('revolute', 'prismatic') or joint.find('mimic') is not None:
                raise ValueError('Only independent bounded joints are supported')
            name = joint.attrib['name']
            limit = joint.find('limit')
            lower, upper, speed = (float(limit.attrib[key]) for key in ('lower', 'upper', 'velocity'))
            if name in self.names or not all(map(math.isfinite, (lower, upper, speed))) or lower >= upper or speed <= 0:
                raise ValueError('Invalid joint limits')
            self.names.append(name)
            self.limits.append((lower, upper))
            self.speeds.append(speed)
        if not self.names:
            raise ValueError('No movable joints')
        self.reset()

    def reset(self):
        self.position = [min(upper, max(lower, 0.0)) for lower, upper in self.limits]
        self.target = self.position.copy()
        self.velocity = [0.0] * len(self.names)

    def command(self, names, positions):
        if len(names) != len(self.names) or len(positions) != len(names) or set(names) != set(self.names):
            raise ValueError('Supply every joint exactly once')
        mapping = dict(zip(names, positions))
        target = [float(mapping[name]) for name in self.names]
        if any(not math.isfinite(q) or not lower <= q <= upper
               for q, (lower, upper) in zip(target, self.limits)):
            raise ValueError('Position is nonfinite or outside prototype limits')
        self.target = target

    def stop(self):
        self.target = self.position.copy()
        self.velocity = [0.0] * len(self.names)

    def step(self, dt):
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError('dt must be finite and positive')
        previous = self.position.copy()
        self.position = [q + max(-speed * dt, min(speed * dt, goal - q))
                         for q, goal, speed in zip(previous, self.target, self.speeds)]
        self.velocity = [(q - old) / dt for q, old in zip(self.position, previous)]


class Controller(Node):
    def __init__(self):
        super().__init__('atom_kinematic_controller')
        description = self.declare_parameter('robot_description', '').value
        self.servo = PositionServo(description)
        self.sequence = 0
        self.last_event = 'initialized'
        self.elapsed = 0.0
        self.previous_time = time.monotonic()
        self.states = self.create_publisher(JointState, '/joint_states', 10)
        self.telemetry = self.create_publisher(String, '/atom_sim/status', 10)
        self.subscription = self.create_subscription(JointState, '/atom_sim/command', self.command, 10)
        self.reset_service = self.create_service(Trigger, '/atom_sim/reset', self.reset)
        self.stop_service = self.create_service(Trigger, '/atom_sim/stop', self.stop)
        self.timer = self.create_timer(0.05, self.tick)
        self.get_logger().warning('Uncalibrated kinematic prototype: no physics, collisions or hardware')

    def command(self, message):
        self.sequence += 1
        try:
            if message.velocity or message.effort:
                raise ValueError('Position commands only; velocity/effort must be empty')
            self.servo.command(message.name, message.position)
            self.last_event = 'accepted'
        except ValueError as error:
            self.last_event = 'rejected: ' + str(error)
            self.get_logger().warning(self.last_event)
        self.publish()

    def reset(self, request, response):
        self.servo.reset()
        self.elapsed = 0.0
        self.previous_time = time.monotonic()
        self.last_event = 'reset'
        self.publish()
        response.success, response.message = True, 'Prototype reset; not hardware homing'
        return response

    def stop(self, request, response):
        self.servo.stop()
        self.last_event = 'stopped'
        self.publish()
        response.success, response.message = True, 'Holding current simulated position'
        return response

    def tick(self):
        now = time.monotonic()
        dt = min(0.05, max(1e-9, now - self.previous_time))
        self.previous_time = now
        self.servo.step(dt)
        self.elapsed += dt
        self.publish()

    def publish(self):
        state = JointState()
        state.header.stamp = self.get_clock().now().to_msg()
        state.name = self.servo.names
        state.position = self.servo.position
        state.velocity = self.servo.velocity
        self.states.publish(state)
        status = dict(profile='uncalibrated-kinematic-v1', command_sequence=self.sequence,
                      event=self.last_event, elapsed_s=self.elapsed, names=self.servo.names,
                      position=self.servo.position, target=self.servo.target,
                      error=[g-q for g, q in zip(self.servo.target, self.servo.position)],
                      collisions=None, effort=None)
        self.telemetry.publish(String(data=json.dumps(status, allow_nan=False)))


def main():
    rclpy.init()
    node = Controller()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
