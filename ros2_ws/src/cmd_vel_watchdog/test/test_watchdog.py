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
from std_msgs.msg import Bool
from std_msgs.msg import String

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


def is_zero(msg):
    return msg.linear.x == 0.0 and msg.angular.z == 0.0


@pytest.fixture
def rclpy_context():
    rclpy.init()
    try:
        yield
    finally:
        rclpy.shutdown()


@pytest.fixture
def watchdog_harness(rclpy_context):
    executor = SingleThreadedExecutor()
    watchdog = CmdVelWatchdog(
        parameter_overrides=[
            Parameter("timeout_sec", value=0.2),
            Parameter("zero_publish_rate_hz", value=20.0),
            Parameter("max_linear_x", value=0.3),
            Parameter("max_angular_z", value=0.7),
        ],
    )
    test_node = rclpy.create_node("cmd_vel_watchdog_test")
    received = {"safe": [], "status": []}

    executor.add_node(watchdog)
    executor.add_node(test_node)

    publisher = test_node.create_publisher(Twist, "cmd_vel", 10)
    estop_publisher = test_node.create_publisher(Bool, "teleop_estop", 10)
    subscriptions = [
        test_node.create_subscription(Twist, "cmd_vel_safe", received["safe"].append, 10),
        test_node.create_subscription(
            String,
            "cmd_vel_watchdog/status",
            received["status"].append,
            10,
        ),
    ]

    try:
        assert subscriptions
        assert spin_until(
            executor,
            lambda: publisher.get_subscription_count() > 0
            and estop_publisher.get_subscription_count() > 0,
        )
        yield executor, publisher, estop_publisher, received
    finally:
        executor.remove_node(test_node)
        executor.remove_node(watchdog)
        test_node.destroy_node()
        watchdog.destroy_node()


def status_contains(received, text):
    return any(text in msg.data for msg in received["status"])


def test_watchdog_clamps_times_out_and_recovers(watchdog_harness):
    executor, publisher, _estop_publisher, received = watchdog_harness

    publisher.publish(make_twist(linear_x=0.8, angular_z=1.4))

    assert spin_until(
        executor,
        lambda: any(
            msg.linear.x == 0.3 and msg.angular.z == 0.7 for msg in received["safe"]
        ),
    )

    received["safe"].clear()
    assert spin_until(
        executor,
        lambda: any(is_zero(msg) for msg in received["safe"]),
        timeout_sec=2.0,
    )

    received["safe"].clear()
    publisher.publish(make_twist(linear_x=0.1, angular_z=-0.2))

    assert spin_until(
        executor,
        lambda: any(
            msg.linear.x == 0.1 and msg.angular.z == -0.2 for msg in received["safe"]
        ),
    )


def test_watchdog_estop_forces_zero_until_clear(watchdog_harness):
    executor, publisher, estop_publisher, received = watchdog_harness

    estop = Bool()
    estop.data = True
    estop_publisher.publish(estop)
    assert spin_until(executor, lambda: status_contains(received, "estop=true"))

    received["safe"].clear()
    publisher.publish(make_twist(linear_x=0.2, angular_z=0.2))
    assert spin_until(executor, lambda: received["safe"])
    assert all(is_zero(msg) for msg in received["safe"])

    clear = Bool()
    clear.data = False
    received["status"].clear()
    estop_publisher.publish(clear)
    assert spin_until(executor, lambda: status_contains(received, "estop=false"))

    received["safe"].clear()
    publisher.publish(make_twist(linear_x=0.2, angular_z=0.2))
    assert spin_until(
        executor,
        lambda: any(
            msg.linear.x == 0.2 and msg.angular.z == 0.2 for msg in received["safe"]
        ),
    )


def test_watchdog_drops_non_finite_commands(watchdog_harness):
    executor, publisher, _estop_publisher, received = watchdog_harness

    received["safe"].clear()
    received["status"].clear()
    publisher.publish(make_twist(linear_x=float("nan"), angular_z=0.2))

    assert spin_until(
        executor,
        lambda: any(is_zero(msg) for msg in received["safe"])
        and status_contains(received, "state=invalid_cmd"),
    )
