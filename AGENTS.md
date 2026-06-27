# Agent Operating Context

This file is the single source of truth for future Codex sessions in this repository.

## Scope

This repository is a ROS2 multi-robot development and deployment harness. It currently contains only scaffolding, guardrails, tools, configuration layout, and documentation. Do not add robot business logic, algorithm nodes, teleoperation nodes, watchdog nodes, driver nodes, or example ROS2 packages unless a future task explicitly requests them.

## Environment Facts

The development authority is macOS. Codex runs on this macOS machine and edits the only authoritative project copy. macOS must not compile or run ROS2 for this project.

All ROS2 build, test, run, and tmux operations happen through SSH on Ubuntu targets.

Targets:

| Logical name | Hardware | Arch | Role |
| --- | --- | --- | --- |
| `nexus` | ThinkPad | x86_64 | Ground station and teleoperation station for joystick input, heavy algorithms, Nav2, SLAM, RViz, and simulation |
| `atlas` | Raspberry Pi | arm64 | Mobile robot edge node for sensors, actuators, and motors |
| `vector` | Raspberry Pi | arm64 | Mobile robot edge node for sensors, actuators, and motors |

SSH aliases are already configured. Use `ssh nexus`, `ssh atlas`, and `ssh vector`; do not add extra host parameters unless inventory later says so.

All targets run Ubuntu 24.04 with ROS2 Jazzy. The fixed target workspace is `/home/zyx/robotics_ws`, with source under `/home/zyx/robotics_ws/src`.

ROS installation variants are role-specific:

- `nexus` runs ROS2 desktop.
- `atlas` and `vector` run ROS2 ros-base.

Do not assume desktop-only packages exist on edge machines. In particular, do not assume `rviz2`, Gazebo, or `demo_nodes_*` are installed on `atlas` or `vector`. Use ros-base-compatible tools and packages where possible. If a future task truly requires a desktop-only package on an edge machine, explicitly install it there and record the dependency and rationale in inventory/docs.

All machines share `ROS_DOMAIN_ID=42` and default to `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`.

The PS5 DualSense controller is attached to `nexus` by USB or Bluetooth during experiments. Ubuntu 24.04 includes the `hid-playstation` driver; do not add third-party controller drivers without a specific future request.

Long-running ROS2 processes are hosted in local tmux sessions on target machines. SSH may disconnect while tmux sessions keep running.

## File Write Mechanism

Codex writes files only on macOS in this repository. ROS2 source lives under `ros2_ws/src/`.

Remote `/home/zyx/robotics_ws/src/` trees are read-only mirrors populated by `harness/deploy.sh` with rsync over SSH. Do not manually edit remote source. Git history exists only on macOS.

## Cross-Architecture Rule

`nexus` is x86_64. `atlas` and `vector` are arm64. Binaries are incompatible.

Never copy `install/`, `build/`, `log/`, or any generated binary artifacts between machines. Only synchronize source. Each machine runs `colcon build` locally.

## Selective Deployment Strategy

Different roles compile only what they need.

- Shared packages deploy to all devices.
- Edge driver packages deploy only to the `robots` group.
- Heavy algorithm, simulation, visualization, and teleoperation packages deploy only to `nexus`.

The deployment policy is defined in `harness/inventory.yaml` using `package_groups` and per-device `deploy_packages`.

At scaffold time, package groups are empty. When adding a package, place its name in exactly the right package group and run `make check DEV=<affected-device-or-group>`.

## macOS Metadata

macOS metadata must not pollute Ubuntu workspaces. Keep `.gitignore` and `harness/rsync-exclude.txt` aligned whenever either changes.

Current excluded patterns include `.DS_Store`, `._*`, `.Spotlight-V100/`, `.Trashes/`, `.fseventsd/`, `.DocumentRevisions-V100/`, `.TemporaryItems/`, `build/`, `install/`, `log/`, `__pycache__/`, and `*.pyc`.

Use `harness/clean-remote-meta.sh <device|group|all>` to remove historical remote `.DS_Store` and `._*` files because rsync excludes do not delete already existing excluded files.

## Raspberry Pi Build Limits

Raspberry Pi targets have limited memory. Do not allow default full-core `colcon` parallelism on `atlas` or `vector`.

`harness/inventory.yaml` sets:

- `nexus`: `build_jobs: 0`, meaning unrestricted/default parallelism.
- `atlas`: `build_jobs: 2`.
- `vector`: `build_jobs: 2`.

`harness/remote-build.sh` uses these values for `--parallel-workers` and `MAKEFLAGS`.

## Safety Rules For Future Robot Logic

1. Teleoperation must have a deadman or enable button. The robot may move only while the operator holds it. Releasing it must immediately command stop.
2. Execution-side Raspberry Pi code must include a `cmd_vel` watchdog. If fresh `cmd_vel` messages stop arriving within the configured timeout, the execution side must command zero velocity locally. This watchdog must not depend on `nexus`, because joystick, Bluetooth, WiFi, or ground station failures must not leave a robot moving.
3. DDS is unauthenticated and unencrypted by default. Any device on the same network can potentially inject or sniff topics. This is acceptable only for trusted development LANs. Production or untrusted networks require SROS2 / DDS-Security.

