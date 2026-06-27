"""Hardware adapters with lazy imports.

Dry-run adapters are used by default and by automated tests. Real adapters only
import optional hardware libraries when a launch explicitly sets dry_run=false.
"""

from collections import deque
from collections.abc import Iterable
import math
import threading
import time

from pi_peripheral_lab.circuit_models import voltage_to_adc_code
from pi_peripheral_lab.dry_gpio import DryGPIOChip
from pi_peripheral_lab.dry_gpio import DryPWMChannel
from pi_peripheral_lab.protocol_bits import parse_hex_bytes
from pi_peripheral_lab.waveform import clamp


_DRY_GPIO_CHIP = DryGPIOChip()
_DRY_SERIAL_BUSES: dict[str, deque[int]] = {}


class MissingHardwareDependency(RuntimeError):
    pass


def _missing_dependency(package: str, feature: str) -> MissingHardwareDependency:
    return MissingHardwareDependency(
        f"{feature} requires optional hardware package {package!r}. "
        "Install it on the target only when running the matching HIL lab."
    )


class GpiodPin:
    """Small compatibility wrapper for libgpiod v1/v2 output/input lines."""

    def __init__(self, bcm: int, direction: str, initial: int = 0, chip_path: str = "/dev/gpiochip0"):
        try:
            import gpiod
        except ImportError as exc:
            raise _missing_dependency("python3-libgpiod", "GPIO hardware access") from exc

        self._gpiod = gpiod
        self._bcm = bcm
        self._request = None
        self._line = None

        if hasattr(gpiod, "request_lines"):
            direction_enum = getattr(gpiod.line.Direction, direction.upper())
            settings_kwargs = {"direction": direction_enum}
            if direction == "output":
                settings_kwargs["output_value"] = (
                    gpiod.line.Value.ACTIVE if initial else gpiod.line.Value.INACTIVE
                )
            settings = gpiod.LineSettings(**settings_kwargs)
            self._request = gpiod.request_lines(
                chip_path,
                consumer="pi_peripheral_lab",
                config={bcm: settings},
            )
        else:
            chip = gpiod.Chip(chip_path)
            line = chip.get_line(bcm)
            if direction == "output":
                line.request(
                    consumer="pi_peripheral_lab",
                    type=gpiod.LINE_REQ_DIR_OUT,
                    default_vals=[1 if initial else 0],
                )
            else:
                line.request(consumer="pi_peripheral_lab", type=gpiod.LINE_REQ_DIR_IN)
            self._line = line

    def set_value(self, value: int) -> None:
        value = 1 if value else 0
        if self._request is not None:
            line_value = (
                self._gpiod.line.Value.ACTIVE if value else self._gpiod.line.Value.INACTIVE
            )
            self._request.set_value(self._bcm, line_value)
            return
        self._line.set_value(value)

    def read(self) -> int:
        if self._request is not None:
            value = self._request.get_value(self._bcm)
            return 1 if str(value).endswith("ACTIVE") or value == 1 else 0
        return int(self._line.get_value())

    def close(self) -> None:
        if self._request is not None:
            self._request.release()
        elif self._line is not None:
            self._line.release()


