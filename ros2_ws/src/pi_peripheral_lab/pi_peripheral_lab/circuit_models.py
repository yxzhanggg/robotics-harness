"""Small circuit calculations used by the lab and its tests."""

from dataclasses import dataclass
import math

from pi_peripheral_lab.waveform import clamp


@dataclass(frozen=True)
class GpioSignalCheck:
    low_v: float
    high_v: float
    series_resistor_ohm: float
    safe: bool
    note: str


def voltage_divider(vin: float, r_top_ohm: float, r_bottom_ohm: float) -> float:
    if r_top_ohm <= 0.0 or r_bottom_ohm <= 0.0:
        raise ValueError("divider resistors must be positive")
    return vin * (r_bottom_ohm / (r_top_ohm + r_bottom_ohm))


def rc_time_constant_sec(resistance_ohm: float, capacitance_farad: float) -> float:
    if resistance_ohm <= 0.0 or capacitance_farad <= 0.0:
        raise ValueError("R and C must be positive")
    return resistance_ohm * capacitance_farad


def rc_cutoff_hz(resistance_ohm: float, capacitance_farad: float) -> float:
    return 1.0 / (2.0 * math.pi * rc_time_constant_sec(resistance_ohm, capacitance_farad))


def rc_lowpass_alpha(sample_period_sec: float, resistance_ohm: float, capacitance_farad: float) -> float:
    if sample_period_sec <= 0.0:
        raise ValueError("sample period must be positive")
    tau = rc_time_constant_sec(resistance_ohm, capacitance_farad)
    return sample_period_sec / (tau + sample_period_sec)


def pwm_average_voltage(v_high: float, duty_cycle: float) -> float:
    return v_high * clamp(duty_cycle, 0.0, 1.0)


def adc_code_to_voltage(code: int, bits: int, reference_voltage: float) -> float:
    if bits <= 0 or reference_voltage <= 0.0:
        raise ValueError("bits and reference voltage must be positive")
    max_code = (1 << bits) - 1
    if code < 0 or code > max_code:
        raise ValueError("ADC code out of range")
    return reference_voltage * code / max_code


def voltage_to_adc_code(voltage: float, bits: int, reference_voltage: float) -> int:
    if bits <= 0 or reference_voltage <= 0.0:
        raise ValueError("bits and reference voltage must be positive")
    max_code = (1 << bits) - 1
    normalized = clamp(voltage / reference_voltage, 0.0, 1.0)
    return int(round(normalized * max_code))


def dac_code_to_voltage(code: int, bits: int, reference_voltage: float) -> float:
    return adc_code_to_voltage(code, bits, reference_voltage)


def voltage_to_dac_code(voltage: float, bits: int, reference_voltage: float) -> int:
    return voltage_to_adc_code(voltage, bits, reference_voltage)


def gpio_signal_check(
    low_v: float,
    high_v: float,
    series_resistor_ohm: float,
) -> GpioSignalCheck:
    if low_v < 0.0:
        return GpioSignalCheck(low_v, high_v, series_resistor_ohm, False, "negative GPIO input")
    if high_v > 3.3:
        return GpioSignalCheck(low_v, high_v, series_resistor_ohm, False, "GPIO input above 3.3 V")
    if series_resistor_ohm < 1_000.0:
        return GpioSignalCheck(low_v, high_v, series_resistor_ohm, False, "series resistor too small")
    if series_resistor_ohm > 10_000.0:
        return GpioSignalCheck(low_v, high_v, series_resistor_ohm, False, "series resistor larger than lab range")
    return GpioSignalCheck(low_v, high_v, series_resistor_ohm, True, "safe for lab GPIO input")


def function_generator_settings_for_gpio(
    low_v: float = 0.0,
    high_v: float = 3.3,
) -> tuple[float, float]:
    """Return Vpp and offset for a Hi-Z 0..3.3 V GPIO square wave."""

    if high_v <= low_v:
        raise ValueError("high_v must be greater than low_v")
    if low_v < 0.0 or high_v > 3.3:
        raise ValueError("GPIO stimulus must remain inside 0..3.3 V")
    vpp = high_v - low_v
    offset = low_v + vpp / 2.0
    return vpp, offset
