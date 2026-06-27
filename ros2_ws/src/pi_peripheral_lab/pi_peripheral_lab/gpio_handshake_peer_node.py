import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import gpio_input
from pi_peripheral_lab.hardware_adapters import gpio_output
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import timer_period_from_hz
from pi_peripheral_lab.pin_map import assert_gpio_is_lab_safe


class GpioHandshakePeerNode(Node):
    def __init__(self, **kwargs):
        super().__init__("gpio_handshake_peer_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._request_bcm = int(declare_and_get(self, "request_gpio_bcm", 27))
        self._ack_bcm = int(declare_and_get(self, "ack_gpio_bcm", 22))
        self._poll_hz = float(declare_and_get(self, "poll_hz", 50.0))
        assert_gpio_is_lab_safe(self._request_bcm)
        assert_gpio_is_lab_safe(self._ack_bcm)

        self._request = gpio_input(self._dry_run, self._request_bcm)
        self._ack = gpio_output(self._dry_run, self._ack_bcm, initial=0)
        self._tick = 0
        self._publisher = self.create_publisher(String, "gpio_handshake/peer", 10)
        self._timer = self.create_timer(timer_period_from_hz(self._poll_hz), self._on_timer)

    def _on_timer(self) -> None:
        if self._dry_run:
            self._request.inject_value((self._tick // 10) % 2)
        request = self._request.read()
        self._ack.set_value(request)
        if self._tick % 10 == 0:
            self._publisher.publish(
                json_string(
                    {
                        "dry_run": self._dry_run,
                        "tick": self._tick,
                        "request_gpio_bcm": self._request_bcm,
                        "ack_gpio_bcm": self._ack_bcm,
                        "request": request,
                        "ack": request,
                    }
                )
            )
        self._tick += 1


def main(args=None):
    rclpy.init(args=args)
    node = GpioHandshakePeerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
