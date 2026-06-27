from __future__ import annotations

import shlex

from robotics_fleet_ops.model import Device
from robotics_fleet_ops.model import REMOTE_WS
from robotics_fleet_ops.model import RMW_IMPLEMENTATION
from robotics_fleet_ops.model import ROS_DISTRO
from robotics_fleet_ops.model import ROS_DOMAIN_ID
from robotics_fleet_ops.model import SERVICE_NAME


def runtime_exports(security: bool = False) -> str:
    exports = [
        f"export ROS_DOMAIN_ID={shlex.quote(ROS_DOMAIN_ID)}",
        f"export RMW_IMPLEMENTATION={shlex.quote(RMW_IMPLEMENTATION)}",
    ]
    if security:
        exports.extend(
            [
                "export ROS_SECURITY_ENABLE=true",
                "export ROS_SECURITY_STRATEGY=Enforce",
                f"export ROS_SECURITY_KEYSTORE={shlex.quote(f'{REMOTE_WS}/security/keystore')}",
            ]
        )
    return "; ".join(exports)


def runtime_shell(device: Device, command: str, security: bool = False) -> str:
    return (
        "set -euo pipefail; "
        f"{runtime_exports(security)}; "
        "set +u; "
        f"source /opt/ros/{shlex.quote(ROS_DISTRO)}/setup.bash; "
        f"source {shlex.quote(REMOTE_WS)}/install/setup.bash; "
        "set -u; "
        f"cd {shlex.quote(REMOTE_WS)}; "
        f"{command}"
    )


def launch_command(device: Device, security: bool = False, collect_rosout: bool = False) -> str:
    command = device.launch_command
    if security:
        command += (
            " security_enable:=true"
            " security_strategy:=Enforce"
            f" security_keystore:={REMOTE_WS}/security/keystore"
        )
    if device.role == "nexus" and collect_rosout:
        command += " enable_rosout_collector:=true"
    return runtime_shell(device, f"exec {command}", security=security)


def tmux_up_command(device: Device, security: bool = False, collect_rosout: bool = False) -> str:
    launch = launch_command(device, security=security, collect_rosout=collect_rosout)
    return (
        "set -euo pipefail; "
        f"tmux has-session -t {shlex.quote(device.session_name)} 2>/dev/null && exit 0; "
        f"tmux new-session -d -s {shlex.quote(device.session_name)} -n runtime "
        f"{shlex.quote(f'bash -lc {shlex.quote(launch)}')}"
    )


def tmux_down_command(device: Device) -> str:
    return f"tmux kill-session -t {shlex.quote(device.session_name)} 2>/dev/null || true"


def tmux_status_command(device: Device) -> str:
    return (
        f"tmux has-session -t {shlex.quote(device.session_name)} 2>/dev/null "
        "&& echo running || echo stopped"
    )


def local_log_bundle_command(device: Device) -> str:
    capture_dir = f"{REMOTE_WS}/log/central/tmux"
    return f"""set -euo pipefail
mkdir -p {shlex.quote(capture_dir)}
if tmux has-session -t {shlex.quote(device.session_name)} 2>/dev/null; then
  tmux capture-pane -p -S -2000 -t {shlex.quote(device.session_name)}:0 > {shlex.quote(f"{capture_dir}/{device.name}.txt")} || true
fi
paths=()
[ -d {shlex.quote(f"{REMOTE_WS}/log")} ] && paths+=({shlex.quote(f"{REMOTE_WS}/log")})
[ -d "$HOME/.ros/log" ] && paths+=("$HOME/.ros/log")
if [ "${{#paths[@]}}" -eq 0 ]; then
  tar -czf - --files-from /dev/null
else
  tar -czf - "${{paths[@]}}" 2>/dev/null
fi
"""


def service_unit(device: Device, security: bool = False, collect_rosout: bool = False) -> str:
    launch = launch_command(device, security=security, collect_rosout=collect_rosout)
    return f"""[Unit]
Description=Robotics harness runtime for {device.name}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={REMOTE_WS}
ExecStart=/bin/bash -lc {shlex.quote(launch)}
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
"""


def service_install_command(unit_text: str) -> str:
    return (
        "set -euo pipefail; "
        "mkdir -p \"$HOME/.config/systemd/user\"; "
        f"cat > \"$HOME/.config/systemd/user/{SERVICE_NAME}\"; "
        "systemctl --user daemon-reload"
    ), unit_text


def service_action_command(action: str) -> str:
    if action == "status":
        return f"systemctl --user status {shlex.quote(SERVICE_NAME)} --no-pager"
    if action in {"start", "stop", "restart", "enable", "disable"}:
        return f"systemctl --user {action} {shlex.quote(SERVICE_NAME)}"
    raise ValueError(f"unsupported service action: {action}")


def security_check_command() -> str:
    return (
        "set -euo pipefail; "
        "command -v ros2 >/dev/null; "
        "ros2 security --help >/dev/null; "
        f"test -d {shlex.quote(f'{REMOTE_WS}/security/keystore')} "
        "&& echo keystore=present || echo keystore=missing"
    )


def security_create_command() -> str:
    keystore = f"{REMOTE_WS}/security/keystore"
    return (
        "set -euo pipefail; "
        f"mkdir -p {shlex.quote(f'{REMOTE_WS}/security')}; "
        f"if [ ! -d {shlex.quote(keystore)} ]; then ros2 security create_keystore {shlex.quote(keystore)}; fi; "
        f"ros2 security create_enclave {shlex.quote(keystore)} /joy_node || true; "
        f"ros2 security create_enclave {shlex.quote(keystore)} /multi_robot_teleop || true; "
        f"ros2 security create_enclave {shlex.quote(keystore)} /rosout_collector || true; "
        f"ros2 security create_enclave {shlex.quote(keystore)} /atlas/cmd_vel_watchdog || true; "
        f"ros2 security create_enclave {shlex.quote(keystore)} /vector/cmd_vel_watchdog || true"
    )
