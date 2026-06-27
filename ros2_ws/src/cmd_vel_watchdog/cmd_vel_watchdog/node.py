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

from __future__ import annotations

import math

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from std_msgs.msg import String


class CmdVelWatchdog(Node):
    """Republish operator intent to safe velocity commands with local interlocks."""

    def __init__(self, **kwargs) -> None:
        super().__init__("cmd_vel_watchdog", **kwargs)

        self.declare_parameter("input_topic", "cmd_vel")
        self.declare_parameter("output_topic", "cmd_vel_safe")
        self.declare_parameter("estop_topic", "teleop_estop")
        self.declare_parameter("status_topic", "~/status")
        self.declare_parameter("timeout_sec", 0.5)
        self.declare_parameter("zero_publish_rate_hz", 10.0)
        self.declare_parameter("max_linear_x", 0.6)
        self.declare_parameter("max_angular_z", 1.5)
        self.declare_parameter("publish_zero_before_first_cmd", True)

        self._timeout_sec = self._positive_float_parameter("timeout_sec", 0.5)
        zero_rate_hz = self._positive_float_parameter("zero_publish_rate_hz", 10.0)
        self._max_linear_x = self._non_negative_float_parameter("max_linear_x", 0.6)
        self._max_angular_z = self._non_negative_float_parameter("max_angular_z", 1.5)
        self._publish_zero_before_first_cmd = bool(
            self.get_parameter("publish_zero_before_first_cmd").value
        )
        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        estop_topic = str(self.get_parameter("estop_topic").value)
        status_topic = str(self.get_parameter("status_topic").value)

        self._last_cmd_time = None
        self._last_safe_cmd = Twist()
        self._estop_active = False
        self._last_status = ""

        self._publisher = self.create_publisher(Twist, output_topic, 10)
        self._status_publisher = self.create_publisher(String, status_topic, 10)
        self._subscription = self.create_subscription(
            Twist,
            input_topic,
            self._on_cmd_vel,
            10,
        )
        self._estop_subscription = self.create_subscription(
            Bool,
            estop_topic,
            self._on_estop,
            10,
        )
        self._timer = self.create_timer(1.0 / zero_rate_hz, self._on_timer)

        self.get_logger().info(
            f"watching {input_topic}; publishing safe commands to {output_topic}; "
            f"estop_topic={estop_topic}; timeout_sec={self._timeout_sec}; "
            f"zero_publish_rate_hz={zero_rate_hz}; max_linear_x={self._max_linear_x}; "
            f"max_angular_z={self._max_angular_z}"
        )

    def _positive_float_parameter(self, name: str, default: float) -> float:
        value = float(self.get_parameter(name).value)
        if value <= 0.0:
            self.get_logger().warn(f"{name} must be positive; using {default}")
            return default
        return value

    def _non_negative_float_parameter(self, name: str, default: float) -> float:
        value = float(self.get_parameter(name).value)
        if value < 0.0:
            self.get_logger().warn(f"{name} must be non-negative; using {default}")
            return default
        return value

    def _on_cmd_vel(self, msg: Twist) -> None:
        self._last_cmd_time = self.get_clock().now()
        if self._estop_active:
            self._publish_zero("estop")
            return

        if not self._twist_is_finite(msg):
            self.get_logger().warn("dropping non-finite cmd_vel and publishing zero")
            self._publish_zero("invalid_cmd")
            return

        safe_cmd = self._clamp_twist(msg)
        self._last_safe_cmd = safe_cmd
        self._publisher.publish(safe_cmd)
        self._publish_status("active")

    def _on_estop(self, msg: Bool) -> None:
        if self._estop_active == bool(msg.data):
            return
        self._estop_active = bool(msg.data)
        if self._estop_active:
            self.get_logger().warn("teleop e-stop active; forcing zero velocity")
            self._publish_zero("estop")
        else:
            self.get_logger().info("teleop e-stop cleared")
            self._publish_zero("idle")

    def _on_timer(self) -> None:
        if self._last_cmd_time is None:
            if self._publish_zero_before_first_cmd:
                self._publish_zero("waiting_for_cmd")
            return

        elapsed = (self.get_clock().now() - self._last_cmd_time).nanoseconds / 1e9
        if self._estop_active:
            self._publish_zero("estop")
        elif elapsed > self._timeout_sec:
            self._publish_zero("timeout")

    def _publish_zero(self, reason: str) -> None:
        self._publisher.publish(Twist())
        self._last_safe_cmd = Twist()
        self._publish_status(reason)

    def _publish_status(self, state: str) -> None:
        status = (
            f"state={state} estop={str(self._estop_active).lower()} "
            f"linear_x={self._last_safe_cmd.linear.x:.3f} "
            f"angular_z={self._last_safe_cmd.angular.z:.3f}"
        )
        if status == self._last_status:
            return
        msg = String()
        msg.data = status
        self._status_publisher.publish(msg)
        self._last_status = status

    def _clamp_twist(self, msg: Twist) -> Twist:
        safe = Twist()
        safe.linear.x = self._clamp(msg.linear.x, -self._max_linear_x, self._max_linear_x)
        safe.angular.z = self._clamp(msg.angular.z, -self._max_angular_z, self._max_angular_z)
        return safe

    @staticmethod
    def _is_zero_twist(msg: Twist) -> bool:
        return (
            msg.linear.x == 0.0
            and msg.linear.y == 0.0
            and msg.linear.z == 0.0
            and msg.angular.x == 0.0
            and msg.angular.y == 0.0
            and msg.angular.z == 0.0
        )

    @staticmethod
    def _twist_is_finite(msg: Twist) -> bool:
        return all(
            math.isfinite(value)
            for value in (
                msg.linear.x,
                msg.linear.y,
                msg.linear.z,
                msg.angular.x,
                msg.angular.y,
                msg.angular.z,
            )
        )

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = CmdVelWatchdog()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
