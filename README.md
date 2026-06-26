# ROS2 Multi-Robot Teleoperation Harness

This repository is the macOS-side authority for a ROS2 Jazzy multi-robot development and deployment harness.

It is only a scaffold. It contains no robot business logic, algorithm nodes, teleoperation nodes, watchdog nodes, drivers, or example ROS2 packages.

## Quick Start

Run a target health check:

```bash
make doctor DEV=all
```

Verify real cross-machine ROS2 DDS discovery:

```bash
make discovery
```

The discovery check uses only ros-base-compatible `ros2 topic pub/echo` and `std_msgs/msg/String`.

Deploy source mirrors:

```bash
make deploy DEV=nexus
make deploy DEV=robots
make deploy DEV=all
```

Run the completion gate:

```bash
make check DEV=<device|group>
```

`check` runs local best-effort lint, deploys source, builds remotely, and runs remote tests. A change is not done until this passes for the affected target.

## tmux Sessions

Start a placeholder session on a single device:

```bash
make session-up DEV=nexus
make session-up DEV=atlas
```

Attach or stop it:

```bash
make session-attach DEV=nexus
make session-down DEV=nexus
```

The scaffold creates reserved panes only. It does not start real teleop, driver, watchdog, or algorithm nodes.

## File Synchronization

Edit only on macOS under `ros2_ws/src/`. The remote path `/home/zyx/robotics_ws/src/` is a read-only mirror populated by `harness/deploy.sh` through rsync over SSH.

Never copy `build/`, `install/`, or `log/` between machines. `nexus` is x86_64, while `atlas` and `vector` are arm64.

## Device Groups

- `all`: `nexus`, `atlas`, `vector`
- `robots`: `atlas`, `vector`

Devices and groups are defined in `harness/inventory.yaml`.

## Safety Summary

Future teleoperation must require a deadman button. Future execution-side robot code must include a local `cmd_vel` watchdog that stops the robot if commands stop arriving. DDS is unauthenticated and unencrypted by default, so this system must stay on trusted development networks unless SROS2 / DDS-Security is added.
