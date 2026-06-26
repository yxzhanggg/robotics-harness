# teleop_joy

`teleop_joy` is deployed only to `nexus`. It launches the standard ROS2 `joy_node` and `teleop_twist_joy_node` packages and publishes `geometry_msgs/msg/Twist` on `/cmd_vel`.

No custom teleoperation logic is implemented here.

## Safety Defaults

The DualSense mapping in `config/dualsense_teleop.yaml` is a calibration starting point:

- `enable_button: 4`, expected to be L1.
- `enable_turbo_button: 5`, expected to be R1.
- Linear x axis: `axis_linear.x: 1`.
- Angular yaw axis: `axis_angular.yaw: 3`.
- Normal limits: `0.25 m/s` linear, `0.8 rad/s` angular.
- Turbo limits: `0.45 m/s` linear, `1.2 rad/s` angular.

`require_enable_button` is true. Releasing the enable button must force output to zero even if the turbo button is still pressed.

## Axis And Button Calibration

Connect the DualSense to `nexus`, then inspect the raw joystick message:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run joy joy_node
ros2 topic echo /joy
```

Move one stick or press one button at a time and update `config/dualsense_teleop.yaml` if the observed axis or button indexes differ from the defaults.

## Run

```bash
ros2 launch teleop_joy teleop_joy.launch.py
```

Robot execution-side drivers must subscribe to `/cmd_vel_safe`, not `/cmd_vel`. `/cmd_vel` is an untrusted operator intent topic and must pass through the execution-side watchdog first.
