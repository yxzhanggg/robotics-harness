# Architecture

This repository is the macOS-side authority for a ROS2 Jazzy multi-robot teleoperation harness. macOS is used for editing, Git history, and deployment orchestration only. ROS2 builds, tests, runtime nodes, and tmux sessions run on Ubuntu targets through SSH.

## Devices

| Logical name | Hardware | Architecture | Role |
| --- | --- | --- | --- |
| `nexus` | ThinkPad | x86_64 | Ground station, teleoperation station, heavy compute, RViz, simulation, Nav2, SLAM |
| `atlas` | Raspberry Pi | arm64 | Mobile robot edge node for sensors, actuators, and motors |
| `vector` | Raspberry Pi | arm64 | Mobile robot edge node for sensors, actuators, and motors |

All devices run Ubuntu 24.04 with ROS2 Jazzy. They share `ROS_DOMAIN_ID=42` and use `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` by default.

## Control And Execution Planes

SSH is the control plane. It is used for deployment, remote build, remote test, and starting or attaching tmux sessions.

DDS is the runtime data plane. ROS2 topics are discovered and exchanged directly on the LAN. The harness does not route robot control through SSH.

## Teleoperation Data Flow

Planned runtime flow:

1. A PS5 DualSense controller is connected to `nexus` by USB or Bluetooth.
2. A future teleoperation stack on `nexus` reads joystick input.
3. The future teleoperation stack publishes `/cmd_vel`.
4. `atlas` and `vector` subscribe to `/cmd_vel` over ROS2 DDS.
5. Future execution-side nodes apply motor commands locally.

The scaffold intentionally does not implement teleop, watchdog, driver, or algorithm nodes.

## Deployment Flow

1. Edit files only on macOS under `ros2_ws/src/`.
2. Run `harness/deploy.sh <device|group>` or `make deploy DEV=<device|group>`.
3. The script uses rsync over SSH to mirror source into `~/robotics_ws/src/` on targets.
4. Each target builds locally with `colcon build`; build and install directories never cross architectures.

Remote source trees are mirrors of the macOS authority. Do not edit them manually.

## Cross-Architecture Boundary

`nexus` is x86_64. `atlas` and `vector` are arm64. Build artifacts are not compatible. Only source is synchronized. `build/`, `install/`, and `log/` are excluded from Git and rsync.
