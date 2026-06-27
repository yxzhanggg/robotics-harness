from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config = PathJoinSubstitution(
        [FindPackageShare("pi_peripheral_lab"), "config", "atlas_adc.yaml"]
    )
    dry_run = LaunchConfiguration("dry_run")
    backend = LaunchConfiguration("backend")
    return LaunchDescription(
        [
            DeclareLaunchArgument("dry_run", default_value="true"),
            DeclareLaunchArgument("backend", default_value="dry"),
            Node(
                package="pi_peripheral_lab",
                executable="adc_reader_node",
                name="adc_reader_node",
                parameters=[config, {"dry_run": dry_run, "backend": backend}],
            ),
        ]
    )
