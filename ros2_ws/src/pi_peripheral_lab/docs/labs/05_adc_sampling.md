# 05 ADC Sampling

## Objective / Goal

Read analog voltage through MCP3008 or ADS1115-style hardware and publish
samples on `/pin_lab/adc`.

## Learning Points

Sampling rate, quantization, aliasing, Nyquist theorem, noise, reference
voltage, and scope correlation with digital samples.

## BOM

atlas, MCP3008 or ADS1115 module, function generator, oscilloscope, protection
resistors, optional voltage divider/clamp.

## Circuit Diagram

```text
function generator OUT -- protection/limit network -- ADC input
function generator GND ----------------------------- atlas GND
ADC digital bus ------------------------------------ atlas SPI or I2C pins
scope CH1 ------------------------------------------ ADC analog input
```

## Wiring Table

| Interface | atlas pins |
| --- | --- |
| MCP3008 SPI MOSI/MISO/SCLK/CE0 | pins 19/21/23/24 |
| I2C ADC SDA/SCL | pins 3/5 |
| GND | pin 6 |

## Oscilloscope Setup

Probe the ADC analog input after the protection network. Confirm it stays
inside the ADC and Pi module limits.

## Function Generator Setup

Use sine, triangle, or square. Start below 1 Hz to 10 Hz and keep the ADC input
inside its allowed range. Verify amplitude on the scope before sampling.

## Run Commands

Dry run:

```bash
ros2 launch pi_peripheral_lab atlas_adc_reader.launch.py
```

MCP3008 HIL:

```bash
ros2 launch pi_peripheral_lab atlas_adc_reader.launch.py dry_run:=false backend:=mcp3008
ros2 topic echo /pin_lab/adc
```

## Expected Waveform

Scope shows the analog input. `/pin_lab/adc` reports code and voltage. Aliasing
appears if signal frequency approaches or exceeds half the sample rate.

## Common Mistakes

- Feeding generator voltage directly beyond ADC range.
- Forgetting ADC reference voltage.
- Assuming sample rate is exact under ROS timers.

## Safety Checklist

- ADC input range is respected.
- Pi GPIO sees only digital 3.3 V bus levels.
- Generator ground and Pi ground are safely common.

## HIL Pass/Fail Criteria

Pass: reported voltage tracks a slow waveform and stays within reference range.

Fail: ADC saturates unexpectedly or bus reads fail after wiring is verified.

## Engineering Reuse

Teaching experiment: ADC reader node and HIL procedure.

Reusable module: ADC conversion helpers in `circuit_models.py`.
