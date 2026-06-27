# 04 PWM And RC Low-Pass Filtering

## Objective / Goal

Output PWM on atlas GPIO18, control duty/frequency from `/pin_lab/joy_control`,
and build an RC low-pass filter to observe approximate analog voltage.

## Learning Points

PWM duty cycle, frequency, jitter, RC cutoff frequency, ripple, response time,
and software PWM limits under Linux.

## BOM

atlas, oscilloscope, resistor, capacitor, breadboard, optional PS5 controller.

## Circuit Diagram

```text
atlas GPIO18 pin 12 ---- R ----+---- scope CH2 filtered output
                               |
                               C
                               |
atlas GND pin 6 ---------------+---- scope ground

scope CH1 may also probe GPIO18 before R.
```

## Wiring Table

| Signal | Connection |
| --- | --- |
| PWM | atlas pin 12 GPIO18 to resistor |
| RC output | resistor/capacitor junction |
| capacitor ground | atlas pin 6 GND |

## Oscilloscope Setup

Use CH1 on raw PWM and CH2 on the RC output. Measure duty, frequency, ripple,
and settling time after a duty change.

## Function Generator Setup

Not used.

## Run Commands

```bash
ros2 launch pi_peripheral_lab atlas_pwm_scope.launch.py dry_run:=false
ros2 topic echo /pin_lab/pwm/status
```

Optional lab controller:

```bash
ros2 launch pi_peripheral_lab atlas_joy_control.launch.py
```

## Expected Waveform

Raw PWM switches between 0 V and 3.3 V. RC output approaches duty times 3.3 V,
with ripple that decreases when the RC cutoff is far below PWM frequency.

## Common Mistakes

- Choosing RC values that make ripple too high.
- Expecting software PWM to be jitter-free.
- Loading the RC output too heavily.

## Safety Checklist

- GPIO18 is not connected to a low-impedance load.
- Capacitor polarity is correct if electrolytic.
- Scope ground connects to Pi ground.

## HIL Pass/Fail Criteria

Pass: duty changes are visible on CH1 and filtered average changes on CH2.

Fail: PWM line exceeds 3.3 V, is shorted, or RC output does not respond.

## Engineering Reuse

Teaching experiment: PWM launch and scope procedure.

Reusable module: `waveform.PwmCommand` and `circuit_models.rc_cutoff_hz`.
