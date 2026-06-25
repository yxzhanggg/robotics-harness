# Configuration Layout

This directory is reserved for layered ROS2 configuration.

- `shared/`: parameters and launch-time configuration that apply to every robot or station.
- `per_robot/atlas/`: atlas-specific calibration, limits, and overrides.
- `per_robot/vector/`: vector-specific calibration, limits, and overrides.

Layering convention for future packages:

1. Load shared defaults first.
2. Load the per-robot override for the target logical device second.
3. Keep machine-specific calibration out of shared files.

No real robot parameters are stored in this scaffold.
