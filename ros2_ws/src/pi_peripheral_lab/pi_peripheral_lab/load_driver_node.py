import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import pwm_channel
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import parse_json_string
from pi_peripheral_lab.pin_map import assert_gpio_is_lab_safe
from pi_peripheral_lab.waveform import clamp


class LoadDriverNode(Node):
    def __init__(self, **kwargs):
        super().__init__("load_driver_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._bcm = int(declare_and_get(self, "gate_gpio_bcm", 18))
        self._frequency_hz = float(declare_and_get(self, "frequency_hz", 200.0))
        self._duty_cycle = float(declare_and_get(self, "duty_cycle", 0.0))
        assert_gpio_is_lab_safe(self._bcm)
        self._pwm = pwm_channel(self._dry_run, self._bcm)
        self._pwm.set(self._frequency_hz, clamp(self._duty_cycle, 0.0, 1.0))
        self._pwm.start()
        self._publisher = self.create_publisher(String, "load_driver/status", 10)
        self.create_subscription(String, "joy_control", self._on_joy_control, 10)
        self._timer = self.create_timer(0.5, self._publish)

    def _on_joy_control(self, msg: String) -> None:
        try:
            data = parse_json_string(msg)
            drive = data.get("load_drive_strength")
            if drive is not None:
                self._duty_cycle = clamp(float(drive), 0.0, 1.0)
                self._pwm.set(self._frequency_hz, self._duty_cycle)
        except (ValueError, TypeError) as exc:
            self.get_logger().warn(f"ignoring invalid load drive command: {exc}")

    def _publish(self) -> None:
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "gate_gpio_bcm": self._bcm,
                    "frequency_hz": self._frequency_hz,
                    "duty_cycle": self._duty_cycle,
                    "safety": (
                        "Pi GPIO drives only the gate/base. Use external low-voltage "
                        "supply, common ground, gate resistor, pulldown, and flyback diode."
                    ),
                }
            )
        )


def main(args=None):
    rclpy.init(args=args)
    node = LoadDriverNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
