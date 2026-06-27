from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config = PathJoinSubstitution(
        [FindPackageShare("pi_peripheral_lab"), "config", "atlas_can.yaml"]
    )
    dry_run = LaunchConfiguration("dry_run")
    channel = LaunchConfiguration("channel")
    bitrate = LaunchConfiguration("bitrate")
    return LaunchDescription(
        [
            DeclareLaunchArgument("dry_run", default_value="true"),
            DeclareLaunchArgument("channel", default_value="dry_can_lab"),
            DeclareLaunchArgument("bitrate", default_value="500000"),
            Node(
                package="pi_peripheral_lab",
                executable="can_receiver_node",
                name="can_receiver_node",
                parameters=[config, {"dry_run": dry_run, "channel": channel, "bitrate": bitrate}],
            ),
        ]
    )
