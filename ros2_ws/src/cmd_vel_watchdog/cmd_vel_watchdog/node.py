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

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node


class CmdVelWatchdog(Node):
    """Republish /cmd_vel to /cmd_vel_safe and force zero after timeout."""

    def __init__(self, **kwargs) -> None:
        super().__init__("cmd_vel_watchdog", **kwargs)

        self.declare_parameter("input_topic", "/cmd_vel")
        self.declare_parameter("output_topic", "/cmd_vel_safe")
        self.declare_parameter("timeout_sec", 0.5)
        self.declare_parameter("zero_publish_rate_hz", 10.0)

        self._timeout_sec = self._positive_float_parameter("timeout_sec", 0.5)
        zero_rate_hz = self._positive_float_parameter("zero_publish_rate_hz", 10.0)
        input_topic = self.get_parameter("input_topic").value
        output_topic = self.get_parameter("output_topic").value

        self._last_cmd_time = None
        self._last_output_zero = True

        self._publisher = self.create_publisher(Twist, output_topic, 10)
        self._subscription = self.create_subscription(
            Twist,
            input_topic,
            self._on_cmd_vel,
            10,
        )
        self._timer = self.create_timer(1.0 / zero_rate_hz, self._on_timer)

        self.get_logger().info(
            f"watching {input_topic}; publishing safe commands to {output_topic}; "
            f"timeout_sec={self._timeout_sec}; zero_publish_rate_hz={zero_rate_hz}"
        )

    def _positive_float_parameter(self, name: str, default: float) -> float:
        value = float(self.get_parameter(name).value)
        if value <= 0.0:
            self.get_logger().warn(f"{name} must be positive; using {default}")
            return default
        return value

    def _on_cmd_vel(self, msg: Twist) -> None:
        self._last_cmd_time = self.get_clock().now()
        self._last_output_zero = self._is_zero_twist(msg)
        self._publisher.publish(msg)

    def _on_timer(self) -> None:
        if self._last_cmd_time is None:
            self._publish_zero()
            return

        elapsed = (self.get_clock().now() - self._last_cmd_time).nanoseconds / 1e9
        if elapsed > self._timeout_sec:
            self._publish_zero()

    def _publish_zero(self) -> None:
        self._publisher.publish(Twist())
        self._last_output_zero = True

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
