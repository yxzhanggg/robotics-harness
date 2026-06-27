import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import serial_port
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import timer_period_from_hz


class UartRxNode(Node):
    def __init__(self, **kwargs):
        super().__init__("uart_rx_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._port = str(declare_and_get(self, "port", "dry_uart_atlas_vector"))
        self._baud_rate = int(declare_and_get(self, "baud_rate", 115200))
        self._poll_hz = float(declare_and_get(self, "poll_hz", 20.0))
        self._serial = serial_port(self._dry_run, self._port, self._baud_rate)
        self._publisher = self.create_publisher(String, "uart/rx", 10)
        self._timer = self.create_timer(timer_period_from_hz(self._poll_hz), self._on_timer)

    def _on_timer(self) -> None:
        data = self._serial.read(256)
        if not data:
            return
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "port": self._port,
                    "baud_rate": self._baud_rate,
                    "hex": data.hex(" "),
                    "text": data.decode("utf-8", errors="replace"),
                }
            )
        )


def main(args=None):
    rclpy.init(args=args)
    node = UartRxNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
