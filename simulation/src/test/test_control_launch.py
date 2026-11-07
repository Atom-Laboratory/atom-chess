"""Exercise command -> controller -> JointState -> TF and reset on real DDS."""
import json
import math
import os
import signal
import subprocess
import time

import rclpy
from rclpy.context import Context
from rclpy.executors import SingleThreadedExecutor
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from std_srvs.srv import Trigger
from tf2_msgs.msg import TFMessage


def test_control_motion_rejection_stop_and_reset(tmp_path):
    domain = 30 + os.getpid() % 50
    context = Context()
    rclpy.init(context=context, domain_id=domain)
    node = rclpy.create_node('control_probe', context=context)
    executor = SingleThreadedExecutor(context=context)
    executor.add_node(node)
    states, statuses, frames = [], [], {}
    def tf_callback(message):
        for transform in message.transforms:
            frames[transform.child_frame_id] = transform
    subscriptions = [
        node.create_subscription(JointState, '/joint_states', states.append, 100),
        node.create_subscription(String, '/atom_sim/status', lambda m: statuses.append(json.loads(m.data)), 100),
        node.create_subscription(TFMessage, '/tf', tf_callback, 100),
    ]
    publisher = node.create_publisher(JointState, '/atom_sim/command', 10)
    reset = node.create_client(Trigger, '/atom_sim/reset')
    stop = node.create_client(Trigger, '/atom_sim/stop')
    log_path = tmp_path / 'control.log'
    process = None
    def until(predicate, timeout=10):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            executor.spin_once(timeout_sec=.05)
            assert process.poll() is None, log_path.read_text()
            if predicate():
                return
        raise AssertionError(log_path.read_text() + '\nCondition timed out')
    try:
        with log_path.open('w') as log:
            process = subprocess.Popen(['ros2', 'launch', 'atom_description', 'control_demo.launch.py', 'rviz:=false'],
                env=dict(os.environ, ROS_DOMAIN_ID=str(domain), DISPLAY='', WAYLAND_DISPLAY='',
                         ROS_LOG_DIR=str(tmp_path/'ros-log')), stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True)
            until(lambda: bool(states) and publisher.get_subscription_count() == 1 and reset.service_is_ready())
            assert len(node.get_publishers_info_by_topic('/joint_states')) == 1
            names = list(states[-1].name)
            goal = [.3, .08, -.4]
            publisher.publish(JointState(name=names, position=goal))
            until(lambda: bool(statuses) and statuses[-1]['event'] == 'accepted')
            until(lambda: all(abs(a-b)<1e-7 for a,b in zip(states[-1].position, goal)))
            assert any(0 < s.position[0] < goal[0] for s in states)
            until(lambda: 'arm1_link' in frames and abs(frames['arm1_link'].transform.translation.y-.08)<1e-7)
            until(lambda: 'z_axis_link' in frames and abs(frames['z_axis_link'].transform.rotation.y-math.sin(.3/2))<1e-7)
            publisher.publish(JointState(name=names, position=[99., 0., 0.]))
            until(lambda: statuses[-1]['event'].startswith('rejected'))
            assert statuses[-1]['target'] == goal
            assert list(states[-1].position) == goal
            publisher.publish(JointState(name=names, position=[1.5, .15, 3.]))
            until(lambda: states[-1].position[0] > .3)
            future = stop.call_async(Trigger.Request())
            until(future.done)
            assert future.result().success
            until(lambda: statuses[-1]['event'] == 'stopped')
            held = statuses[-1]['position']
            stamp = states[-1].header.stamp.sec + states[-1].header.stamp.nanosec/1e9
            until(lambda: states[-1].header.stamp.sec + states[-1].header.stamp.nanosec/1e9 > stamp+.15)
            assert list(states[-1].position) == held
            future = reset.call_async(Trigger.Request())
            until(future.done)
            assert future.result().success
            until(lambda: list(states[-1].position) == [0., 0., 0.])
            assert statuses[-1]['collisions'] is None
    finally:
        if process is not None:
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
        executor.shutdown()
        node.destroy_node()
        context.shutdown()
