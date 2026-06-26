# cmd_vel_watchdog

`cmd_vel_watchdog` is deployed only to robot edge machines: `atlas` and `vector`.

It subscribes to `/cmd_vel`, republishes valid operator commands to `/cmd_vel_safe`, and publishes zero `geometry_msgs/msg/Twist` commands when fresh input stops arriving.

Execution-side drivers must subscribe to `/cmd_vel_safe`. They must never subscribe directly to `/cmd_vel`.

## Parameters

- `input_topic`: defaults to `/cmd_vel`.
- `output_topic`: defaults to `/cmd_vel_safe`.
- `timeout_sec`: defaults to `0.5`.
- `zero_publish_rate_hz`: defaults to `10.0`.

The watchdog runs on the execution side, so it continues to stop the robot if `nexus`, WiFi, Bluetooth, or the joystick fails.

## Run

```bash
ros2 run cmd_vel_watchdog cmd_vel_watchdog
```

## Test

```bash
colcon test --packages-select cmd_vel_watchdog
colcon test-result --all
```
