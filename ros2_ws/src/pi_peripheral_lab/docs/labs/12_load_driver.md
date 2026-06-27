# 12 Load Driver

## Objective / Goal

Use atlas GPIO18 PWM to drive a MOSFET or NPN low-side switch for a small
low-voltage load such as an LED strip, buzzer, fan, or small motor.

## Learning Points

Low-side switching, gate/base resistor, gate pulldown, flyback diode, external
supply, common ground, and why GPIO must not supply load current.

## BOM

atlas, logic-level MOSFET or NPN transistor, resistor, pulldown resistor,
flyback diode for inductive loads, external low-voltage supply, load,
oscilloscope.

## Circuit Diagram

```text
external +V ---- load ---- MOSFET drain/collector
MOSFET source/emitter ---- external GND ---- atlas GND pin 6
atlas GPIO18 pin 12 -- gate/base resistor -- MOSFET gate/base
gate/base -- pulldown resistor -- GND
flyback diode across inductive load, reverse biased during normal operation
```

## Wiring Table

| Signal | Connection |
| --- | --- |
| GPIO control | atlas pin 12 GPIO18 through gate/base resistor |
| pulldown | gate/base to GND |
| external supply GND | atlas GND pin 6 |
| load power | external supply, not Pi 5 V |

## Oscilloscope Setup

Probe gate/base drive and optionally load voltage. Keep ground references safe
when using an external supply.

## Function Generator Setup

Not used.

## Run Commands

```bash
ros2 launch pi_peripheral_lab atlas_load_driver.launch.py dry_run:=false
ros2 topic echo /pin_lab/load_driver/status
```

Optional PS5 control:

```bash
ros2 launch pi_peripheral_lab atlas_joy_control.launch.py
```

## Expected Waveform

Gate/base drive is a 0 V to 3.3 V PWM signal. Load voltage/current changes with
duty cycle. Inductive loads show controlled flyback through the diode.

## Common Mistakes

- Driving a motor directly from GPIO.
- Missing flyback diode on inductive load.
- No gate pulldown, causing startup glitches.
- External supply ground not common with Pi ground.

## Safety Checklist

- Load current path does not go through Pi GPIO.
- Flyback diode is installed for inductive loads.
- External supply voltage/current are appropriate.
- Gate/base resistor and pulldown are installed.

## HIL Pass/Fail Criteria

Pass: duty controls load strength and GPIO waveform remains 0 V to 3.3 V.

Fail: Pi overheats/resets, GPIO drives load directly, or inductive spikes are
uncontrolled.

## Engineering Reuse

Teaching experiment: load driver launch and safety checklist.

Reusable module: PWM command limiting and the adapter boundary.
