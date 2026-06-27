import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import can_bus
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import timer_period_from_hz
from pi_peripheral_lab.protocol_bits import bytes_to_hex


class CanReceiverNode(Node):
    def __init__(self, **kwargs):
        super().__init__("can_receiver_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._channel = str(declare_and_get(self, "channel", "dry_can_lab"))
        self._bitrate = int(declare_and_get(self, "bitrate", 500000))
        self._poll_hz = float(declare_and_get(self, "poll_hz", 20.0))
        self._bus = can_bus(self._dry_run, self._channel, self._bitrate)
        self._publisher = self.create_publisher(String, "can/rx", 10)
        self._timer = self.create_timer(timer_period_from_hz(self._poll_hz), self._on_timer)

    def _on_timer(self) -> None:
        frame = self._bus.recv(timeout=0.0)
        if frame is None:
            return
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "channel": self._channel,
                    "bitrate": self._bitrate,
                    "identifier": f"0x{int(frame.arbitration_id):X}",
                    "payload": bytes_to_hex(frame.data),
                    "extended": bool(getattr(frame, "is_extended_id", False)),
                }
            )
        )


def main(args=None):
    rclpy.init(args=args)
    node = CanReceiverNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
