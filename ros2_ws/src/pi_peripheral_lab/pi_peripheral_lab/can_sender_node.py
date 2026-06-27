import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import can_bus
from pi_peripheral_lab.hardware_adapters import can_message
from pi_peripheral_lab.hardware_adapters import parse_payload_bytes
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import parse_json_string
from pi_peripheral_lab.node_common import timer_period_from_hz
from pi_peripheral_lab.protocol_bits import bytes_to_hex
from pi_peripheral_lab.protocol_bits import can_identifier_is_valid


class CanSenderNode(Node):
    def __init__(self, **kwargs):
        super().__init__("can_sender_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._channel = str(declare_and_get(self, "channel", "dry_can_lab"))
        self._bitrate = int(declare_and_get(self, "bitrate", 500000))
        self._identifier = int(str(declare_and_get(self, "identifier", "0x123")), 0)
        self._extended = as_bool(declare_and_get(self, "extended", False))
        self._payload = parse_payload_bytes(str(declare_and_get(self, "payload_hex", "0x50 0x49")))
        self._rate_hz = float(declare_and_get(self, "rate_hz", 1.0))
        if not can_identifier_is_valid(self._identifier, self._extended):
            raise ValueError("invalid CAN identifier")
        self._bus = can_bus(self._dry_run, self._channel, self._bitrate)
        self._publisher = self.create_publisher(String, "can/tx", 10)
        self.create_subscription(String, "joy_control", self._on_joy_control, 10)
        self._timer = self.create_timer(timer_period_from_hz(self._rate_hz), self._on_timer)

    def _on_joy_control(self, msg: String) -> None:
        try:
            data = parse_json_string(msg)
            payload = data.get("can_payload_hex")
            if payload:
                self._payload = parse_payload_bytes(str(payload))
        except (ValueError, TypeError) as exc:
            self.get_logger().warn(f"ignoring invalid joy_control CAN command: {exc}")

    def _on_timer(self) -> None:
        frame = can_message(self._dry_run, self._identifier, self._payload, self._extended)
        self._bus.send(frame)
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "channel": self._channel,
                    "bitrate": self._bitrate,
                    "identifier": f"0x{self._identifier:X}",
                    "payload": bytes_to_hex(self._payload),
                    "note": "This node requires real CAN hardware for physical-layer CAN; GPIO is not used as fake CAN.",
                }
            )
        )


def main(args=None):
    rclpy.init(args=args)
    node = CanSenderNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
