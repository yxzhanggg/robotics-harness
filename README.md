# ROS2 Multi-Robot Teleoperation Harness

This repository is the macOS-side authority for a ROS2 Jazzy multi-robot
development and deployment harness.

It includes the harness plus the initial production teleoperation path: a PS5
controller on `nexus` can select and command either `atlas` or `vector`, while
each robot runs a local `cmd_vel` watchdog that publishes safe velocity commands.

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

The tmux harness creates reserved panes. Runtime launch commands are run inside
target sessions after deployment and build.

## Multi-Machine Bringup

After `make check DEV=all` succeeds, runtime launch assets are available on the
Ubuntu targets:

```bash
ros2 launch robotics_bringup nexus.launch.py selected_robot:=atlas
ros2 launch robotics_bringup robot.launch.py robot_name:=atlas
ros2 launch robotics_bringup robot.launch.py robot_name:=vector
```

For coordinated tmux startup through SSH aliases from an Ubuntu target with this
workspace sourced:

```bash
ros2 run robotics_fleet_ops fleet_ops up all --collect-rosout
ros2 run robotics_fleet_ops fleet_ops status all
ros2 run robotics_fleet_ops fleet_ops down all
```

## Teleoperation

On `nexus`:

```bash
ros2 launch teleop_joy teleop_joy.launch.py selected_robot:=atlas
```

On each robot:

```bash
ros2 launch cmd_vel_watchdog cmd_vel_watchdog.launch.py robot_name:=atlas
ros2 launch cmd_vel_watchdog cmd_vel_watchdog.launch.py robot_name:=vector
```

The teleop node publishes operator intent to `/<robot>/cmd_vel`. Robot drivers
must consume only `/<robot>/cmd_vel_safe`, after the local watchdog enforces
timeout, e-stop, and velocity clamps.

## Configuration And Calibration

Layered runtime parameters live in `robotics_bringup`:

- `config/shared/`: defaults common to all machines.
- `config/per_device/nexus/`: ground-station overrides.
- `config/per_robot/atlas/` and `config/per_robot/vector/`: robot limits and
  calibration placeholders.

The bringup launch files load shared parameters first, then machine-specific
overrides.

## Logs, Services, And Security

Centralized ROS log capture is available on `nexus`:

```bash
ros2 launch robotics_bringup nexus.launch.py enable_rosout_collector:=true
ros2 run robotics_fleet_ops fleet_ops logs all --output-dir fleet_logs
```

User-level systemd service units can be rendered or explicitly installed:

```bash
ros2 run robotics_fleet_ops fleet_ops service render all
ros2 run robotics_fleet_ops fleet_ops service install all
ros2 run robotics_fleet_ops fleet_ops service start all
```

SROS2 support is opt-in:

```bash
ros2 run robotics_fleet_ops fleet_ops security check all
ros2 run robotics_fleet_ops fleet_ops security create all
ros2 run robotics_fleet_ops fleet_ops up all --security
```

The security mode uses `ROS_SECURITY_ENABLE=true`,
`ROS_SECURITY_STRATEGY=Enforce`, and
`/home/zyx/robotics_ws/security/keystore`.

## File Synchronization

Edit only on macOS under `ros2_ws/src/`. The remote path `/home/zyx/robotics_ws/src/` is a read-only mirror populated by `harness/deploy.sh` through rsync over SSH.

Never copy `build/`, `install/`, or `log/` between machines. `nexus` is x86_64, while `atlas` and `vector` are arm64.

## Device Groups

- `all`: `nexus`, `atlas`, `vector`
- `robots`: `atlas`, `vector`

Devices and groups are defined in `harness/inventory.yaml`.

## Safety Summary

Teleoperation requires a deadman button. Execution-side robot code includes a
local `cmd_vel` watchdog that stops the robot if commands stop arriving. DDS is
unauthenticated and unencrypted by default, so this system must stay on trusted
development networks unless SROS2 / DDS-Security is enabled and validated.
