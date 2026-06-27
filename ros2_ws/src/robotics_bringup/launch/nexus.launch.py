from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _bringup_path(*parts):
    return PathJoinSubstitution([FindPackageShare("robotics_bringup"), *parts])


def generate_launch_description():
    selected_robot = LaunchConfiguration("selected_robot")
    security_enable = LaunchConfiguration("security_enable")
    security_strategy = LaunchConfiguration("security_strategy")
    security_keystore = LaunchConfiguration("security_keystore")
    shared_teleop_params = LaunchConfiguration("shared_teleop_params")
    nexus_teleop_params = LaunchConfiguration("nexus_teleop_params")
    enable_rosout_collector = LaunchConfiguration("enable_rosout_collector")
    rosout_log_file = LaunchConfiguration("rosout_log_file")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "selected_robot",
                default_value="atlas",
                description="Initial teleoperation target: atlas or vector.",
            ),
            DeclareLaunchArgument(
                "shared_teleop_params",
                default_value=_bringup_path("config", "shared", "teleop_joy.yaml"),
                description="Shared teleoperation parameters.",
            ),
            DeclareLaunchArgument(
                "nexus_teleop_params",
                default_value=_bringup_path("config", "per_device", "nexus", "teleop_joy.yaml"),
                description="Nexus-specific teleoperation parameters.",
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
            DeclareLaunchArgument(
                "enable_rosout_collector",
                default_value="false",
                description="Start the optional rosout JSONL collector on nexus.",
            ),
            DeclareLaunchArgument(
                "rosout_log_file",
                default_value="/home/zyx/robotics_ws/log/central/rosout.jsonl",
                description="Output path for the optional rosout collector.",
            ),
            SetEnvironmentVariable("ROS_SECURITY_ENABLE", security_enable),
            SetEnvironmentVariable("ROS_SECURITY_STRATEGY", security_strategy),
            SetEnvironmentVariable("ROS_SECURITY_KEYSTORE", security_keystore),
            Node(
                package="joy",
                executable="joy_node",
                name="joy_node",
                parameters=[shared_teleop_params, nexus_teleop_params],
                output="screen",
            ),
            Node(
                package="teleop_joy",
                executable="multi_robot_teleop",
                name="multi_robot_teleop",
                parameters=[
                    shared_teleop_params,
                    nexus_teleop_params,
                    {"selected_robot": selected_robot},
                ],
                output="screen",
            ),
            Node(
                package="robotics_fleet_ops",
                executable="rosout_collector",
                name="rosout_collector",
                parameters=[{"output_file": rosout_log_file}],
                output="screen",
                condition=IfCondition(enable_rosout_collector),
            ),
        ]
    )
