# 01 Pin Map And Electrical Safety

## Objective / Goal

Learn the Raspberry Pi 40-pin header, BCM numbering, physical pin numbering,
power pins, ground pins, and the electrical limits used by this lab.

## Learning Points

- BCM GPIO numbers are not physical pin numbers.
- GPIO is 3.3 V logic only.
- Common ground is required for signal references.
- Oscilloscope and function-generator grounds may be earth referenced.
- Series resistors, dividers, clamps, and pull resistors reduce risk.

## BOM

Raspberry Pi atlas, vector, breadboard, jumper wires, 1 k ohm to 10 k ohm
resistors, 10 k ohm pull resistors, oscilloscope, function generator.

## Circuit Diagram

```text
Pi physical pin 6 GND ---- breadboard ground rail
Pi GPIO signal pin ---- optional 1 k ohm to 10 k ohm ---- lab signal
```

## Wiring Table

| Signal | BCM | Physical pin | Direction |
| --- | ---: | ---: | --- |
| GND | n/a | 6 | reference |
| atlas square/request | 17 | 11 | output |
| atlas ack input | 24 | 18 | input |
| atlas PWM | 18 | 12 | output |

## Oscilloscope Setup

Connect probe ground to the same breadboard ground rail as Pi pin 6. Probe only
one signal first. Use 1x or 10x consistently and confirm the scope setting.

## Function Generator Setup

Do not connect the generator until its output is verified on the scope. For a
GPIO square input, use Hi-Z 3.3 Vpp, 1.65 V offset, then verify 0 V to 3.3 V.
If the generator is configured for a 50 ohm load, the displayed and actual
voltage may differ on a high-impedance GPIO input.

## Run Commands

```bash
ros2 launch pi_peripheral_lab atlas_gpio_output.launch.py
ros2 topic echo /pin_lab/gpio_output/status
```

Use `dry_run:=false` only after wiring and checks.

## Expected Waveform

GPIO high is about 3.3 V and GPIO low is about 0 V. Edges are not ideal; rise
and fall time depend on wiring, capacitance, and load.

## Common Mistakes

- Confusing BCM 17 with physical pin 17.
- Connecting a 5 V module output directly to GPIO.
- Clipping scope ground to a non-ground node.
- Connecting two Pi 5 V pins together.

## Safety Checklist

- GPIO input is between 0 V and 3.3 V.
- Grounds are intentionally common.
- No two push-pull outputs are tied together.
- Scope and function-generator grounds are understood before connection.

## HIL Pass/Fail Criteria

Pass: pin identification is correct, scope ground is safe, and GPIO high/low
levels stay within 0 V to 3.3 V.

Fail: any signal exceeds 3.3 V, goes negative, or shorts a supply/ground path.

## Engineering Reuse

Teaching experiment: this document and launch file.

Reusable module: `pi_peripheral_lab.pin_map` safety checks and pin facts.
