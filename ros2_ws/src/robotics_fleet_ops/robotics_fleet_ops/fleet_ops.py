from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

from robotics_fleet_ops.model import expand_target
from robotics_fleet_ops.rendering import local_log_bundle_command
from robotics_fleet_ops.rendering import security_check_command
from robotics_fleet_ops.rendering import security_create_command
from robotics_fleet_ops.rendering import service_action_command
from robotics_fleet_ops.rendering import service_install_command
from robotics_fleet_ops.rendering import service_unit
from robotics_fleet_ops.rendering import tmux_down_command
from robotics_fleet_ops.rendering import tmux_status_command
from robotics_fleet_ops.rendering import tmux_up_command
from robotics_fleet_ops.remote import run_ssh
from robotics_fleet_ops.remote import stream_ssh_to_file


def _add_target(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("target", nargs="?", default="all", help="Device or group.")


def _print_or_run(device, command: str, dry_run: bool, input_text: str | None = None) -> int:
    if dry_run:
        print(f"[{device.name}] ssh {device.ssh_host} -- {command}")
        if input_text is not None:
            print(input_text)
        return 0
    return run_ssh(device, command, input_text=input_text)


def command_up(args: argparse.Namespace) -> int:
    status = 0
    for device in expand_target(args.target):
        command = tmux_up_command(
            device,
            security=args.security,
            collect_rosout=args.collect_rosout,
        )
        status |= _print_or_run(device, command, args.dry_run)
    return status


def command_down(args: argparse.Namespace) -> int:
    status = 0
    for device in expand_target(args.target):
        status |= _print_or_run(device, tmux_down_command(device), args.dry_run)
    return status


def command_status(args: argparse.Namespace) -> int:
    status = 0
    for device in expand_target(args.target):
        status |= _print_or_run(device, tmux_status_command(device), args.dry_run)
    return status


def command_logs(args: argparse.Namespace) -> int:
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir) / stamp
    status = 0
    for device in expand_target(args.target):
        output_file = output_dir / f"{device.name}.tar.gz"
        command = local_log_bundle_command(device)
        if args.dry_run:
            print(f"[{device.name}] {output_file}: ssh {device.ssh_host} -- {command}")
            continue
        result = stream_ssh_to_file(device, command, output_file)
        if result == 0:
            print(f"{device.name}: wrote {output_file}")
        status |= result
    return status


def command_service(args: argparse.Namespace) -> int:
    status = 0
    for device in expand_target(args.target):
        if args.service_action == "render":
            print(service_unit(device, security=args.security, collect_rosout=args.collect_rosout))
            continue
        if args.service_action == "install":
            command, unit_text = service_install_command(
                service_unit(device, security=args.security, collect_rosout=args.collect_rosout)
            )
            status |= _print_or_run(device, command, args.dry_run, input_text=unit_text)
            continue
        command = service_action_command(args.service_action)
        status |= _print_or_run(device, command, args.dry_run)
    return status


def command_security(args: argparse.Namespace) -> int:
    status = 0
    for device in expand_target(args.target):
        command = security_check_command() if args.security_action == "check" else security_create_command()
        status |= _print_or_run(device, command, args.dry_run)
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fleet_ops",
        description="Manage robotics harness runtime operations through SSH aliases.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    up = subparsers.add_parser("up", help="Start per-device tmux runtime sessions.")
    _add_target(up)
    up.add_argument("--security", action="store_true", help="Enable SROS2 environment.")
    up.add_argument(
        "--collect-rosout",
        action="store_true",
        help="Enable the nexus rosout JSONL collector.",
    )
    up.add_argument("--dry-run", action="store_true")
    up.set_defaults(func=command_up)

    down = subparsers.add_parser("down", help="Stop per-device tmux runtime sessions.")
    _add_target(down)
    down.add_argument("--dry-run", action="store_true")
    down.set_defaults(func=command_down)

    status = subparsers.add_parser("status", help="Check tmux runtime session status.")
    _add_target(status)
    status.add_argument("--dry-run", action="store_true")
    status.set_defaults(func=command_status)

    logs = subparsers.add_parser("logs", help="Collect remote ROS and tmux logs.")
    _add_target(logs)
    logs.add_argument(
        "--output-dir",
        default="fleet_logs",
        help="Local directory for collected tarballs.",
    )
    logs.add_argument("--dry-run", action="store_true")
    logs.set_defaults(func=command_logs)

    service = subparsers.add_parser("service", help="Manage user-level systemd service units.")
    service.add_argument(
        "service_action",
        choices=("render", "install", "start", "stop", "restart", "status", "enable", "disable"),
    )
    _add_target(service)
    service.add_argument("--security", action="store_true", help="Enable SROS2 in the service.")
    service.add_argument(
        "--collect-rosout",
        action="store_true",
        help="Enable rosout collection in the nexus service.",
    )
    service.add_argument("--dry-run", action="store_true")
    service.set_defaults(func=command_service)

    security = subparsers.add_parser("security", help="Check or create SROS2 keystore material.")
    security.add_argument("security_action", choices=("check", "create"))
    _add_target(security)
    security.add_argument("--dry-run", action="store_true")
    security.set_defaults(func=command_security)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
