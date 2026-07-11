import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_share = get_package_share_directory('atom_description')
    ros_gz_sim = get_package_share_directory('ros_gz_sim')
    urdf_file = os.path.join(pkg_share, 'urdf', 'atom.urdf.xacro')
    
    # Monta o caminho exato para o Gazebo achar as meshes
    # O GZ_SIM_RESOURCE_PATH deve apontar para o diretório 'share' do workspace
    install_share_dir = os.path.join(get_package_prefix('atom_description'), 'share')
    set_env = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=install_share_dir
    )

    # Compila o Xacro para uma string
    robot_description_content = Command([
        FindExecutable(name='xacro'), ' ', urdf_file
    ])
    robot_description = {'robot_description': robot_description_content}

    return LaunchDescription([
        set_env,
        
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[robot_description]
        ),
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': '-r empty.sdf'}.items(),
        ),
        
        # O PULO DO GATO: Injeção direta via -string em vez de -topic
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-string', robot_description_content,
                '-name', 'atom_scara',
                '-z', '0.1' # Solta o robô 10cm do chão
            ],
            output='screen'
        )
    ])