class SoftwarePWM:
    """Threaded GPIO PWM for teaching waveforms, not precision motor control."""

    def __init__(self, pin, bcm: int):
        self._pin = pin
        self.bcm = bcm
        self.frequency_hz = 100.0
        self.duty_cycle = 0.0
        self.enabled = False
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def start(self) -> None:
        self.enabled = True

    def stop(self) -> None:
        self.enabled = False
        self._pin.set_value(0)

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)
        close = getattr(self._pin, "close", None)
        if close is not None:
            close()

    def set(self, frequency_hz: float, duty_cycle: float) -> None:
        if frequency_hz <= 0.0:
            raise ValueError("frequency_hz must be positive")
        self.frequency_hz = frequency_hz
        self.duty_cycle = clamp(duty_cycle, 0.0, 1.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            if not self.enabled or self.duty_cycle <= 0.0:
                self._pin.set_value(0)
                time.sleep(0.02)
                continue
            if self.duty_cycle >= 1.0:
                self._pin.set_value(1)
                time.sleep(0.02)
                continue
            period = 1.0 / self.frequency_hz
            high_time = period * self.duty_cycle
            low_time = period - high_time
            self._pin.set_value(1)
            time.sleep(high_time)
            self._pin.set_value(0)
            time.sleep(low_time)


def gpio_output(dry_run: bool, bcm: int, initial: int = 0):
    if dry_run:
        pin = _DRY_GPIO_CHIP.pin(bcm)
        pin.configure("output", initial=initial)
        return pin
    return GpiodPin(bcm, "output", initial=initial)


def gpio_input(dry_run: bool, bcm: int, pull: str = "none"):
    if dry_run:
        pin = _DRY_GPIO_CHIP.pin(bcm)
        pin.configure("input", pull=pull)
        return pin
    return GpiodPin(bcm, "input")


def pwm_channel(dry_run: bool, bcm: int):
    if dry_run:
        return DryPWMChannel(bcm=bcm)
    return SoftwarePWM(gpio_output(False, bcm, initial=0), bcm=bcm)


class DrySerialPort:
    def __init__(self, port: str):
        self.port = port
        self._buffer = _DRY_SERIAL_BUSES.setdefault(port, deque())

    def write(self, data: bytes) -> int:
        self._buffer.extend(data)
        return len(data)

    def read(self, size: int = 1) -> bytes:
        data = bytearray()
        for _ in range(max(size, 0)):
            if not self._buffer:
                break
            data.append(self._buffer.popleft())
        return bytes(data)

    def close(self) -> None:
        pass


def serial_port(dry_run: bool, port: str, baud_rate: int, timeout_sec: float = 0.02):
    if dry_run:
        return DrySerialPort(port)
    try:
        import serial
    except ImportError as exc:
        raise _missing_dependency("python3-serial", "UART/RS485 serial access") from exc
    return serial.Serial(port=port, baudrate=baud_rate, timeout=timeout_sec)


class DrySpiBus:
    def xfer2(self, payload: list[int]) -> list[int]:
        return [byte & 0xFF for byte in payload]

    def close(self) -> None:
        pass


def spi_bus(dry_run: bool, bus: int, device: int, max_speed_hz: int, mode: int = 0):
    if dry_run:
        return DrySpiBus()
    try:
        import spidev
    except ImportError as exc:
        raise _missing_dependency("python3-spidev", "SPI access") from exc
    spi = spidev.SpiDev()
    spi.open(bus, device)
    spi.max_speed_hz = max_speed_hz
    spi.mode = mode
    return spi


class DryI2CBus:
    def __init__(self, present_addresses: Iterable[int] = (0x48, 0x60)):
        self.present_addresses = set(present_addresses)
        self.writes: list[tuple[int, list[int]]] = []

    def read_byte(self, address: int) -> int:
        if address not in self.present_addresses:
            raise OSError("dry I2C NACK")
        return 0

    def write_i2c_block_data(self, address: int, register: int, data: list[int]) -> None:
        if address not in self.present_addresses:
            raise OSError("dry I2C NACK")
        self.writes.append((address, [register, *data]))

    def close(self) -> None:
        pass


def i2c_bus(dry_run: bool, bus: int, dry_addresses: Iterable[int] = (0x48, 0x60)):
    if dry_run:
        return DryI2CBus(dry_addresses)
    try:
        from smbus2 import SMBus
    except ImportError:
        try:
            from smbus import SMBus
        except ImportError as exc:
            raise _missing_dependency("python3-smbus or python3-smbus2", "I2C access") from exc
    return SMBus(bus)


class DryAdc:
    def __init__(self, bits: int, reference_voltage: float):
        self.bits = bits
        self.reference_voltage = reference_voltage
        self._start = time.monotonic()

    def read_channel(self, channel: int) -> tuple[int, float]:
        phase = (time.monotonic() - self._start) % 1.0
        voltage = (0.5 + 0.5 * math.sin(2.0 * math.pi * phase)) * self.reference_voltage
        return voltage_to_adc_code(voltage, self.bits, self.reference_voltage), voltage


class Mcp3008Adc:
    def __init__(self, spi, reference_voltage: float):
        self._spi = spi
        self.reference_voltage = reference_voltage

    def read_channel(self, channel: int) -> tuple[int, float]:
        if channel < 0 or channel > 7:
            raise ValueError("MCP3008 channel must be 0..7")
        response = self._spi.xfer2([1, (8 + channel) << 4, 0])
        code = ((response[1] & 0x03) << 8) | response[2]
        voltage = code * self.reference_voltage / 1023.0
        return code, voltage


def adc_adapter(
    dry_run: bool,
    backend: str,
    reference_voltage: float,
    spi=None,
    bits: int = 12,
):
    if dry_run or backend == "dry":
        return DryAdc(bits=bits, reference_voltage=reference_voltage)
    if backend == "mcp3008":
        if spi is None:
            raise ValueError("mcp3008 ADC requires an SPI bus")
        return Mcp3008Adc(spi, reference_voltage)
    raise ValueError(f"unsupported ADC backend: {backend}")


class DryDac:
    def __init__(self, reference_voltage: float):
        self.reference_voltage = reference_voltage
        self.last_voltage = 0.0

    def set_voltage(self, voltage: float) -> None:
        self.last_voltage = clamp(voltage, 0.0, self.reference_voltage)


class Mcp4725Dac:
    def __init__(self, bus, address: int, reference_voltage: float):
        self._bus = bus
        self.address = address
        self.reference_voltage = reference_voltage

    def set_voltage(self, voltage: float) -> None:
        code = int(round(clamp(voltage, 0.0, self.reference_voltage) / self.reference_voltage * 4095))
        self._bus.write_i2c_block_data(self.address, 0x40, [(code >> 4) & 0xFF, (code & 0x0F) << 4])


def dac_adapter(dry_run: bool, backend: str, reference_voltage: float, bus=None, address: int = 0x60):
    if dry_run or backend == "dry":
        return DryDac(reference_voltage)
    if backend == "mcp4725":
        if bus is None:
            raise ValueError("mcp4725 DAC requires an I2C bus")
        return Mcp4725Dac(bus, address, reference_voltage)
    raise ValueError(f"unsupported DAC backend: {backend}")


class DryCanBus:
    def __init__(self, channel: str):
        self.channel = channel
        self._buffer = _DRY_SERIAL_BUSES.setdefault(f"can:{channel}", deque())

    def send(self, message) -> None:
        self._buffer.append(message)

    def recv(self, timeout: float = 0.0):
        deadline = time.monotonic() + max(timeout, 0.0)
        while time.monotonic() <= deadline:
            if self._buffer:
                return self._buffer.popleft()
            time.sleep(0.005)
        return self._buffer.popleft() if self._buffer else None

    def shutdown(self) -> None:
        pass


class DryCanMessage:
    def __init__(self, arbitration_id: int, data: bytes, is_extended_id: bool = False):
        self.arbitration_id = arbitration_id
        self.data = data
        self.is_extended_id = is_extended_id


def can_bus(dry_run: bool, channel: str, bitrate: int, bustype: str = "socketcan"):
    if dry_run:
        return DryCanBus(channel)
    try:
        import can
    except ImportError as exc:
        raise _missing_dependency("python3-can", "CAN access") from exc
    return can.interface.Bus(channel=channel, bustype=bustype, bitrate=bitrate)


def can_message(dry_run: bool, arbitration_id: int, data: bytes, extended: bool = False):
    if dry_run:
        return DryCanMessage(arbitration_id, data, extended)
    try:
        import can
    except ImportError as exc:
        raise _missing_dependency("python3-can", "CAN message creation") from exc
    return can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=extended)


def parse_payload_bytes(payload: str) -> bytes:
    return bytes(parse_hex_bytes(payload))
