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
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool

from teleop_joy.multi_robot_teleop import MultiRobotTeleop


def spin_until(executor, predicate, timeout_sec=2.0):
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        executor.spin_once(timeout_sec=0.02)
        if predicate():
            return True
    return False


def make_joy(*, linear=0.0, angular=0.0, buttons=None):
    msg = Joy()
    msg.axes = [0.0, linear, 0.0, angular]
    msg.buttons = [0] * 8
    if buttons:
        for button in buttons:
            msg.buttons[button] = 1
    return msg


def is_zero(msg):
    return msg.linear.x == 0.0 and msg.angular.z == 0.0


def has_cmd(messages, linear_x, angular_z):
    return any(
        msg.linear.x == pytest.approx(linear_x)
        and msg.angular.z == pytest.approx(angular_z)
        for msg in messages
    )


@pytest.fixture
def rclpy_context():
    rclpy.init()
    try:
        yield
    finally:
        rclpy.shutdown()


@pytest.fixture
def teleop_harness(rclpy_context):
    executor = SingleThreadedExecutor()
    teleop = MultiRobotTeleop(
        parameter_overrides=[
            Parameter("publish_rate_hz", value=30.0),
            Parameter("stale_joy_timeout_sec", value=0.2),
            Parameter("scale_linear_x", value=0.5),
            Parameter("scale_angular_z", value=1.0),
            Parameter("scale_linear_x_turbo", value=0.8),
            Parameter("scale_angular_z_turbo", value=1.4),
        ],
    )
    test_node = rclpy.create_node("multi_robot_teleop_test")

    executor.add_node(teleop)
    executor.add_node(test_node)

    received = {
        "atlas": [],
        "vector": [],
        "atlas_estop": [],
        "vector_estop": [],
    }
    publisher = test_node.create_publisher(Joy, "/joy", 10)
    subscriptions = [
        test_node.create_subscription(Twist, "/atlas/cmd_vel", received["atlas"].append, 10),
        test_node.create_subscription(Twist, "/vector/cmd_vel", received["vector"].append, 10),
        test_node.create_subscription(
            Bool,
            "/atlas/teleop_estop",
            received["atlas_estop"].append,
            10,
        ),
        test_node.create_subscription(
            Bool,
            "/vector/teleop_estop",
            received["vector_estop"].append,
            10,
        ),
    ]

    try:
        assert subscriptions
        assert spin_until(executor, lambda: publisher.get_subscription_count() > 0)
        yield executor, teleop, publisher, received
    finally:
        executor.remove_node(test_node)
        executor.remove_node(teleop)
        test_node.destroy_node()
        teleop.destroy_node()


def test_deadman_and_runtime_robot_selection(teleop_harness):
    executor, _teleop, publisher, received = teleop_harness

    publisher.publish(make_joy(linear=1.0, angular=0.5))
    assert spin_until(executor, lambda: len(received["atlas"]) > 0)
    assert all(is_zero(msg) for msg in received["atlas"])

    received["atlas"].clear()
    received["vector"].clear()
    publisher.publish(make_joy(linear=0.6, angular=-0.4, buttons=[4]))

    assert spin_until(
        executor,
        lambda: has_cmd(received["atlas"], 0.3, -0.4),
    )
    assert all(is_zero(msg) for msg in received["vector"])

    received["atlas"].clear()
    received["vector"].clear()
    publisher.publish(make_joy(buttons=[1]))
    assert spin_until(executor, lambda: received["atlas"] and received["vector"])
    assert all(is_zero(msg) for msg in received["atlas"])
    assert all(is_zero(msg) for msg in received["vector"])

    received["atlas"].clear()
    received["vector"].clear()
    publisher.publish(make_joy(linear=0.5, angular=0.25, buttons=[4, 5]))

    assert spin_until(
        executor,
        lambda: has_cmd(received["vector"], 0.4, 0.35),
    )
    assert all(is_zero(msg) for msg in received["atlas"])


def test_estop_latches_until_clear(teleop_harness):
    executor, _teleop, publisher, received = teleop_harness

    publisher.publish(make_joy(buttons=[2]))
    assert spin_until(
        executor,
        lambda: any(msg.data for msg in received["atlas_estop"])
        and any(msg.data for msg in received["vector_estop"]),
    )

    received["atlas"].clear()
    publisher.publish(make_joy(linear=1.0, angular=1.0, buttons=[4]))
    assert spin_until(executor, lambda: received["atlas"])
    assert all(is_zero(msg) for msg in received["atlas"])

    publisher.publish(make_joy(buttons=[3]))
    assert spin_until(
        executor,
        lambda: any(not msg.data for msg in received["atlas_estop"])
        and any(not msg.data for msg in received["vector_estop"]),
    )

    received["atlas"].clear()
    publisher.publish(make_joy(linear=1.0, angular=1.0, buttons=[4]))
    assert spin_until(
        executor,
        lambda: has_cmd(received["atlas"], 0.5, 1.0),
    )


def test_stale_joy_timeout_publishes_zero(teleop_harness):
    executor, _teleop, publisher, received = teleop_harness

    publisher.publish(make_joy(linear=1.0, angular=0.5, buttons=[4]))
    assert spin_until(
        executor,
        lambda: has_cmd(received["atlas"], 0.5, 0.5),
    )

    received["atlas"].clear()
    assert spin_until(
        executor,
        lambda: any(is_zero(msg) for msg in received["atlas"]),
        timeout_sec=2.0,
    )
