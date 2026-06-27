import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import serial_port
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import timer_period_from_hz
from pi_peripheral_lab.protocol_bits import verify_rs485_lab_frame


class Rs485ReceiverNode(Node):
    def __init__(self, **kwargs):
        super().__init__("rs485_receiver_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._port = str(declare_and_get(self, "port", "dry_rs485_lab"))
        self._baud_rate = int(declare_and_get(self, "baud_rate", 115200))
        self._poll_hz = float(declare_and_get(self, "poll_hz", 20.0))
        self._serial = serial_port(self._dry_run, self._port, self._baud_rate)
        self._buffer = bytearray()
        self._publisher = self.create_publisher(String, "rs485/rx", 10)
        self._timer = self.create_timer(timer_period_from_hz(self._poll_hz), self._on_timer)

    def _on_timer(self) -> None:
        self._buffer.extend(self._serial.read(256))
        if len(self._buffer) < 4:
            return
        # Teaching frame uses one-byte length at offset 1.
        frame_len = 4 + self._buffer[1]
        if len(self._buffer) < frame_len:
            return
        frame = bytes(self._buffer[:frame_len])
        del self._buffer[:frame_len]
        try:
            address, payload = verify_rs485_lab_frame(frame)
            status = {
                "dry_run": self._dry_run,
                "port": self._port,
                "baud_rate": self._baud_rate,
                "address": address,
                "payload": payload.decode("utf-8", errors="replace"),
                "frame_hex": frame.hex(" "),
                "crc_ok": True,
            }
        except ValueError as exc:
            status = {
                "dry_run": self._dry_run,
                "port": self._port,
                "baud_rate": self._baud_rate,
                "frame_hex": frame.hex(" "),
                "crc_ok": False,
                "error": str(exc),
            }
        self._publisher.publish(json_string(status))


def main(args=None):
    rclpy.init(args=args)
    node = Rs485ReceiverNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
