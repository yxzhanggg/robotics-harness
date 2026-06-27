import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import pwm_channel
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import parse_json_string
from pi_peripheral_lab.pin_map import assert_gpio_is_lab_safe
from pi_peripheral_lab.waveform import PwmCommand


class PwmScopeNode(Node):
    def __init__(self, **kwargs):
        super().__init__("pwm_scope_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._bcm = int(declare_and_get(self, "gpio_bcm", 18))
        self._min_frequency_hz = float(declare_and_get(self, "min_frequency_hz", 10.0))
        self._max_frequency_hz = float(declare_and_get(self, "max_frequency_hz", 1000.0))
        frequency_hz = float(declare_and_get(self, "frequency_hz", 100.0))
        duty_cycle = float(declare_and_get(self, "duty_cycle", 0.5))
        assert_gpio_is_lab_safe(self._bcm)

        self._pwm = pwm_channel(self._dry_run, self._bcm)
        self._publisher = self.create_publisher(String, "pwm/status", 10)
        self.create_subscription(String, "joy_control", self._on_joy_control, 10)
        self._set_pwm(PwmCommand(frequency_hz, duty_cycle))
        self._timer = self.create_timer(0.5, self._publish_status)

    def _set_pwm(self, command: PwmCommand) -> None:
        self._command = command.sanitized(self._min_frequency_hz, self._max_frequency_hz)
        self._pwm.set(self._command.frequency_hz, self._command.duty_cycle)
        self._pwm.start()

    def _on_joy_control(self, msg: String) -> None:
        try:
            data = parse_json_string(msg)
            pwm = data.get("pwm", {})
            self._set_pwm(
                PwmCommand(
                    frequency_hz=float(pwm.get("frequency_hz", self._command.frequency_hz)),
                    duty_cycle=float(pwm.get("duty_cycle", self._command.duty_cycle)),
                )
            )
        except (ValueError, TypeError, KeyError) as exc:
            self.get_logger().warn(f"ignoring invalid joy_control PWM command: {exc}")

    def _publish_status(self) -> None:
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "gpio_bcm": self._bcm,
                    "frequency_hz": self._command.frequency_hz,
                    "duty_cycle": self._command.duty_cycle,
                }
            )
        )

    def destroy_node(self):
        close = getattr(self._pwm, "close", None)
        if close is not None:
            close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PwmScopeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
