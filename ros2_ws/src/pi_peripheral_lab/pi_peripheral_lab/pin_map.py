"""Pin map and safety helpers for the Raspberry Pi peripheral lab.

The package uses BCM GPIO numbering in code. Physical pin numbers are recorded
here so experiment documents can give wiring tables without duplicating facts.
"""

from dataclasses import dataclass
from typing import Optional


MAX_GPIO_INPUT_VOLTAGE = 3.3
MIN_GPIO_INPUT_VOLTAGE = 0.0
PROTECTED_SERIES_RESISTOR_RANGE_OHM = (1_000.0, 10_000.0)
RESERVED_HAT_EEPROM_BCM = frozenset({0, 1})


@dataclass(frozen=True)
class PinSpec:
    """Electrical role for one Pi header signal."""

    logical_name: str
    device: str
    bcm: Optional[int]
    physical_pin: int
    default_direction: str
    default_role: str
    notes: str = ""


PIN_MAP = {
    "gnd_pin6": PinSpec("gnd_pin6", "all", None, 6, "power", "GND"),
    "atlas_square_request": PinSpec(
        "atlas_square_request",
        "atlas",
        17,
        11,
        "output",
        "GPIO square wave or handshake request",
    ),
    "atlas_ack_input": PinSpec(
        "atlas_ack_input",
        "atlas",
        24,
        18,
        "input",
        "Handshake acknowledge input",
    ),
    "atlas_pwm": PinSpec(
        "atlas_pwm",
        "atlas",
        18,
        12,
        "output",
        "PWM output for scope, RC filter, and load-drive gate control",
    ),
    "atlas_uart_tx": PinSpec("atlas_uart_tx", "atlas", 14, 8, "output", "UART TXD"),
    "atlas_uart_rx": PinSpec("atlas_uart_rx", "atlas", 15, 10, "input", "UART RXD"),
    "atlas_i2c_sda": PinSpec(
        "atlas_i2c_sda",
        "atlas",
        2,
        3,
        "open-drain",
        "I2C SDA, do not use for push-pull experiments",
    ),
    "atlas_i2c_scl": PinSpec(
        "atlas_i2c_scl",
        "atlas",
        3,
        5,
        "open-drain",
        "I2C SCL, do not use for push-pull experiments",
    ),
    "atlas_spi_mosi": PinSpec("atlas_spi_mosi", "atlas", 10, 19, "output", "SPI MOSI"),
    "atlas_spi_miso": PinSpec("atlas_spi_miso", "atlas", 9, 21, "input", "SPI MISO"),
    "atlas_spi_sclk": PinSpec("atlas_spi_sclk", "atlas", 11, 23, "output", "SPI SCLK"),
    "atlas_spi_ce0": PinSpec("atlas_spi_ce0", "atlas", 8, 24, "output", "SPI CE0"),
    "vector_request_input": PinSpec(
        "vector_request_input",
        "vector",
        27,
        13,
        "input",
        "Handshake request input from atlas",
    ),
    "vector_ack_output": PinSpec(
        "vector_ack_output",
        "vector",
        22,
        15,
        "output",
        "Handshake acknowledge output to atlas",
    ),
}


def get_pin(logical_name: str) -> PinSpec:
    """Return one named pin or raise a useful error."""

    try:
        return PIN_MAP[logical_name]
    except KeyError as exc:
        known = ", ".join(sorted(PIN_MAP))
        raise KeyError(f"unknown lab pin {logical_name!r}; known pins: {known}") from exc


def pins_for_device(device: str) -> list[PinSpec]:
    """Return pins used by one target plus shared power pins."""

    return [
        pin
        for pin in PIN_MAP.values()
        if pin.device == device or pin.device == "all"
    ]


def assert_gpio_is_lab_safe(bcm: int) -> None:
    """Reject pins that this lab reserves for Pi HAT EEPROM ID."""

    if bcm in RESERVED_HAT_EEPROM_BCM:
        raise ValueError("GPIO0/GPIO1 are reserved for HAT EEPROM ID in this lab")
    if bcm < 0 or bcm > 27:
        raise ValueError(f"BCM GPIO number out of Raspberry Pi 40-pin range: {bcm}")


def validate_gpio_input_voltage(voltage: float) -> float:
    """Return a valid GPIO input voltage or raise for unsafe levels."""

    if voltage < MIN_GPIO_INPUT_VOLTAGE or voltage > MAX_GPIO_INPUT_VOLTAGE:
        raise ValueError(
            "Raspberry Pi GPIO input must stay between "
            f"{MIN_GPIO_INPUT_VOLTAGE:.1f} V and {MAX_GPIO_INPUT_VOLTAGE:.1f} V"
        )
    return voltage


def validate_series_resistor(ohms: float) -> float:
    """Validate the function-generator-to-GPIO protection resistor range."""

    low, high = PROTECTED_SERIES_RESISTOR_RANGE_OHM
    if ohms < low or ohms > high:
        raise ValueError(
            "GPIO injection resistor should be between "
            f"{low:.0f} ohm and {high:.0f} ohm for this lab"
        )
    return ohms


def assert_no_push_pull_contention(
    first_direction: str,
    second_direction: str,
) -> None:
    """Reject a wire plan that connects two push-pull outputs together."""

    outputs = {"output", "push-pull-output"}
    if first_direction in outputs and second_direction in outputs:
        raise ValueError("never connect two GPIO push-pull outputs together")
