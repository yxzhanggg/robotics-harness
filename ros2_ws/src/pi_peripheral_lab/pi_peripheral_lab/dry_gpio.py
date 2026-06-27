"""Dry-run GPIO and PWM adapters for repeatable tests without hardware."""

from collections.abc import Callable
from dataclasses import dataclass
import time
from typing import Optional


EdgeCallback = Callable[[int, float], None]


@dataclass
class DryGPIOPin:
    bcm: int
    direction: str = "input"
    value: int = 0
    pull: str = "none"

    def __post_init__(self) -> None:
        self.value = 1 if self.value else 0
        self._callbacks: list[EdgeCallback] = []

    def configure(self, direction: str, pull: str = "none", initial: int = 0) -> None:
        if direction not in {"input", "output"}:
            raise ValueError("direction must be input or output")
        if pull not in {"none", "up", "down"}:
            raise ValueError("pull must be none, up, or down")
        self.direction = direction
        self.pull = pull
        self.value = 1 if initial else 0

    def set_value(self, value: int) -> None:
        if self.direction != "output":
            raise RuntimeError(f"GPIO{self.bcm} is not configured as output")
        self.inject_value(value)

    def inject_value(self, value: int) -> None:
        next_value = 1 if value else 0
        if next_value == self.value:
            return
        self.value = next_value
        timestamp = time.monotonic()
        for callback in list(self._callbacks):
            callback(self.value, timestamp)

    def read(self) -> int:
        return self.value

    def add_edge_callback(self, callback: EdgeCallback) -> None:
        self._callbacks.append(callback)


class DryGPIOChip:
    def __init__(self) -> None:
        self._pins: dict[int, DryGPIOPin] = {}

    def pin(self, bcm: int) -> DryGPIOPin:
        if bcm not in self._pins:
            self._pins[bcm] = DryGPIOPin(bcm=bcm)
        return self._pins[bcm]


@dataclass
class DryPWMChannel:
    bcm: int
    frequency_hz: float = 100.0
    duty_cycle: float = 0.0
    enabled: bool = False

    def start(self) -> None:
        self.enabled = True

    def stop(self) -> None:
        self.enabled = False
        self.duty_cycle = 0.0

    def set(self, frequency_hz: float, duty_cycle: float) -> None:
        if frequency_hz <= 0.0:
            raise ValueError("frequency_hz must be positive")
        if duty_cycle < 0.0 or duty_cycle > 1.0:
            raise ValueError("duty_cycle must be in [0, 1]")
        self.frequency_hz = frequency_hz
        self.duty_cycle = duty_cycle


class EdgeCounter:
    def __init__(self, edge: str = "rising") -> None:
        if edge not in {"rising", "falling", "both"}:
            raise ValueError("edge must be rising, falling, or both")
        self.edge = edge
        self.count = 0
        self.timestamps_sec: list[float] = []
        self._last_value: Optional[int] = None

    def observe(self, value: int, timestamp_sec: Optional[float] = None) -> None:
        current = 1 if value else 0
        timestamp = time.monotonic() if timestamp_sec is None else timestamp_sec
        if self._last_value is None:
            self._last_value = current
            return
        rising = self._last_value == 0 and current == 1
        falling = self._last_value == 1 and current == 0
        matched = (
            (self.edge == "rising" and rising)
            or (self.edge == "falling" and falling)
            or (self.edge == "both" and (rising or falling))
        )
        self._last_value = current
        if matched:
            self.count += 1
            self.timestamps_sec.append(timestamp)

    def reset(self) -> None:
        self.count = 0
        self.timestamps_sec.clear()
        self._last_value = None
