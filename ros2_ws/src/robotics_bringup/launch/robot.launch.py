from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _bringup_path(*parts):
    return PathJoinSubstitution([FindPackageShare("robotics_bringup"), *parts])


def generate_launch_description():
    robot_name = LaunchConfiguration("robot_name")
    security_enable = LaunchConfiguration("security_enable")
    security_strategy = LaunchConfiguration("security_strategy")
    security_keystore = LaunchConfiguration("security_keystore")
    shared_watchdog_params = LaunchConfiguration("shared_watchdog_params")
    robot_watchdog_params = LaunchConfiguration("robot_watchdog_params")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "robot_name",
                description="Robot namespace: atlas or vector.",
            ),
            DeclareLaunchArgument(
                "shared_watchdog_params",
                default_value=_bringup_path("config", "shared", "cmd_vel_watchdog.yaml"),
                description="Shared watchdog parameters.",
            ),
            DeclareLaunchArgument(
                "robot_watchdog_params",
                default_value=[
                    _bringup_path("config", "per_robot"),
                    "/",
                    robot_name,
                    "/cmd_vel_watchdog.yaml",
                ],
                description="Robot-specific watchdog parameters.",
            ),
            DeclareLaunchArgument(
                "security_enable",
                default_value="false",
                description="Set ROS_SECURITY_ENABLE for launched processes.",
            ),
            DeclareLaunchArgument(
                "security_strategy",
                default_value="Permissive",
                description="Set ROS_SECURITY_STRATEGY for launched processes.",
            ),
            DeclareLaunchArgument(
                "security_keystore",
                default_value="/home/zyx/robotics_ws/security/keystore",
                description="Set ROS_SECURITY_KEYSTORE for launched processes.",
            ),
            SetEnvironmentVariable("ROS_SECURITY_ENABLE", security_enable),
            SetEnvironmentVariable("ROS_SECURITY_STRATEGY", security_strategy),
            SetEnvironmentVariable("ROS_SECURITY_KEYSTORE", security_keystore),
            Node(
                package="cmd_vel_watchdog",
                executable="cmd_vel_watchdog",
                name="cmd_vel_watchdog",
                namespace=robot_name,
                parameters=[shared_watchdog_params, robot_watchdog_params],
                output="screen",
            ),
        ]
    )
