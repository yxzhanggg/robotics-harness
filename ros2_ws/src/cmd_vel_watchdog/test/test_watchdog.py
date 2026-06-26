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

import time

from geometry_msgs.msg import Twist
import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.parameter import Parameter

from cmd_vel_watchdog.node import CmdVelWatchdog


def spin_until(executor, predicate, timeout_sec=2.0):
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        executor.spin_once(timeout_sec=0.02)
        if predicate():
            return True
    return False


def make_twist(linear_x=0.0, angular_z=0.0):
    msg = Twist()
    msg.linear.x = linear_x
    msg.angular.z = angular_z
    return msg


@pytest.fixture
def rclpy_context():
    rclpy.init()
    try:
        yield
    finally:
        rclpy.shutdown()


def test_watchdog_forwards_times_out_and_recovers(rclpy_context):
    executor = SingleThreadedExecutor()
    watchdog = CmdVelWatchdog(
        parameter_overrides=[
            Parameter("timeout_sec", value=0.2),
            Parameter("zero_publish_rate_hz", value=20.0),
        ],
    )
    test_node = rclpy.create_node("cmd_vel_watchdog_test")
    received = []

    executor.add_node(watchdog)
    executor.add_node(test_node)

    publisher = test_node.create_publisher(Twist, "/cmd_vel", 10)
    subscription = test_node.create_subscription(
        Twist,
        "/cmd_vel_safe",
        received.append,
        10,
    )

    try:
        assert spin_until(executor, lambda: publisher.get_subscription_count() > 0)
        assert subscription is not None

        nonzero = make_twist(linear_x=0.2, angular_z=0.4)
        publisher.publish(nonzero)

        assert spin_until(
            executor,
            lambda: any(msg.linear.x == 0.2 and msg.angular.z == 0.4 for msg in received),
        )

        received.clear()
        assert spin_until(
            executor,
            lambda: any(msg.linear.x == 0.0 and msg.angular.z == 0.0 for msg in received),
            timeout_sec=2.0,
        )

        recovered = make_twist(linear_x=0.1, angular_z=-0.2)
        received.clear()
        publisher.publish(recovered)

        assert spin_until(
            executor,
            lambda: any(msg.linear.x == 0.1 and msg.angular.z == -0.2 for msg in received),
        )
    finally:
        executor.remove_node(test_node)
        executor.remove_node(watchdog)
        test_node.destroy_node()
        watchdog.destroy_node()
