import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    # Caminhos dos pacotes
    atom_control_dir = get_package_share_directory('atom_control')
    atom_description_dir = get_package_share_directory('atom_description')
    gazebo_ros_dir = get_package_share_directory('gazebo_ros')

    # Processar o arquivo URDF/Xacro
    xacro_file = os.path.join(atom_description_dir, 'urdf', 'atom_scara.urdf') # Ajuste o nome do ficheiro se necessário
    robot_description_config = xacro.process_file(xacro_file)
    robot_description = {'robot_description': robot_description_config.toxml()}

    # Node: Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    # Launch: Gazebo Server e Client
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_dir, 'launch', 'gazebo.launch.py')
        )
    )

    # Node: Spawner da entidade no Gazebo
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'atom_scara'],
        output='screen'
    )

    # Node: Spawner do Joint State Broadcaster
    load_joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    # Node: Spawner do Controller do Braço (apenas inicia após o spawn do robô)
    load_scara_arm_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['scara_arm_controller', '--controller-manager', '/controller_manager'],
    )

    # Garantir ordem correta de inicialização dos controladores
    delay_arm_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[load_joint_state_broadcaster, load_scara_arm_controller],
        )
    )

    return LaunchDescription([
        robot_state_publisher,
        gazebo,
        spawn_entity,
        delay_arm_controller
    ])