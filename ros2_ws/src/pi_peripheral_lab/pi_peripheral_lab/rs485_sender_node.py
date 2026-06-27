import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import serial_port
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import parse_json_string
from pi_peripheral_lab.node_common import timer_period_from_hz
from pi_peripheral_lab.protocol_bits import rs485_lab_frame


class Rs485SenderNode(Node):
    def __init__(self, **kwargs):
        super().__init__("rs485_sender_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._port = str(declare_and_get(self, "port", "dry_rs485_lab"))
        self._baud_rate = int(declare_and_get(self, "baud_rate", 115200))
        self._address = int(declare_and_get(self, "address", 1))
        self._payload = str(declare_and_get(self, "payload", "rs485-lab"))
        self._rate_hz = float(declare_and_get(self, "rate_hz", 1.0))
        self._serial = serial_port(self._dry_run, self._port, self._baud_rate)
        self._publisher = self.create_publisher(String, "rs485/tx", 10)
        self.create_subscription(String, "joy_control", self._on_joy_control, 10)
        self._timer = self.create_timer(timer_period_from_hz(self._rate_hz), self._on_timer)

    def _on_joy_control(self, msg: String) -> None:
        try:
            data = parse_json_string(msg)
            payload = data.get("rs485_payload")
            if payload:
                self._payload = str(payload)
        except (ValueError, TypeError) as exc:
            self.get_logger().warn(f"ignoring invalid joy_control RS485 command: {exc}")

    def _on_timer(self) -> None:
        frame = rs485_lab_frame(self._payload.encode("utf-8"), self._address)
        self._serial.write(frame)
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "port": self._port,
                    "baud_rate": self._baud_rate,
                    "address": self._address,
                    "payload": self._payload,
                    "frame_hex": frame.hex(" "),
                }
            )
        )


def main(args=None):
    rclpy.init(args=args)
    node = Rs485SenderNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
