"""Display the existing, uncalibrated prototype without a physics backend."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package = FindPackageShare('atom_description')
    model = PathJoinSubstitution([package, 'urdf', 'atom.urdf.xacro'])
    rviz_config = PathJoinSubstitution([package, 'rviz', 'atom.rviz'])
    use_sim_time = ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)
    robot_description = ParameterValue(
        Command([FindExecutable(name='xacro'), ' ', model]), value_type=str
    )

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true',
                              description='Use sliders; false publishes the default joint states.'),
        DeclareLaunchArgument('rviz', default_value='true',
                              description='Start RViz; false allows a headless session.'),
        DeclareLaunchArgument('use_sim_time', default_value='false',
                              description='Enable only when an external /clock is available.'),
        LogInfo(msg='ATOM diagnostic prototype: joint axes, limits and dimensions are '
                    'uncalibrated. This model is not connected to hardware.'),
        Node(
            package='robot_state_publisher', executable='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description, 'use_sim_time': use_sim_time}],
        ),
        Node(
            package='joint_state_publisher_gui', executable='joint_state_publisher_gui',
            name='joint_state_publisher', condition=IfCondition(LaunchConfiguration('gui')),
            parameters=[{'use_sim_time': use_sim_time}], output='screen',
        ),
        Node(
            package='joint_state_publisher', executable='joint_state_publisher',
            name='joint_state_publisher', condition=UnlessCondition(LaunchConfiguration('gui')),
            parameters=[{'use_sim_time': use_sim_time}], output='screen',
        ),
        Node(
            package='rviz2', executable='rviz2', name='rviz2',
            condition=IfCondition(LaunchConfiguration('rviz')),
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': use_sim_time}], output='screen',
        ),
    ])
