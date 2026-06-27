from __future__ import annotations

from pathlib import Path
import subprocess

from robotics_fleet_ops.model import Device


def run_ssh(device: Device, command: str, *, input_text: str | None = None) -> int:
    completed = subprocess.run(
        ["ssh", device.ssh_host, "bash", "-lc", command],
        input=input_text,
        text=True,
        check=False,
    )
    return completed.returncode


def stream_ssh_to_file(device: Device, command: str, output_file: Path) -> int:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("wb") as handle:
        completed = subprocess.run(
            ["ssh", device.ssh_host, "bash", "-lc", command],
            stdout=handle,
            check=False,
        )
    return completed.returncode
