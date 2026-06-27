import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import parse_payload_bytes
from pi_peripheral_lab.hardware_adapters import spi_bus
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import parse_json_string
from pi_peripheral_lab.node_common import timer_period_from_hz
from pi_peripheral_lab.protocol_bits import bytes_to_hex
from pi_peripheral_lab.protocol_bits import spi_bits


class SpiWaveNode(Node):
    def __init__(self, **kwargs):
        super().__init__("spi_wave_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._bus_id = int(declare_and_get(self, "bus", 0))
        self._device = int(declare_and_get(self, "device", 0))
        self._max_speed_hz = int(declare_and_get(self, "max_speed_hz", 500000))
        self._mode = int(declare_and_get(self, "mode", 0))
        self._payload = parse_payload_bytes(str(declare_and_get(self, "payload_hex", "0xAA 0x55")))
        self._rate_hz = float(declare_and_get(self, "rate_hz", 1.0))
        self._spi = spi_bus(self._dry_run, self._bus_id, self._device, self._max_speed_hz, self._mode)
        self._publisher = self.create_publisher(String, "spi/transfer", 10)
        self.create_subscription(String, "joy_control", self._on_joy_control, 10)
        self._timer = self.create_timer(timer_period_from_hz(self._rate_hz), self._on_timer)

    def _on_joy_control(self, msg: String) -> None:
        try:
            data = parse_json_string(msg)
            payload = data.get("spi_payload_hex")
            if payload:
                self._payload = parse_payload_bytes(str(payload))
        except (ValueError, TypeError) as exc:
            self.get_logger().warn(f"ignoring invalid joy_control SPI command: {exc}")

    def _on_timer(self) -> None:
        rx = self._spi.xfer2(list(self._payload))
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "bus": self._bus_id,
                    "device": self._device,
                    "mode": self._mode,
                    "max_speed_hz": self._max_speed_hz,
                    "tx": bytes_to_hex(self._payload),
                    "rx": bytes_to_hex(rx),
                    "mosi_bits_msb": spi_bits(self._payload, bit_order="msb"),
                }
            )
        )


def main(args=None):
    rclpy.init(args=args)
    node = SpiWaveNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
