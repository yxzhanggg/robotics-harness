from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from rcl_interfaces.msg import Log
import rclpy
from rclpy.node import Node


class RosoutCollector(Node):
    def __init__(self) -> None:
        super().__init__("rosout_collector")
        self.declare_parameter("output_file", "/home/zyx/robotics_ws/log/central/rosout.jsonl")
        output_file = str(self.get_parameter("output_file").value)
        self._output_path = Path(output_file).expanduser()
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self._output_path.open("a", encoding="utf-8")
        self._subscription = self.create_subscription(Log, "/rosout", self._on_log, 100)
        self.get_logger().info(f"collecting /rosout to {self._output_path}")

    def _on_log(self, msg: Log) -> None:
        record = {
            "received_utc": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "stamp": {"sec": msg.stamp.sec, "nanosec": msg.stamp.nanosec},
            "level": msg.level,
            "name": msg.name,
            "file": msg.file,
            "function": msg.function,
            "line": msg.line,
            "message": msg.msg,
        }
        self._handle.write(json.dumps(record, sort_keys=True) + "\n")
        self._handle.flush()

    def destroy_node(self) -> bool:
        if not self._handle.closed:
            self._handle.close()
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = RosoutCollector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
