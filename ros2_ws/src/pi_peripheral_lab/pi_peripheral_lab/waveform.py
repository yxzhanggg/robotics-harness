"""Pure waveform and control mapping helpers for lab nodes."""

from dataclasses import dataclass
import math


def clamp(value: float, low: float, high: float) -> float:
    if low > high:
        raise ValueError("low limit must be <= high limit")
    if math.isnan(value) or math.isinf(value):
        raise ValueError("non-finite value is not allowed")
    return min(max(value, low), high)


def clamp_int(value: int, low: int, high: int) -> int:
    if low > high:
        raise ValueError("low limit must be <= high limit")
    return min(max(int(value), low), high)


@dataclass(frozen=True)
class SquareWave:
    frequency_hz: float
    duty_cycle: float = 0.5

    def __post_init__(self) -> None:
        if self.frequency_hz <= 0.0:
            raise ValueError("frequency_hz must be > 0")
        clamp(self.duty_cycle, 0.0, 1.0)

    @property
    def period_sec(self) -> float:
        return 1.0 / self.frequency_hz

    @property
    def high_time_sec(self) -> float:
        return self.period_sec * self.duty_cycle

    @property
    def low_time_sec(self) -> float:
        return self.period_sec - self.high_time_sec


@dataclass(frozen=True)
class PwmCommand:
    frequency_hz: float
    duty_cycle: float

    def sanitized(
        self,
        min_frequency_hz: float,
        max_frequency_hz: float,
    ) -> "PwmCommand":
        return PwmCommand(
            frequency_hz=clamp(self.frequency_hz, min_frequency_hz, max_frequency_hz),
            duty_cycle=clamp(self.duty_cycle, 0.0, 1.0),
        )


@dataclass(frozen=True)
class JoyControl:
    duty_axis: float = 0.0
    frequency_axis: float = 0.0
    trigger_axis: float = 0.0
    buttons: tuple[int, ...] = ()


def axis_to_unit(axis_value: float) -> float:
    """Map a joystick axis in [-1, 1] to [0, 1]."""

    return (clamp(axis_value, -1.0, 1.0) + 1.0) * 0.5


def axis_to_range(axis_value: float, low: float, high: float) -> float:
    return low + axis_to_unit(axis_value) * (high - low)


def pwm_from_joy(
    joy: JoyControl,
    min_frequency_hz: float = 10.0,
    max_frequency_hz: float = 1_000.0,
) -> PwmCommand:
    """Map PS5 stick axes to a safe PWM command."""

    return PwmCommand(
        duty_cycle=axis_to_unit(joy.duty_axis),
        frequency_hz=axis_to_range(joy.frequency_axis, min_frequency_hz, max_frequency_hz),
    )


def drive_strength_from_trigger(trigger_axis: float) -> float:
    """Map trigger axes to [0, 1], accepting both ROS joy conventions."""

    return axis_to_unit(trigger_axis)


def triangle_phase_value(phase: float, low: float = 0.0, high: float = 1.0) -> float:
    phase = phase % 1.0
    unit = 2.0 * phase if phase < 0.5 else 2.0 * (1.0 - phase)
    return low + unit * (high - low)


def sine_phase_value(phase: float, low: float = 0.0, high: float = 1.0) -> float:
    unit = 0.5 + 0.5 * math.sin(2.0 * math.pi * (phase % 1.0))
    return low + unit * (high - low)


def step_phase_value(phase: float, low: float = 0.0, high: float = 1.0) -> float:
    return high if (phase % 1.0) >= 0.5 else low


def pattern_bit(pattern: str, tick: int) -> int:
    """Return the digital output bit for a named low-speed teaching pattern."""

    if pattern == "square":
        return tick % 2
    if pattern == "pulse":
        return 1 if tick % 8 == 0 else 0
    if pattern == "heartbeat":
        return 1 if tick % 10 in {0, 2} else 0
    if pattern == "idle_low":
        return 0
    if pattern == "idle_high":
        return 1
    raise ValueError(f"unknown GPIO pattern: {pattern}")


def frequency_stats(edge_timestamps_sec: list[float]) -> dict[str, float]:
    """Estimate frequency and jitter from rising-edge timestamps."""

    if len(edge_timestamps_sec) < 2:
        return {"edge_count": float(len(edge_timestamps_sec)), "frequency_hz": 0.0, "jitter_sec": 0.0}

    periods = [
        b - a
        for a, b in zip(edge_timestamps_sec, edge_timestamps_sec[1:])
        if b > a
    ]
    if not periods:
        return {"edge_count": float(len(edge_timestamps_sec)), "frequency_hz": 0.0, "jitter_sec": 0.0}

    avg_period = sum(periods) / len(periods)
    jitter = max(periods) - min(periods)
    return {
        "edge_count": float(len(edge_timestamps_sec)),
        "frequency_hz": 1.0 / avg_period,
        "jitter_sec": jitter,
    }
