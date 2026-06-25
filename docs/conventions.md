# Conventions

## Package Naming

Use clear ROS2 package names that include the project or domain when helpful. Prefer names that expose role rather than hardware details unless the package is truly hardware-specific.

Suggested categories:

- Shared interfaces and utilities: deploy to all devices.
- Edge drivers and low-level adapters: deploy to `robots`.
- Heavy compute, simulation, visualization, and teleoperation: deploy to `nexus`.

## Python vs C++

Use Python for orchestration, light adapters, and tooling where startup latency and hard real-time behavior are not concerns.

Use C++ for high-rate drivers, control loops, performance-sensitive perception, or code that must minimize runtime jitter.

## Adding A ROS2 Package

1. Create the package under `ros2_ws/src/`.
2. Decide its deployment class: `shared`, `robots`, `nexus`, `atlas`, or `vector`.
3. Add the package name to the matching `package_groups` entry in `harness/inventory.yaml`.
4. Add any system dependencies to the package manifest so `rosdep install --from-paths src --ignore-src -y` can resolve them.
5. Run `make check DEV=<device|group>` for every affected target group.

## Configuration Layering

Load `config/shared/` defaults first. Load `config/per_robot/<device>/` overrides second. Do not put robot-specific calibration in shared config.

## Commits

Keep commits scoped. Do not mix harness changes, robot package logic, and target-machine operational changes in the same commit.

## Done Rule

An implementation is not complete until `harness/check.sh <device|group>` passes for the affected devices.
