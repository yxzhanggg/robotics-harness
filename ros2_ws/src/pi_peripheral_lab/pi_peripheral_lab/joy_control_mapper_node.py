import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import String

from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.waveform import JoyControl
from pi_peripheral_lab.waveform import clamp
from pi_peripheral_lab.waveform import drive_strength_from_trigger
from pi_peripheral_lab.waveform import pwm_from_joy


class JoyControlMapperNode(Node):
    def __init__(self, **kwargs):
        super().__init__("joy_control_mapper_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._duty_axis = int(declare_and_get(self, "duty_axis", 0))
        self._frequency_axis = int(declare_and_get(self, "frequency_axis", 3))
        self._trigger_axis = int(declare_and_get(self, "trigger_axis", 5))
        self._min_frequency_hz = float(declare_and_get(self, "min_frequency_hz", 10.0))
        self._max_frequency_hz = float(declare_and_get(self, "max_frequency_hz", 1000.0))
        self._reference_voltage = float(declare_and_get(self, "reference_voltage", 3.3))
        self._publisher = self.create_publisher(String, "joy_control", 10)
        self.create_subscription(Joy, "joy", self._on_joy, 10)
        if self._dry_run:
            self._timer = self.create_timer(1.0, self._publish_dry)

    def _axis(self, axes: list[float], index: int, default: float = 0.0) -> float:
        return axes[index] if 0 <= index < len(axes) else default

    def _button(self, buttons: list[int], index: int) -> bool:
        return bool(buttons[index]) if 0 <= index < len(buttons) else False

    def _publish_control(self, joy: JoyControl, buttons: list[int]) -> None:
        pwm = pwm_from_joy(joy, self._min_frequency_hz, self._max_frequency_hz)
        drive = drive_strength_from_trigger(joy.trigger_axis)
        payload = {
            "dry_run": self._dry_run,
            "pwm": {
                "duty_cycle": pwm.duty_cycle,
                "frequency_hz": pwm.frequency_hz,
            },
            "load_drive_strength": drive,
            "dac_voltage": clamp(drive * self._reference_voltage, 0.0, self._reference_voltage),
            "gpio_pattern": "heartbeat" if self._button(buttons, 0) else "square",
            "uart_payload": "ps5-cross" if self._button(buttons, 0) else "ps5-idle",
            "spi_payload_hex": "0xA5 0x5A" if self._button(buttons, 1) else "0xAA 0x55",
            "can_payload_hex": "0x01 0x05" if self._button(buttons, 2) else "0x50 0x49",
            "rs485_payload": "ps5-square" if self._button(buttons, 3) else "rs485-idle",
            "boundary": "lab controller only; does not publish cmd_vel, cmd_vel_safe, or production robot commands",
        }
        self._publisher.publish(json_string(payload))

    def _on_joy(self, msg: Joy) -> None:
        joy = JoyControl(
            duty_axis=self._axis(msg.axes, self._duty_axis),
            frequency_axis=self._axis(msg.axes, self._frequency_axis),
            trigger_axis=self._axis(msg.axes, self._trigger_axis),
            buttons=tuple(msg.buttons),
        )
        self._publish_control(joy, list(msg.buttons))

    def _publish_dry(self) -> None:
        self._publish_control(
            JoyControl(duty_axis=0.0, frequency_axis=0.0, trigger_axis=0.0, buttons=()),
            [],
        )


def main(args=None):
    rclpy.init(args=args)
    node = JoyControlMapperNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