Execution-side drivers must subscribe to `/cmd_vel_safe`, never directly to `/cmd_vel`. `/cmd_vel` is operator intent and must pass through `cmd_vel_watchdog` on the robot before any actuator or motor driver consumes it.

## Harness Engineering Principles

- `AGENTS.md` is the context authority for future sessions.
- The harness operations baseline is locked. The lock protects only harness-related files listed in `harness/lock-manifest.sha256`; it does not protect robot project files under `ros2_ws/src/`, `docs/`, or `config/`.
- Do not modify locked harness files unless the user explicitly asks to unlock or evolve the harness.
- `harness/check.sh` verifies the harness lock before deploy, build, or test work begins.
- A change is not complete until `harness/check.sh <device|group>` passes for the affected device or group.
- All scripts must be idempotent and return non-zero on failure.
- Do not modify target system files outside `/home/zyx/robotics_ws` unless a future task explicitly requests it.
- Destructive operations such as `rm -rf` and rsync `--delete` require defensive checks.
- Keep versions fixed and avoid unnecessary dependencies.
- Refer to devices through `harness/inventory.yaml` logical names, not hardcoded hostnames in ad hoc scripts.
- Support device groups. `robots=[atlas,vector]`; `all=[nexus,atlas,vector]`.
- Keep `harness/rsync-exclude.txt` and `.gitignore` synchronized in intent.

## Standard Workflow

1. Edit on macOS.
2. Put ROS2 source under `ros2_ws/src/`.
3. Update `harness/inventory.yaml` package groups when package deployment scope changes.
4. Run `make check DEV=<device|group>`.
5. Treat the work as incomplete until `check.sh` passes.

Useful commands:

```bash
make doctor DEV=all
make discovery
make deploy DEV=<device|group>
make build DEV=<device|group>
make test DEV=<device|group>
make check DEV=<device|group>
make clean-meta DEV=all
make session-up DEV=<device>
make session-attach DEV=<device>
make session-down DEV=<device>
```

## Directory Conventions

- `harness/`: deployment, remote build/test, doctor, DDS discovery, and tmux orchestration scripts.
- `harness/inventory.yaml`: devices, groups, remote workspaces, build jobs, and package deployment strategy.
- `ros2_ws/src/`: authoritative local ROS2 source tree.
- `config/shared/`: future shared parameters.
- `config/per_robot/<device>/`: future robot-specific calibration and overrides.
- `docs/architecture.md`: topology and deployment architecture.
- `docs/conventions.md`: package, config, and workflow conventions.
- `docs/roadmap.md`: planned but intentionally unimplemented items.

## Adding A ROS2 Package

1. Create the package under `ros2_ws/src/`.
2. Decide the deployment group:
   - `shared` for interfaces and common utilities.
   - `robots` for edge packages needed by both Raspberry Pis.
   - `nexus` for heavy compute, visualization, simulation, and teleoperation.
   - `atlas` or `vector` only for packages specific to one robot.
3. Add the package name to `package_groups` in `harness/inventory.yaml`.
4. Declare OS dependencies in `package.xml` so `rosdep install --from-paths src --ignore-src -y` works.
5. Run `make check DEV=<affected-device-or-group>`.

Current deployment examples:

- `teleop_joy` is in the `nexus` package group because joystick input and teleoperation run on the ground station.
- `cmd_vel_watchdog` is in the `robots` package group because safety gating must run on `atlas` and `vector`.
- A shared `robot_interfaces` package has not been created yet; the current teleoperation path uses standard `geometry_msgs/msg/Twist`.

## ROS_DOMAIN_ID And DDS Discovery

All devices use `ROS_DOMAIN_ID=42`. Runtime ROS2 communication uses native DDS discovery on the LAN, not SSH tunnels.

Use `harness/discovery-test.sh` or `make discovery` to verify real cross-machine topic discovery with ros-base-compatible `ros2 topic pub/echo` and `std_msgs/msg/String`. Do not use `demo_nodes_*` for this harness check because edge machines run ros-base. If discovery fails while SSH works, suspect multicast isolation on the WiFi/AP. Future mitigation should use FastDDS Discovery Server or static peer configuration, wired through `harness/env.sh` and inventory-managed deployment conventions.

## Maintenance Discipline

Update `AGENTS.md` whenever environment facts, workflow rules, safety requirements, deployment strategy, or directory conventions change.

Update `docs/roadmap.md` instead of prematurely implementing planned robot functionality.

Keep `.gitignore` and `harness/rsync-exclude.txt` aligned when metadata or build-output exclusions change.

## Do Not Touch Without Explicit Request

- Do not install packages on target machines.
- Do not edit target files outside `/home/zyx/robotics_ws`.
- Do not add ROS2 robot nodes or example packages.
- Do not copy build artifacts across architectures.
- Do not replace tmux with systemd until requested.
- Do not expose this DDS network to untrusted networks.
- Do not commit or push unless the user explicitly requests Git operations.
