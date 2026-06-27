# 06 DAC And Analog Output

## Objective / Goal

Generate analog output with MCP4725 or PWM plus RC, controlled by a waveform or
PS5 lab command.

## Learning Points

DAC code, reference voltage, step response, settling time, triangle/sine
generation, and PWM ripple when using an RC filter.

## BOM

atlas, MCP4725 or equivalent DAC, oscilloscope, breadboard, optional RC filter.

## Circuit Diagram

```text
atlas SDA pin 3 ---- DAC SDA
atlas SCL pin 5 ---- DAC SCL
atlas GND pin 6 ---- DAC GND ---- scope ground
DAC OUT ------------ scope CH1
```

## Wiring Table

| Signal | atlas pin |
| --- | --- |
| SDA | pin 3 GPIO2 |
| SCL | pin 5 GPIO3 |
| GND | pin 6 |
| DAC OUT | scope CH1 |

## Oscilloscope Setup

Probe DAC OUT with DC coupling. Measure voltage range, settling time, and any
ripple/noise.

## Function Generator Setup

Not used.

## Run Commands

```bash
ros2 launch pi_peripheral_lab atlas_dac_output.launch.py dry_run:=false backend:=mcp4725
ros2 topic echo /pin_lab/dac
```

## Expected Waveform

Triangle, sine, or step-like output stays between 0 V and the configured
reference voltage.

## Common Mistakes

- Missing I2C pull-ups.
- Wrong I2C address.
- Expecting DAC output to drive a heavy load directly.

## Safety Checklist

- DAC VCC is compatible with Pi I2C levels.
- Grounds are common.
- Output load is high impedance unless buffered.

## HIL Pass/Fail Criteria

Pass: scope waveform matches `/pin_lab/dac` voltage and stays in range.

Fail: no I2C ACK, wrong voltage range, or output is overloaded.

## Engineering Reuse

Teaching experiment: DAC waveform launch.

Reusable module: DAC conversion helpers and MCP4725 adapter pattern.
