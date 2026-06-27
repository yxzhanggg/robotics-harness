import math

import pytest

from pi_peripheral_lab.circuit_models import function_generator_settings_for_gpio
from pi_peripheral_lab.circuit_models import gpio_signal_check
from pi_peripheral_lab.circuit_models import rc_cutoff_hz
from pi_peripheral_lab.circuit_models import voltage_divider
from pi_peripheral_lab.circuit_models import voltage_to_adc_code
from pi_peripheral_lab.dry_gpio import DryGPIOChip
from pi_peripheral_lab.dry_gpio import DryPWMChannel
from pi_peripheral_lab.dry_gpio import EdgeCounter
from pi_peripheral_lab.pin_map import assert_gpio_is_lab_safe
from pi_peripheral_lab.pin_map import validate_gpio_input_voltage
from pi_peripheral_lab.pin_map import validate_series_resistor
from pi_peripheral_lab.protocol_bits import can_identifier_is_valid
from pi_peripheral_lab.protocol_bits import crc16_modbus
from pi_peripheral_lab.protocol_bits import parse_hex_bytes
from pi_peripheral_lab.protocol_bits import rs485_lab_frame
from pi_peripheral_lab.protocol_bits import uart_8n1_frame
from pi_peripheral_lab.protocol_bits import verify_rs485_lab_frame
from pi_peripheral_lab.waveform import JoyControl
from pi_peripheral_lab.waveform import SquareWave
from pi_peripheral_lab.waveform import axis_to_unit
from pi_peripheral_lab.waveform import frequency_stats
from pi_peripheral_lab.waveform import pattern_bit
from pi_peripheral_lab.waveform import pwm_from_joy


def test_pin_safety_rejects_reserved_and_unsafe_voltage():
    assert_gpio_is_lab_safe(17)
    assert validate_gpio_input_voltage(3.3) == 3.3
    assert validate_series_resistor(1_000.0) == 1_000.0

    with pytest.raises(ValueError):
        assert_gpio_is_lab_safe(0)
    with pytest.raises(ValueError):
        validate_gpio_input_voltage(5.0)
    with pytest.raises(ValueError):
        validate_series_resistor(100.0)


def test_waveform_helpers_and_joy_mapping():
    square = SquareWave(100.0, 0.25)
    assert square.period_sec == pytest.approx(0.01)
    assert square.high_time_sec == pytest.approx(0.0025)
    assert square.low_time_sec == pytest.approx(0.0075)
    assert axis_to_unit(-1.0) == 0.0
    assert axis_to_unit(1.0) == 1.0

    pwm = pwm_from_joy(JoyControl(duty_axis=1.0, frequency_axis=-1.0), 10.0, 1000.0)
    assert pwm.duty_cycle == 1.0
    assert pwm.frequency_hz == 10.0
    assert pattern_bit("heartbeat", 2) == 1


def test_frequency_stats():
    stats = frequency_stats([0.0, 0.1, 0.2, 0.3])
    assert stats["edge_count"] == 4.0
    assert stats["frequency_hz"] == pytest.approx(10.0)
    assert stats["jitter_sec"] == pytest.approx(0.0)


def test_protocol_bits_uart_rs485_and_can():
    assert uart_8n1_frame(0x55) == [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    assert parse_hex_bytes("0xAA, 0x55") == [0xAA, 0x55]
    assert crc16_modbus(b"123456789") == 0x4B37
    frame = rs485_lab_frame(b"hello", address=7)
    address, payload = verify_rs485_lab_frame(frame)
    assert address == 7
    assert payload == b"hello"
    assert can_identifier_is_valid(0x7FF)
    assert not can_identifier_is_valid(0x800)
    assert can_identifier_is_valid(0x1FFFFFFF, extended=True)


def test_circuit_models():
    assert voltage_divider(5.0, 10_000.0, 20_000.0) == pytest.approx(3.3333333)
    assert rc_cutoff_hz(10_000.0, 100e-9) == pytest.approx(159.1549, rel=1e-4)
    assert voltage_to_adc_code(1.65, 10, 3.3) == 512
    vpp, offset = function_generator_settings_for_gpio()
    assert vpp == pytest.approx(3.3)
    assert offset == pytest.approx(1.65)

    safe = gpio_signal_check(0.0, 3.3, 1_000.0)
    unsafe = gpio_signal_check(-0.1, 3.3, 1_000.0)
    assert safe.safe
    assert not unsafe.safe


def test_dry_gpio_and_pwm_are_deterministic():
    chip = DryGPIOChip()
    pin = chip.pin(17)
    pin.configure("output")
    observed = []
    pin.add_edge_callback(lambda value, stamp: observed.append((value, stamp)))

    pin.set_value(1)
    pin.set_value(0)
    assert [value for value, _stamp in observed] == [1, 0]

    counter = EdgeCounter(edge="rising")
    counter.observe(0, 0.0)
    counter.observe(1, 0.1)
    counter.observe(0, 0.2)
    counter.observe(1, 0.3)
    assert counter.count == 2
    assert counter.timestamps_sec == [0.1, 0.3]

    pwm = DryPWMChannel(bcm=18)
    pwm.set(100.0, 0.5)
    pwm.start()
    assert pwm.enabled
    assert pwm.frequency_hz == 100.0
    assert pwm.duty_cycle == 0.5
    pwm.stop()
    assert not pwm.enabled
    assert pwm.duty_cycle == 0.0


def test_non_finite_values_are_rejected():
    with pytest.raises(ValueError):
        SquareWave(10.0, math.nan)
