import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pi_peripheral_lab.hardware_adapters import dac_adapter
from pi_peripheral_lab.hardware_adapters import i2c_bus
from pi_peripheral_lab.node_common import as_bool
from pi_peripheral_lab.node_common import declare_and_get
from pi_peripheral_lab.node_common import json_string
from pi_peripheral_lab.node_common import parse_json_string
from pi_peripheral_lab.node_common import timer_period_from_hz
from pi_peripheral_lab.waveform import sine_phase_value
from pi_peripheral_lab.waveform import step_phase_value
from pi_peripheral_lab.waveform import triangle_phase_value


class DacOutputNode(Node):
    def __init__(self, **kwargs):
        super().__init__("dac_output_node", namespace="/pin_lab", **kwargs)
        self._dry_run = as_bool(declare_and_get(self, "dry_run", True))
        self._backend = str(declare_and_get(self, "backend", "dry"))
        self._address = int(str(declare_and_get(self, "address", "0x60")), 0)
        self._reference_voltage = float(declare_and_get(self, "reference_voltage", 3.3))
        self._waveform = str(declare_and_get(self, "waveform", "triangle"))
        self._frequency_hz = float(declare_and_get(self, "frequency_hz", 0.5))
        self._update_hz = float(declare_and_get(self, "update_hz", 20.0))
        bus = None
        if not self._dry_run and self._backend == "mcp4725":
            bus = i2c_bus(False, 1)
        self._dac = dac_adapter(self._dry_run, self._backend, self._reference_voltage, bus=bus, address=self._address)
        self._publisher = self.create_publisher(String, "dac", 10)
        self.create_subscription(String, "joy_control", self._on_joy_control, 10)
        self._tick = 0
        self._timer = self.create_timer(timer_period_from_hz(self._update_hz), self._on_timer)

    def _on_joy_control(self, msg: String) -> None:
        try:
            data = parse_json_string(msg)
            voltage = data.get("dac_voltage")
            if voltage is not None:
                self._dac.set_voltage(float(voltage))
                self._publish(float(voltage), "joy")
        except (ValueError, TypeError) as exc:
            self.get_logger().warn(f"ignoring invalid joy_control DAC command: {exc}")

    def _waveform_voltage(self) -> float:
        phase = self._tick * self._frequency_hz / self._update_hz
        if self._waveform == "step":
            return step_phase_value(phase, 0.0, self._reference_voltage)
        if self._waveform == "sine":
            return sine_phase_value(phase, 0.0, self._reference_voltage)
        return triangle_phase_value(phase, 0.0, self._reference_voltage)

    def _publish(self, voltage: float, source: str) -> None:
        self._publisher.publish(
            json_string(
                {
                    "dry_run": self._dry_run,
                    "backend": self._backend,
                    "address": f"0x{self._address:02X}",
                    "reference_voltage": self._reference_voltage,
                    "voltage": voltage,
                    "source": source,
                }
            )
        )

    def _on_timer(self) -> None:
        voltage = self._waveform_voltage()
        self._dac.set_voltage(voltage)
        self._publish(voltage, self._waveform)
        self._tick += 1


def main(args=None):
    rclpy.init(args=args)
    node = DacOutputNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
