from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config = PathJoinSubstitution(
        [FindPackageShare("pi_peripheral_lab"), "config", "atlas_handshake.yaml"]
    )
    dry_run = LaunchConfiguration("dry_run")
    return LaunchDescription(
        [
            DeclareLaunchArgument("dry_run", default_value="true"),
            Node(
                package="pi_peripheral_lab",
                executable="gpio_handshake_main_node",
                name="gpio_handshake_main_node",
                parameters=[config, {"dry_run": dry_run}],
            ),
        ]
    )
