import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import i2c_bus
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import timer_period_from_hz
from pi_peripheral_lab.protocol_bits import i2c_7bit_address_is_valid


class I2cProbeNode(Node):
    def __init__(self, **kwargs):
        super().__init__("i2c_probe_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._bus_id = int(declare_and_get(self, "bus", 1))
        self._rate_hz = float(declare_and_get(self, "rate_hz", 0.2))
        dry_addresses = str(declare_and_get(self, "dry_addresses", "0x48 0x60"))
        self._bus = i2c_bus(
            self._dry_run,
            self._bus_id,
            dry_addresses=[int(token, 0) for token in dry_addresses.split()],
        )
        self._publisher = self.create_publisher(String, "i2c/probe", 10)
        self._timer = self.create_timer(timer_period_from_hz(self._rate_hz), self._on_timer)

    def _on_timer(self) -> None:
        found = []
        for address in range(0x03, 0x78):
            if not i2c_7bit_address_is_valid(address):
                continue
            try:
                self._bus.read_byte(address)
                found.append(address)
            except OSError:
                pass
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "bus": self._bus_id,
                    "found": [f"0x{address:02X}" for address in found],
                    "note": "I2C is open-drain; use pull-ups and avoid address conflicts.",
                }
            )
        )


def main(args=None):
    rclpy.init(args=args)
    node = I2cProbeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
