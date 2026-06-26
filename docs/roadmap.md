# Roadmap

## Implemented

- Teleoperation package using `joy` and `teleop_twist_joy`.
- Execution-side `cmd_vel` watchdog node publishing `/cmd_vel_safe`.

## Planned But Not Implemented

- Multi-machine launch orchestration.
- Machine-specific calibration and parameter files.
- Centralized log collection.
- systemd-based long-running service management.
- SROS2 / DDS-Security hardening for trusted production networks.

Do not implement these items unless a future task explicitly requests them.
