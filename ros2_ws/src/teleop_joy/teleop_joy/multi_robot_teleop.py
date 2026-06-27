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

from dataclasses import dataclass
from dataclasses import replace

from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool
from std_msgs.msg import String


@dataclass(frozen=True)
class MotionLimits:
    linear_x: float
    angular_z: float
    turbo_linear_x: float
    turbo_angular_z: float


@dataclass(frozen=True)
class TeleopConfig:
    robots: tuple[str, ...]
    cmd_vel_topic: str
    joy_topic: str
    status_topic: str
    estop_topic: str
    selected_robot: str
    require_enable_button: bool
    enable_button: int
    turbo_button: int
    estop_button: int
    clear_estop_button: int
    axis_linear_x: int
    axis_angular_z: int
    select_buttons: dict[str, int]
    deadzone: float
    publish_rate_hz: float
    stale_joy_timeout_sec: float
    limits: MotionLimits


class MultiRobotTeleop(Node):
    """Map one joystick on nexus to exactly one robot command topic at a time."""

    def __init__(self, **kwargs) -> None:
        super().__init__("multi_robot_teleop", **kwargs)

        self._declare_parameters()
        self._config = self._read_config()

        self._cmd_publishers = {
            robot: self.create_publisher(
                Twist,
                self._robot_topic(robot, self._config.cmd_vel_topic),
                10,
            )
            for robot in self._config.robots
        }
        self._estop_state_publishers = {
            robot: self.create_publisher(
                Bool,
                self._robot_topic(robot, self._config.estop_topic),
                10,
            )
            for robot in self._config.robots
        }
        self._status_publisher = self.create_publisher(String, self._config.status_topic, 10)
        self._joy_subscription = self.create_subscription(
            Joy,
            self._config.joy_topic,
            self._on_joy,
            10,
        )
        self._timer = self.create_timer(
            1.0 / self._config.publish_rate_hz,
            self._on_timer,
        )
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self._selected_robot = self._config.selected_robot
        self._last_buttons: list[int] = []
        self._last_joy: Joy | None = None
        self._last_joy_time = None
        self._last_cmd = Twist()
        self._estop_latched = False
        self._last_status = ""

        self._publish_estop(False)
        self._publish_zero_to_all()
        self._publish_status(force=True)
        self.get_logger().info(
            "multi-robot teleop ready; robots=%s selected=%s cmd_vel_suffix=%s"
            % (
                ",".join(self._config.robots),
                self._selected_robot,
                self._config.cmd_vel_topic,
            )
        )

    def _declare_parameters(self) -> None:
        self.declare_parameter("robots", ["atlas", "vector"])
        self.declare_parameter("selected_robot", "atlas")
        self.declare_parameter("joy_topic", "/joy")
        self.declare_parameter("cmd_vel_topic", "cmd_vel")
        self.declare_parameter("status_topic", "~/status")
        self.declare_parameter("estop_topic", "teleop_estop")
        self.declare_parameter("require_enable_button", True)
        self.declare_parameter("enable_button", 4)
        self.declare_parameter("turbo_button", 5)
        self.declare_parameter("estop_button", 2)
        self.declare_parameter("clear_estop_button", 3)
        self.declare_parameter("axis_linear_x", 1)
        self.declare_parameter("axis_angular_z", 3)
        self.declare_parameter("select_buttons.atlas", 0)
        self.declare_parameter("select_buttons.vector", 1)
        self.declare_parameter("deadzone", 0.08)
        self.declare_parameter("publish_rate_hz", 20.0)
        self.declare_parameter("stale_joy_timeout_sec", 0.35)
        self.declare_parameter("scale_linear_x", 0.25)
        self.declare_parameter("scale_angular_z", 0.8)
        self.declare_parameter("scale_linear_x_turbo", 0.45)
        self.declare_parameter("scale_angular_z_turbo", 1.2)

    def _read_config(self) -> TeleopConfig:
        robots = tuple(str(item) for item in self.get_parameter("robots").value)
        if not robots:
            raise ValueError("robots parameter must contain at least one robot name")

        selected_robot = str(self.get_parameter("selected_robot").value)
        if selected_robot not in robots:
            raise ValueError(
                "selected_robot must be one of %s, got %s"
                % (", ".join(robots), selected_robot)
            )

        select_buttons = {
            robot: self._int_parameter(f"select_buttons.{robot}", index)
            for index, robot in enumerate(robots)
        }

        publish_rate_hz = self._positive_float_parameter("publish_rate_hz")
        stale_timeout = self._positive_float_parameter("stale_joy_timeout_sec")
        deadzone = self._bounded_float_parameter("deadzone", 0.0, 1.0)

        return TeleopConfig(
            robots=robots,
            cmd_vel_topic=self._topic_suffix_parameter("cmd_vel_topic"),
            joy_topic=self._absolute_topic_parameter("joy_topic"),
            status_topic=str(self.get_parameter("status_topic").value),
            estop_topic=self._topic_suffix_parameter("estop_topic"),
            selected_robot=selected_robot,
            require_enable_button=bool(self.get_parameter("require_enable_button").value),
            enable_button=self._int_parameter("enable_button"),
            turbo_button=self._int_parameter("turbo_button"),
            estop_button=self._int_parameter("estop_button"),
            clear_estop_button=self._int_parameter("clear_estop_button"),
            axis_linear_x=self._int_parameter("axis_linear_x"),
            axis_angular_z=self._int_parameter("axis_angular_z"),
            select_buttons=select_buttons,
            deadzone=deadzone,
            publish_rate_hz=publish_rate_hz,
            stale_joy_timeout_sec=stale_timeout,
            limits=MotionLimits(
                linear_x=self._non_negative_float_parameter("scale_linear_x"),
                angular_z=self._non_negative_float_parameter("scale_angular_z"),
                turbo_linear_x=self._non_negative_float_parameter("scale_linear_x_turbo"),
                turbo_angular_z=self._non_negative_float_parameter("scale_angular_z_turbo"),
            ),
        )

    def _on_set_parameters(
        self,
        parameters: list[Parameter],
    ) -> SetParametersResult:
        allowed = {
            "selected_robot",
            "scale_linear_x",
            "scale_angular_z",
            "scale_linear_x_turbo",
            "scale_angular_z_turbo",
            "deadzone",
        }
        names = {parameter.name for parameter in parameters}
        unsupported = names - allowed
        if unsupported:
            return SetParametersResult(
                successful=False,
                reason="parameters are not runtime mutable: %s"
                % ", ".join(sorted(unsupported)),
            )

        for parameter in parameters:
            if parameter.name == "selected_robot":
                robot = str(parameter.value)
                if robot not in self._config.robots:
                    return SetParametersResult(
                        successful=False,
                        reason="selected_robot must be one of %s"
                        % ", ".join(self._config.robots),
                    )
            elif parameter.name == "deadzone":
                value = float(parameter.value)
                if value < 0.0 or value > 1.0:
                    return SetParametersResult(
                        successful=False,
                        reason="deadzone must be between 0.0 and 1.0",
                    )
            else:
                if float(parameter.value) < 0.0:
                    return SetParametersResult(
                        successful=False,
                        reason=f"{parameter.name} must be non-negative",
                    )

        for parameter in parameters:
            if parameter.name == "selected_robot":
                self._apply_selected_robot(str(parameter.value))
            elif parameter.name == "deadzone":
                self._config = replace(self._config, deadzone=float(parameter.value))
            elif parameter.name == "scale_linear_x":
                self._config = replace(
                    self._config,
                    limits=replace(
                        self._config.limits,
                        linear_x=float(parameter.value),
                    ),
                )
            elif parameter.name == "scale_angular_z":
                self._config = replace(
                    self._config,
                    limits=replace(
                        self._config.limits,
                        angular_z=float(parameter.value),
                    ),
                )
            elif parameter.name == "scale_linear_x_turbo":
                self._config = replace(
                    self._config,
                    limits=replace(
                        self._config.limits,
                        turbo_linear_x=float(parameter.value),
                    ),
                )
            elif parameter.name == "scale_angular_z_turbo":
                self._config = replace(
                    self._config,
                    limits=replace(
                        self._config.limits,
                        turbo_angular_z=float(parameter.value),
                    ),
                )

        return SetParametersResult(successful=True)

    def _on_joy(self, msg: Joy) -> None:
        previous_buttons = self._last_buttons
        self._last_buttons = list(msg.buttons)
        self._last_joy = msg
        self._last_joy_time = self.get_clock().now()

        if self._rising_edge(self._config.estop_button, msg.buttons, previous_buttons):
            self._estop_latched = True
            self._publish_estop(True)
            self._publish_zero_to_all()
            self.get_logger().warn("teleop e-stop latched")

        if self._rising_edge(self._config.clear_estop_button, msg.buttons, previous_buttons):
            self._estop_latched = False
            self._publish_estop(False)
            self.get_logger().info("teleop e-stop cleared")

        for robot, button in self._config.select_buttons.items():
            if self._rising_edge(button, msg.buttons, previous_buttons):
                self._select_robot(robot)

    def _on_timer(self) -> None:
        if self._last_joy_time is None or self._joy_is_stale():
            self._last_cmd = Twist()
            self._publish_zero_to_all()
            self._publish_status()
            return

        if self._last_joy is None or self._estop_latched:
            self._last_cmd = Twist()
            self._publish_zero_to_all()
            self._publish_status()
            return

        cmd = self._twist_from_joy(self._last_joy)
        self._last_cmd = cmd

        if self._is_zero_twist(cmd):
            self._publish_zero_to_all()
        else:
            self._publish_zero_to_unselected()
            self._cmd_publishers[self._selected_robot].publish(cmd)

        self._publish_status()

    def _twist_from_joy(self, msg: Joy) -> Twist:
        if self._config.require_enable_button and not self._button_pressed(
            self._config.enable_button,
            msg.buttons,
        ):
            return Twist()

        turbo = self._button_pressed(self._config.turbo_button, msg.buttons)
        linear_scale = (
            self._config.limits.turbo_linear_x
            if turbo
            else self._config.limits.linear_x
        )
        angular_scale = (
            self._config.limits.turbo_angular_z
            if turbo
            else self._config.limits.angular_z
        )

        twist = Twist()
        twist.linear.x = self._axis_value(msg.axes, self._config.axis_linear_x) * linear_scale
        twist.angular.z = self._axis_value(msg.axes, self._config.axis_angular_z) * angular_scale
        return twist

    def _select_robot(self, robot: str) -> None:
        if robot == self._selected_robot:
            return
        self.set_parameters([Parameter("selected_robot", value=robot)])

    def _apply_selected_robot(self, robot: str) -> None:
        if robot == self._selected_robot:
            return
        old_robot = self._selected_robot
        self._selected_robot = robot
        self._publish_zero(old_robot)
        self._publish_zero(robot)
        self.get_logger().info(f"selected robot changed: {old_robot} -> {robot}")
        self._publish_status(force=True)

    def _joy_is_stale(self) -> bool:
        if self._last_joy_time is None:
            return True
        elapsed = (self.get_clock().now() - self._last_joy_time).nanoseconds / 1e9
        return elapsed > self._config.stale_joy_timeout_sec

    def _publish_zero_to_all(self) -> None:
        for robot in self._config.robots:
            self._publish_zero(robot)

    def _publish_zero_to_unselected(self) -> None:
        for robot in self._config.robots:
            if robot != self._selected_robot:
                self._publish_zero(robot)

    def _publish_zero(self, robot: str) -> None:
        self._cmd_publishers[robot].publish(Twist())

    def _publish_estop(self, value: bool) -> None:
        msg = Bool()
        msg.data = value
        for publisher in self._estop_state_publishers.values():
            publisher.publish(msg)

    def _publish_status(self, *, force: bool = False) -> None:
        enabled = (
            self._last_joy is not None
            and not self._joy_is_stale()
            and (
                not self._config.require_enable_button
                or self._button_pressed(self._config.enable_button, self._last_joy.buttons)
            )
        )
        status = (
            f"selected={self._selected_robot} "
            f"enabled={str(enabled).lower()} "
            f"estop={str(self._estop_latched).lower()} "
            f"linear_x={self._last_cmd.linear.x:.3f} "
            f"angular_z={self._last_cmd.angular.z:.3f}"
        )
        if not force and status == self._last_status:
            return
        msg = String()
        msg.data = status
        self._status_publisher.publish(msg)
        self._last_status = status

    def _button_pressed(self, index: int, buttons: list[int] | tuple[int, ...]) -> bool:
        if index < 0 or index >= len(buttons):
            return False
        return bool(buttons[index])

    def _rising_edge(
        self,
        index: int,
        buttons: list[int] | tuple[int, ...],
        previous_buttons: list[int],
    ) -> bool:
        return self._button_pressed(index, buttons) and not self._button_pressed(
            index,
            previous_buttons,
        )

    def _axis_value(self, axes: list[float] | tuple[float, ...], index: int) -> float:
        if index < 0 or index >= len(axes):
            return 0.0
        value = float(axes[index])
        if abs(value) < self._config.deadzone:
            return 0.0
        return max(-1.0, min(1.0, value))

    def _positive_float_parameter(self, name: str) -> float:
        value = float(self.get_parameter(name).value)
        if value <= 0.0:
            raise ValueError(f"{name} must be positive")
        return value

    def _non_negative_float_parameter(self, name: str) -> float:
        value = float(self.get_parameter(name).value)
        if value < 0.0:
            raise ValueError(f"{name} must be non-negative")
        return value

    def _bounded_float_parameter(self, name: str, lower: float, upper: float) -> float:
        value = float(self.get_parameter(name).value)
        if value < lower or value > upper:
            raise ValueError(f"{name} must be between {lower} and {upper}")
        return value

    def _int_parameter(self, name: str, default: int | None = None) -> int:
        if self.has_parameter(name):
            return int(self.get_parameter(name).value)
        if default is None:
            raise ValueError(f"missing required integer parameter: {name}")
        self.declare_parameter(name, default)
        return default

    def _absolute_topic_parameter(self, name: str) -> str:
        value = str(self.get_parameter(name).value).strip()
        if not value.startswith("/"):
            raise ValueError(f"{name} must be an absolute topic")
        return value

    def _topic_suffix_parameter(self, name: str) -> str:
        value = str(self.get_parameter(name).value).strip()
        if not value:
            raise ValueError(f"{name} must not be empty")
        if value.startswith("/"):
            value = value[1:]
        if not value:
            raise ValueError(f"{name} must contain a topic name")
        return value

    @staticmethod
    def _robot_topic(robot: str, suffix: str) -> str:
        return f"/{robot}/{suffix.lstrip('/')}"

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
    node = MultiRobotTeleop()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
