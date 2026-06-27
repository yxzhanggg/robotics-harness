from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config = PathJoinSubstitution(
        [FindPackageShare("pi_peripheral_lab"), "config", "atlas_uart.yaml"]
    )
    dry_run = LaunchConfiguration("dry_run")
    port = LaunchConfiguration("port")
    baud_rate = LaunchConfiguration("baud_rate")
    return LaunchDescription(
        [
            DeclareLaunchArgument("dry_run", default_value="true"),
            DeclareLaunchArgument("port", default_value="dry_uart_atlas_vector"),
            DeclareLaunchArgument("baud_rate", default_value="115200"),
            Node(
                package="pi_peripheral_lab",
                executable="uart_rx_node",
                name="uart_rx_node",
                parameters=[config, {"dry_run": dry_run, "port": port, "baud_rate": baud_rate}],
            ),
        ]
    )
