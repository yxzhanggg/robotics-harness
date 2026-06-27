import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.dry_gpio import EdgeCounter
from pi_peripheral_lab.hardware_adapters import gpio_input
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import timer_period_from_hz
from pi_peripheral_lab.pin_map import assert_gpio_is_lab_safe
from pi_peripheral_lab.waveform import frequency_stats


class FrequencyCounterNode(Node):
    def __init__(self, **kwargs):
        super().__init__("frequency_counter_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._bcm = int(declare_and_get(self, "gpio_bcm", 17))
        self._publish_hz = float(declare_and_get(self, "publish_hz", 1.0))
        self._dry_signal_hz = float(declare_and_get(self, "dry_signal_hz", 10.0))
        assert_gpio_is_lab_safe(self._bcm)
        self._pin = gpio_input(self._dry_run, self._bcm, pull="down")
        self._counter = EdgeCounter(edge="rising")
        self._last_value = int(self._pin.read())
        self._counter.observe(self._last_value)
        self._dry_tick = 0
        if hasattr(self._pin, "add_edge_callback"):
            self._pin.add_edge_callback(lambda value, stamp: self._counter.observe(value, stamp))
        self._publisher = self.create_publisher(String, "frequency", 10)
        self._sample_timer = self.create_timer(0.001 if self._dry_run else 0.002, self._sample_input)
        self._publish_timer = self.create_timer(timer_period_from_hz(self._publish_hz), self._publish)

    def _sample_input(self) -> None:
        if self._dry_run:
            self._dry_tick += 1
            half_period_ticks = max(1, int(500.0 / self._dry_signal_hz))
            self._pin.inject_value(1 if (self._dry_tick // half_period_ticks) % 2 else 0)
            return
        value = int(self._pin.read())
        if value != self._last_value:
            self._counter.observe(value)
            self._last_value = value

    def _publish(self) -> None:
        stats = frequency_stats(self._counter.timestamps_sec)
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "gpio_bcm": self._bcm,
                    "edge_count": self._counter.count,
                    "frequency_hz": stats["frequency_hz"],
                    "jitter_sec": stats["jitter_sec"],
                    "note": "Linux GPIO edge timing is educational only; use the oscilloscope as reference.",
                }
            )
        )
        self._counter.reset()
        self._last_value = int(self._pin.read())
        self._counter.observe(self._last_value)


def main(args=None):
    rclpy.init(args=args)
    node = FrequencyCounterNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
