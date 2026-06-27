# Architecture

This repository is the macOS-side authority for a ROS2 Jazzy multi-robot teleoperation harness. macOS is used for editing, Git history, and deployment orchestration only. ROS2 builds, tests, runtime nodes, and tmux sessions run on Ubuntu targets through SSH.

## Devices

| Logical name | Hardware | Architecture | Role |
| --- | --- | --- | --- |
| `nexus` | ThinkPad | x86_64 | Ground station, teleoperation station, heavy compute, RViz, simulation, Nav2, SLAM |
| `atlas` | Raspberry Pi | arm64 | Mobile robot edge node for sensors, actuators, and motors |
| `vector` | Raspberry Pi | arm64 | Mobile robot edge node for sensors, actuators, and motors |

All devices run Ubuntu 24.04 with ROS2 Jazzy. `nexus` uses the desktop ROS variant. `atlas` and `vector` use ros-base, so desktop-only packages such as RViz, Gazebo, and `demo_nodes_*` must not be assumed on edge machines. All devices share `ROS_DOMAIN_ID=42` and use `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` by default.

## Control And Execution Planes

SSH is the control plane. It is used for deployment, remote build, remote test, and starting or attaching tmux sessions.

DDS is the runtime data plane. ROS2 topics are discovered and exchanged directly on the LAN. The harness does not route robot control through SSH.

## Teleoperation Data Flow

Runtime flow:

1. A PS5 DualSense controller is connected to `nexus` by USB or Bluetooth.
2. `joy_node` on `nexus` publishes `/joy`.
3. `multi_robot_teleop` on `nexus` selects exactly one target robot at a time.
4. The selected target receives operator intent on `/<robot>/cmd_vel`.
5. Non-selected robots receive zero commands while teleop is active.
6. `cmd_vel_watchdog` runs locally on `atlas` and `vector`.
7. Each watchdog clamps incoming intent, enforces e-stop and timeout behavior,
   then publishes `/<robot>/cmd_vel_safe`.
8. Future execution-side drivers must consume only `/<robot>/cmd_vel_safe`.

`/<robot>/cmd_vel` is operator intent and is not a safe actuator input. The edge
watchdog is the safety gate that remains local to the robot if `nexus`, the
controller, WiFi, or DDS input fails.

## Deployment Flow

1. Edit files only on macOS under `ros2_ws/src/`.
2. Run `harness/deploy.sh <device|group>` or `make deploy DEV=<device|group>`.
3. The script uses rsync over SSH to mirror source into `/home/zyx/robotics_ws/src/` on targets.
4. Each target builds locally with `colcon build`; build and install directories never cross architectures.

Remote source trees are mirrors of the macOS authority. Do not edit them manually.

## Runtime Bringup

`robotics_bringup` provides role-specific launch files:

- `nexus.launch.py` starts `joy_node`, `multi_robot_teleop`, and optionally the
  `rosout_collector`.
- `robot.launch.py` starts the local `cmd_vel_watchdog` in the selected robot
  namespace.

`robotics_fleet_ops` provides SSH/tmux orchestration from an Ubuntu target with
the workspace sourced. It starts one tmux session per device and runs the
matching `robotics_bringup` launch file. This keeps ROS2 runtime processes on
Ubuntu targets while preserving the existing macOS-authoritative source model.

## Operations

Centralized logging has two layers:

- live `/rosout` collection on `nexus` to JSONL;
- on-demand remote log bundling of `/home/zyx/robotics_ws/log`, `~/.ros/log`,
  and captured tmux panes through `fleet_ops logs`.

Long-running service management is available through user-level systemd units
rendered by `fleet_ops service`. The tmux path remains available for experiments
and debugging.

SROS2 support is opt-in. Bringup launch files can export
`ROS_SECURITY_ENABLE=true`, `ROS_SECURITY_STRATEGY=Enforce`, and a workspace
keystore path. Policy templates live in `robotics_bringup/security/policies/`,
and keystore checks/creation are exposed through `fleet_ops security`.

## Cross-Architecture Boundary

`nexus` is x86_64. `atlas` and `vector` are arm64. Build artifacts are not compatible. Only source is synchronized. `build/`, `install/`, and `log/` are excluded from Git and rsync.
