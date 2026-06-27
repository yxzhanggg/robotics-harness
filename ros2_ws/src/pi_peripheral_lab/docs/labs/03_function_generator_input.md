# 03 Function Generator GPIO Input

## Objective / Goal

Inject a safe 0 V to 3.3 V square wave into atlas GPIO17 and measure edge count,
frequency, duty-cycle behavior, and Linux timing jitter.

## Learning Points

Input threshold, edge counting, non-real-time Linux jitter, protection resistor,
Hi-Z versus 50 ohm generator settings, and why the oscilloscope is the timing
reference.

## BOM

atlas, function generator, oscilloscope, 1 k ohm to 10 k ohm resistor, jumper
wires.

## Circuit Diagram

```text
function generator OUT -- 1 k ohm to 10 k ohm -- atlas GPIO17 pin 11
function generator GND -------------------------- atlas GND pin 6
scope CH1 --------------------------------------- atlas GPIO17 pin 11
scope ground ------------------------------------ atlas GND pin 6
```

## Wiring Table

| Signal | Connection |
| --- | --- |
| generator signal | series resistor to atlas pin 11 GPIO17 |
| generator ground | atlas pin 6 GND |
| scope CH1 | atlas pin 11 GPIO17 |
| scope ground | atlas pin 6 GND |

## Oscilloscope Setup

Before connecting to GPIO, verify the generator output directly on the scope.
Use DC coupling. Confirm low is not below 0 V and high is not above 3.3 V.

## Function Generator Setup

Start with square wave, 10 Hz, Hi-Z, 3.3 Vpp, 1.65 V offset. If using 50 ohm
load mode, verify the actual voltage because a high-impedance GPIO input can
receive a different amplitude than the front panel implies.

## Run Commands

```bash
ros2 launch pi_peripheral_lab atlas_frequency_counter.launch.py dry_run:=false
ros2 topic echo /pin_lab/frequency
```

## Expected Waveform

Scope shows a 0 V to 3.3 V square wave. ROS-reported frequency should be close
at low rates, but it is not a precision measurement.

## Common Mistakes

- Negative offset causing negative GPIO voltage.
- 5 V amplitude entering the GPIO.
- No series resistor.
- Treating Linux GPIO edge timing as an oscilloscope.

## Safety Checklist

- Generator output verified before GPIO connection.
- Series resistor is present.
- GPIO voltage is 0 V to 3.3 V.
- Ground reference is understood.

## HIL Pass/Fail Criteria

Pass: scope confirms safe voltage and `/pin_lab/frequency` reports plausible
edge counts at 10 Hz to 100 Hz.

Fail: voltage exceeds limits or the reported count is unstable at very low
frequencies after wiring is checked.

## Engineering Reuse

Teaching experiment: frequency counter launch and HIL setup.

Reusable module: `waveform.frequency_stats` and `dry_gpio.EdgeCounter`.
