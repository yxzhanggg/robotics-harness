# teleop_joy

`teleop_joy` is deployed only to `nexus`. It launches the standard ROS2 `joy_node`
plus the project `multi_robot_teleop` node.

`multi_robot_teleop` maps one PS5 DualSense controller to exactly one selected
robot at a time. It publishes operator intent commands on namespaced topics:

- `/atlas/cmd_vel`
- `/vector/cmd_vel`

It also publishes a latched operator e-stop state to:

- `/atlas/teleop_estop`
- `/vector/teleop_estop`

## Safety Defaults

The DualSense mapping in `config/dualsense_teleop.yaml` is a calibration starting point:

- `enable_button: 4`, expected to be L1.
- `turbo_button: 5`, expected to be R1.
- `estop_button: 2`, expected to be square.
- `clear_estop_button: 3`, expected to be triangle.
- `select_buttons.atlas: 0`, expected to be cross.
- `select_buttons.vector: 1`, expected to be circle.
- Linear x axis: `axis_linear.x: 1`.
- Angular yaw axis: `axis_angular.yaw: 3`.
- Normal limits: `0.25 m/s` linear, `0.8 rad/s` angular.
- Turbo limits: `0.45 m/s` linear, `1.2 rad/s` angular.

`require_enable_button` is true. Releasing the enable button must force output to zero even if the turbo button is still pressed.

Switching robots publishes zero to both the old and new selected robot before any
new non-zero command is emitted. Stale joystick input also forces zero commands
to every configured robot.

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
ros2 launch teleop_joy teleop_joy.launch.py selected_robot:=atlas
```

Runtime robot selection is normally done with the configured controller buttons.
It can also be changed through the ROS parameter API:

```bash
ros2 param set /multi_robot_teleop selected_robot vector
```

Robot execution-side drivers must subscribe to `/<robot>/cmd_vel_safe`, not
`/<robot>/cmd_vel`. The `cmd_vel` topic is untrusted operator intent and must
pass through the execution-side watchdog first.
