"""Shared ROS helpers for pi_peripheral_lab nodes."""

import json
from typing import Any

from std_msgs.msg import String


def json_string(payload: dict[str, Any]) -> String:
    msg = String()
    msg.data = json.dumps(payload, sort_keys=True)
    return msg


def parse_json_string(msg: String) -> dict[str, Any]:
    data = json.loads(msg.data)
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def declare_and_get(node, name: str, default):
    node.declare_parameter(name, default)
    return node.get_parameter(name).value


def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise ValueError(f"cannot parse boolean parameter value: {value!r}")


def timer_period_from_hz(frequency_hz: float) -> float:
    if frequency_hz <= 0.0:
        raise ValueError("timer frequency must be positive")
    return 1.0 / frequency_hz


def create_lab_node_name(base_name: str) -> tuple[str, str]:
    return base_name, "/pin_lab"
