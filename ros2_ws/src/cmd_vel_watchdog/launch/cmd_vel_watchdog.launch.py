# Copyright 2026 zyx
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_name = LaunchConfiguration('robot_name')
    config_file = PathJoinSubstitution([
        FindPackageShare('cmd_vel_watchdog'),
        'config',
        'watchdog.yaml',
    ])

    robot_name_arg = DeclareLaunchArgument(
        'robot_name',
        default_value='atlas',
        description='Robot namespace for safe command gating.',
    )

    watchdog_node = Node(
        package='cmd_vel_watchdog',
        executable='cmd_vel_watchdog',
        name='cmd_vel_watchdog',
        namespace=robot_name,
        parameters=[config_file],
        output='screen',
    )

    return LaunchDescription([
        robot_name_arg,
        watchdog_node,
    ])
