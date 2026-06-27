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
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config_file = PathJoinSubstitution([
        FindPackageShare('teleop_joy'),
        'config',
        'dualsense_teleop.yaml',
    ])

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[config_file],
        output='screen',
    )

    selected_robot_arg = DeclareLaunchArgument(
        'selected_robot',
        default_value='atlas',
        description='Initial robot target: atlas or vector.',
    )

    teleop_node = Node(
        package='teleop_joy',
        executable='multi_robot_teleop',
        name='multi_robot_teleop',
        parameters=[config_file, {'selected_robot': LaunchConfiguration('selected_robot')}],
        output='screen',
    )

    return LaunchDescription([
        selected_robot_arg,
        joy_node,
        teleop_node,
    ])
