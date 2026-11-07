"""Launch one conventional kinematic controller and its visualization."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    share = FindPackageShare('atom_description')
    description = ParameterValue(Command([FindExecutable(name='xacro'), ' ',
        PathJoinSubstitution([share, 'urdf', 'atom.urdf.xacro'])]), value_type=str)
    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': description}], output='screen'),
        Node(package='atom_description', executable='kinematic_controller.py',
             parameters=[{'robot_description': description}], output='screen'),
        Node(package='rviz2', executable='rviz2',
             condition=IfCondition(LaunchConfiguration('rviz')),
             arguments=['-d', PathJoinSubstitution([share, 'rviz', 'atom.rviz'])]),
    ])
