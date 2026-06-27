# robotics_bringup

Role-specific launch and layered configuration for the robotics harness.

Launch files:

- `nexus.launch.py`: PS5 joystick input, multi-robot teleoperation, optional
  `/rosout` JSONL collection.
- `robot.launch.py`: local `cmd_vel_watchdog` for `atlas` or `vector`.

Parameter layers are loaded shared-first, machine-specific second. Robot drivers
must consume only `/<robot>/cmd_vel_safe`; this package does not define or start
motor drivers.
