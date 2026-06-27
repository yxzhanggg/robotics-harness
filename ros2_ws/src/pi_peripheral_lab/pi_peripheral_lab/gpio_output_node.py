import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import gpio_output
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import timer_period_from_hz
from pi_peripheral_lab.pin_map import assert_gpio_is_lab_safe
from pi_peripheral_lab.waveform import pattern_bit


class GpioOutputNode(Node):
    def __init__(self, **kwargs):
        super().__init__("gpio_output_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._bcm = int(declare_and_get(self, "gpio_bcm", 17))
        self._pattern = str(declare_and_get(self, "pattern", "square"))
        self._rate_hz = float(declare_and_get(self, "rate_hz", 2.0))
        assert_gpio_is_lab_safe(self._bcm)

        self._pin = gpio_output(self._dry_run, self._bcm, initial=0)
        self._tick = 0
        self._publisher = self.create_publisher(String, "gpio_output/status", 10)
        self._timer = self.create_timer(timer_period_from_hz(self._rate_hz), self._on_timer)

    def _on_timer(self) -> None:
        value = pattern_bit(self._pattern, self._tick)
        self._pin.set_value(value)
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "gpio_bcm": self._bcm,
                    "pattern": self._pattern,
                    "tick": self._tick,
                    "value": value,
                }
            )
        )
        self._tick += 1

    def destroy_node(self):
        close = getattr(self._pin, "close", None)
        if close is not None:
            close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = GpioOutputNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
