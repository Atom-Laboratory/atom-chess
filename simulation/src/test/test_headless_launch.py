"""Exercise the actual installed launch and TF publishers in an isolated ROS domain."""

import math
import os
from pathlib import Path
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.context import Context
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import JointState
from tf2_msgs.msg import TFMessage
import xacro


def test_headless_launch_publishes_joint_states_and_complete_tf(tmp_path):
    share = Path(get_package_share_directory('atom_description'))
    robot = ET.fromstring(xacro.process_file(str(share / 'urdf/atom.urdf.xacro')).toxml())
    expected_edges = {
        joint.find('child').attrib['link']: joint.find('parent').attrib['link']
        for joint in robot.findall('joint')
    }
    moving = {joint.attrib['name'] for joint in robot.findall('joint')
              if joint.attrib['type'] != 'fixed'}
    domain = 100 + os.getpid() % 100
    environment = dict(os.environ, ROS_DOMAIN_ID=str(domain),
                       ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',
                       ROS_LOG_DIR=str(tmp_path / 'ros-log'))
    # Invalid graphical endpoints ensure gui:=false/rviz:=false really avoid Qt.
    environment.update(DISPLAY='', WAYLAND_DISPLAY='')
    context = Context()
    rclpy.init(context=context, domain_id=domain)
    node = rclpy.create_node('atom_description_smoke_test', context=context)
    executor = SingleThreadedExecutor(context=context)
    executor.add_node(node)
    transforms = {}
    joint_states = []

    def on_tf(message):
        for transform in message.transforms:
            transforms[transform.child_frame_id] = transform

    static_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                           reliability=ReliabilityPolicy.RELIABLE)
    subscriptions = [
        node.create_subscription(TFMessage, '/tf_static', on_tf, static_qos),
        node.create_subscription(TFMessage, '/tf', on_tf, 100),
        node.create_subscription(JointState, '/joint_states', joint_states.append, 10),
    ]
    process = None
    log_file = tmp_path / 'launch.log'
    try:
        with log_file.open('w') as output:
            process = subprocess.Popen(
                ['ros2', 'launch', 'atom_description', 'view_robot.launch.py',
                 'gui:=false', 'rviz:=false'],
                env=environment, stdout=output, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                executor.spin_once(timeout_sec=0.1)
                assert process.poll() is None, log_file.read_text()
                if joint_states and set(transforms) == set(expected_edges):
                    break
            assert joint_states, f'No joint states received:\n{log_file.read_text()}'
            assert set(transforms) == set(expected_edges), log_file.read_text()
            state = joint_states[-1]
            assert set(state.name) == moving
            assert len(state.position) == len(state.name)
            assert all(math.isfinite(value) for value in state.position)
            for child, parent in expected_edges.items():
                transform = transforms[child]
                assert transform.header.frame_id == parent
                quaternion = transform.transform.rotation
                assert math.isclose(sum(value * value for value in (
                    quaternion.x, quaternion.y, quaternion.z, quaternion.w)),
                    1.0, abs_tol=1e-6)
            # Only the selected publisher should own joint_states.
            assert len(node.get_publishers_info_by_topic('/joint_states')) == 1
    finally:
        if process is not None:
            # Signal the launch parent first so it can reap its own child nodes.
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
        for subscription in subscriptions:
            node.destroy_subscription(subscription)
        executor.shutdown()
        node.destroy_node()
        context.shutdown()
