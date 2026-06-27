# 10 CAN

## Objective / Goal

Send CAN frames from atlas and receive them on vector using real CAN hardware.

## Learning Points

Dominant and recessive states, differential signaling, ACK, bitrate, bus-off,
error frames, and termination.

## BOM

atlas CAN HAT or USB-CAN, vector CAN HAT or USB-CAN, twisted pair, two 120 ohm
termination resistors, oscilloscope or differential probe.

## Circuit Diagram

```text
atlas CAN_H ---- twisted pair ---- vector CAN_H
atlas CAN_L ---- twisted pair ---- vector CAN_L
120 ohm across H/L at each bus end
atlas GND  ---- optional reference ---- vector GND
```

## Wiring Table

| Signal | Connection |
| --- | --- |
| CAN_H | atlas CAN_H to vector CAN_H |
| CAN_L | atlas CAN_L to vector CAN_L |
| termination | 120 ohm across CAN_H/CAN_L at both ends |

## Oscilloscope Setup

Use a differential probe if available. With two scope channels, probe CAN_H and
CAN_L relative to safe ground and use math subtraction if appropriate.

## Function Generator Setup

Not used.

## Run Commands

On vector:

```bash
ros2 launch pi_peripheral_lab vector_can_receiver.launch.py dry_run:=false
ros2 topic echo /pin_lab/can/rx
```

On atlas:

```bash
ros2 launch pi_peripheral_lab atlas_can_sender.launch.py dry_run:=false
ros2 topic echo /pin_lab/can/tx
```

## Expected Waveform

CAN_H and CAN_L move differentially during dominant bits. Receiver reports the
same arbitration ID and payload. This lab does not fake CAN with GPIO.

## Common Mistakes

- Missing termination.
- Bitrate mismatch.
- CAN_H/CAN_L swapped.
- CAN interface not configured up at OS level.

## Safety Checklist

- Real CAN transceivers are used.
- Bus has proper termination.
- Grounds/reference are safe for the transceivers.
- No GPIO is wired directly to CAN_H/CAN_L.

## HIL Pass/Fail Criteria

Pass: vector receives frames and scope shows differential CAN signaling.

Fail: bus-off, no ACK, no differential signal, or direct GPIO-to-CAN wiring.

## Engineering Reuse

Teaching experiment: CAN sender/receiver nodes.

Reusable module: CAN ID validation and hardware adapter boundary.
