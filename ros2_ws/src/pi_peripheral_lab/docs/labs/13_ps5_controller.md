# 13 PS5 Lab Controller

## Objective / Goal

Use a PS5 DualSense controller as a lab command surface without connecting it
to the production robot execution chain.

## Learning Points

Joystick axes, trigger mapping, button-triggered lab actions, topic boundary,
and separation between learning tools and production control.

## BOM

nexus or atlas with ROS joy source available, PS5 DualSense controller, lab
nodes from previous experiments.

## Circuit Diagram

```text
PS5 controller -> ROS Joy message -> /pin_lab/joy -> joy_control_mapper_node -> /pin_lab/joy_control
```

No electrical GPIO circuit is required for this mapping node by itself.

## Wiring Table

Not applicable. This is a ROS lab-control topic mapping.

## Oscilloscope Setup

Use the scope on the lab output being controlled, such as PWM or DAC.

## Function Generator Setup

Not used.

## Run Commands

```bash
ros2 launch pi_peripheral_lab atlas_joy_control.launch.py
ros2 topic echo /pin_lab/joy_control
```

Then run a controlled lab node, for example:

```bash
ros2 launch pi_peripheral_lab atlas_pwm_scope.launch.py
```

## Expected Waveform

Left stick maps to PWM duty, right stick maps to PWM frequency, trigger maps to
DAC voltage and load-drive strength. Buttons select lab payloads.

## Common Mistakes

- Publishing to `/joy` instead of `/pin_lab/joy`.
- Reusing this lab mapper as production teleoperation.
- Expecting controller mapping to enforce robot motion safety.

## Safety Checklist

- The mapper publishes only `/pin_lab/joy_control`.
- No `/cmd_vel`, `/cmd_vel_safe`, or actuator production topic is used.
- The controlled hardware lab has its own safety checklist completed.

## HIL Pass/Fail Criteria

Pass: `/pin_lab/joy_control` changes with controller input and controlled lab
outputs respond within their safe ranges.

Fail: mapper publishes any production robot control topic or bypasses a lab
safety boundary.

## Engineering Reuse

Teaching experiment: PS5 mapper and lab JSON command format.

Reusable module: `waveform.pwm_from_joy` and axis scaling helpers.
