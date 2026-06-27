# Roadmap

## Implemented

- Teleoperation package using `joy` plus the project `multi_robot_teleop` node.
- Execution-side `cmd_vel` watchdog node publishing `/<robot>/cmd_vel_safe`.
- Runtime robot selection between `atlas` and `vector` from one PS5 controller.
- Namespaced operator intent and safe velocity topics.
- Teleoperation e-stop and execution-side timeout safety gates.
- Multi-machine launch orchestration through `robotics_bringup` launch files and
  the `robotics_fleet_ops fleet_ops up|down|status` tmux/SSH controller.
- Machine-specific calibration and parameter files in `robotics_bringup/config/`.
- Centralized log collection through the optional `rosout_collector` node and
  `fleet_ops logs`.
- systemd-based long-running service management through `fleet_ops service`.
- SROS2 / DDS-Security hardening profiles through `robotics_bringup` security
  launch arguments, policy templates, and `fleet_ops security`.

## Planned But Not Implemented

- Hardware motor, actuator, and sensor drivers.
- Production SROS2 certificate authority operations and key rotation.
- FastDDS Discovery Server or static peer discovery for multicast-hostile LANs.
