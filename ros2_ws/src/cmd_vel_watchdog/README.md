# cmd_vel_watchdog

`cmd_vel_watchdog` is deployed only to robot edge machines: `atlas` and `vector`.

It runs inside the robot namespace, subscribes to `cmd_vel`, republishes clamped
operator commands to `cmd_vel_safe`, and publishes zero `geometry_msgs/msg/Twist`
commands when fresh input stops arriving.

With `robot_name:=atlas`, the effective topics are:

- Input: `/atlas/cmd_vel`
- Safe output: `/atlas/cmd_vel_safe`
- Operator e-stop input: `/atlas/teleop_estop`

Execution-side drivers must subscribe to `/<robot>/cmd_vel_safe`. They must never
subscribe directly to `/<robot>/cmd_vel`.

## Parameters

- `input_topic`: defaults to `cmd_vel`.
- `output_topic`: defaults to `cmd_vel_safe`.
- `estop_topic`: defaults to `teleop_estop`.
- `status_topic`: defaults to `~/status`.
- `timeout_sec`: defaults to `0.5`.
- `zero_publish_rate_hz`: defaults to `10.0`.
- `max_linear_x`: defaults to `0.6`.
- `max_angular_z`: defaults to `1.5`.
- `publish_zero_before_first_cmd`: defaults to `true`.

The watchdog runs on the execution side, so it continues to stop the robot if `nexus`, WiFi, Bluetooth, or the joystick fails.

## Run

```bash
ros2 launch cmd_vel_watchdog cmd_vel_watchdog.launch.py robot_name:=atlas
```

## Test

```bash
colcon test --packages-select cmd_vel_watchdog
colcon test-result --all
```
