import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import adc_adapter
from pi_peripheral_lab.hardware_adapters import spi_bus
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import timer_period_from_hz


class AdcReaderNode(Node):
    def __init__(self, **kwargs):
        super().__init__("adc_reader_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._backend = str(declare_and_get(self, "backend", "dry"))
        self._channel = int(declare_and_get(self, "channel", 0))
        self._reference_voltage = float(declare_and_get(self, "reference_voltage", 3.3))
        self._bits = int(declare_and_get(self, "bits", 12))
        self._rate_hz = float(declare_and_get(self, "sample_rate_hz", 10.0))
        spi = None
        if not self._dry_run and self._backend == "mcp3008":
            spi = spi_bus(False, 0, 0, 500000, 0)
            self._bits = 10
        self._adc = adc_adapter(self._dry_run, self._backend, self._reference_voltage, spi=spi, bits=self._bits)
        self._publisher = self.create_publisher(String, "adc", 10)
        self._timer = self.create_timer(timer_period_from_hz(self._rate_hz), self._on_timer)

    def _on_timer(self) -> None:
        code, voltage = self._adc.read_channel(self._channel)
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "backend": self._backend,
                    "channel": self._channel,
                    "code": code,
                    "bits": self._bits,
                    "reference_voltage": self._reference_voltage,
                    "voltage": voltage,
                    "sample_rate_hz": self._rate_hz,
                }
            )
        )


def main(args=None):
    rclpy.init(args=args)
    node = AdcReaderNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
