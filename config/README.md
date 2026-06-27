# Configuration Layout

This directory is reserved for layered ROS2 configuration notes and future
harness-managed config.

- `shared/`: parameters and launch-time configuration that apply to every robot or station.
- `per_robot/atlas/`: atlas-specific calibration, limits, and overrides.
- `per_robot/vector/`: vector-specific calibration, limits, and overrides.

Layering convention for future packages:

1. Load shared defaults first.
2. Load the per-robot override for the target logical device second.
3. Keep machine-specific calibration out of shared files.

Deployable runtime parameters now live in the `robotics_bringup` package because
the current harness synchronizes only `ros2_ws/src/` to Ubuntu targets. Keep the
same layering semantics there:

- `robotics_bringup/config/shared/`
- `robotics_bringup/config/per_device/nexus/`
- `robotics_bringup/config/per_robot/atlas/`
- `robotics_bringup/config/per_robot/vector/`
