from __future__ import annotations

from dataclasses import dataclass


REMOTE_WS = "/home/zyx/robotics_ws"
ROS_DISTRO = "jazzy"
ROS_DOMAIN_ID = "42"
RMW_IMPLEMENTATION = "rmw_fastrtps_cpp"
SESSION_PREFIX = "robotics_harness_runtime"
SERVICE_NAME = "robotics-harness-runtime.service"


@dataclass(frozen=True)
class Device:
    name: str
    ssh_host: str
    role: str

    @property
    def session_name(self) -> str:
        return f"{SESSION_PREFIX}_{self.name}"

    @property
    def launch_command(self) -> str:
        if self.role == "nexus":
            return "ros2 launch robotics_bringup nexus.launch.py"
        return f"ros2 launch robotics_bringup robot.launch.py robot_name:={self.name}"


DEVICES = {
    "nexus": Device("nexus", "nexus", "nexus"),
    "atlas": Device("atlas", "atlas", "robot"),
    "vector": Device("vector", "vector", "robot"),
}

GROUPS = {
    "all": ("nexus", "atlas", "vector"),
    "robots": ("atlas", "vector"),
}


def expand_target(target: str) -> tuple[Device, ...]:
    if target in DEVICES:
        return (DEVICES[target],)
    if target in GROUPS:
        return tuple(DEVICES[name] for name in GROUPS[target])
    raise ValueError(f"unknown device or group: {target}")
