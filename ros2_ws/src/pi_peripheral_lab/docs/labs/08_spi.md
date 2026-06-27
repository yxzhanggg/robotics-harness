# 08 SPI

## Objective / Goal

Run atlas as an SPI master and observe SCLK, MOSI, CE0, and optional MISO.

## Learning Points

CPOL, CPHA, chip select, MISO, MOSI, SCLK, endianness, bit order, and full-duplex
transfers.

## BOM

atlas, oscilloscope, MCP3008 or SPI EEPROM optional, jumper wires.

## Circuit Diagram

```text
atlas MOSI pin 19 ---- SPI device MOSI
atlas MISO pin 21 ---- SPI device MISO
atlas SCLK pin 23 ---- SPI device SCLK
atlas CE0  pin 24 ---- SPI device CS
atlas GND  pin 6  ---- SPI device GND ---- scope ground
```

## Wiring Table

| Signal | atlas pin |
| --- | --- |
| MOSI | 19 GPIO10 |
| MISO | 21 GPIO9 |
| SCLK | 23 GPIO11 |
| CE0 | 24 GPIO8 |
| GND | 6 |

## Oscilloscope Setup

Use CH1 on SCLK, CH2 on MOSI, optional CH3 on CE0. Trigger on CE0 falling edge
or SCLK.

## Function Generator Setup

Not used.

## Run Commands

```bash
ros2 launch pi_peripheral_lab atlas_spi_wave.launch.py dry_run:=false
ros2 topic echo /pin_lab/spi/transfer
```

## Expected Waveform

CE0 asserts, SCLK toggles at configured speed, MOSI shifts configured bytes.
MISO is meaningful only when a real SPI device is connected.

## Common Mistakes

- SPI not enabled at system level.
- Wrong CPOL/CPHA mode.
- MISO/MOSI swapped.
- Device powered at 5 V with 5 V logic.

## Safety Checklist

- SPI device logic is 3.3 V or level shifted.
- GND is common.
- CE0 is connected to the intended device.

## HIL Pass/Fail Criteria

Pass: scope shows expected clock and MOSI bits, and a connected device returns
plausible data.

Fail: no clock, wrong chip select, or bus voltage exceeds 3.3 V.

## Engineering Reuse

Teaching experiment: SPI waveform node.

Reusable module: `protocol_bits.spi_bits` and SPI adapter pattern.
