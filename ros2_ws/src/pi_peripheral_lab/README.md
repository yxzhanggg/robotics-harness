# pi_peripheral_lab

`pi_peripheral_lab` is a standalone Raspberry Pi electrical and peripheral
engineering lab package. It is a teaching package, not a production robot
driver package. Future robot drivers should be created as separate packages.

All ROS topics are under `/pin_lab`. The package does not subscribe to
`/cmd_vel`, `/cmd_vel_safe`, or production robot control topics. PS5 input is
mapped only to `/pin_lab/joy_control` for lab experiments.

## Deployment

This package is deployed only to the target-specific package groups:

- `atlas`: main DUT for GPIO, PWM, buses, ADC/DAC, load driving, and sender labs.
- `vector`: peer node for handshake, UART, CAN, and RS485 receiver labs.

It is intentionally not in the `robots` package group.

## Safety Rules

- Low-voltage lab only. Do not connect mains voltage.
- Raspberry Pi GPIO is 3.3 V logic. Never feed 5 V or negative voltage into a GPIO.
- Put a 1 k ohm to 10 k ohm series protection resistor between a function
  generator and a GPIO input.
- For a 0 V to 3.3 V square wave into GPIO, start with Hi-Z output settings of
  3.3 Vpp and 1.65 V offset, then verify the actual waveform on the scope.
  A generator set for 50 ohm load can output a different voltage when connected
  to a high-impedance circuit.
- Oscilloscope ground clips and most function-generator grounds are earth
  referenced. Confirm the ground reference before clipping them to a circuit.
- Between two Raspberry Pis, connect only GND and signal wires. Do not connect
  5 V rails together.
- Never connect two push-pull GPIO outputs together.
- Use a flyback diode for inductive loads.
- With external load power, the Pi drives only a MOSFET gate or transistor base.
  It does not supply load current directly.

## Optional Hardware Dependencies

Automated tests and default launch files run in `dry_run=true` and require no
real hardware or optional hardware packages.

Install optional packages on the target only when running the matching HIL lab:

- `python3-libgpiod`: real GPIO input/output and software PWM.
- `python3-serial`: UART and RS485 serial ports.
- `python3-spidev`: SPI and MCP3008 access.
- `python3-smbus` or `python3-smbus2`: I2C, ADS1115-style probes, MCP4725 DAC.
- `python3-can`: SocketCAN or USB-CAN HIL.

The package does not enable `/dev/serial0`, `/dev/i2c-*`, `/dev/spidev*`, or CAN
interfaces automatically. System enablement and permissions must be handled
explicitly on the target during a lab session.

## Software Structure

- Pure logic modules: `pin_map.py`, `waveform.py`, `protocol_bits.py`,
  `circuit_models.py`.
- Dry-run adapters: `dry_gpio.py`.
- Hardware adapters: `hardware_adapters.py`, with lazy imports.
- ROS nodes: one node per lab surface.
- Config and launch: `config/*.yaml`, `launch/*.launch.py`.
- HIL guides: `docs/labs/*.md`.

## Default Pins

| Signal | BCM | Physical pin | Device |
| --- | ---: | ---: | --- |
| GND | n/a | 6 | all |
| Square/request | 17 | 11 | atlas |
| Ack input | 24 | 18 | atlas |
| PWM | 18 | 12 | atlas |
| UART TX | 14 | 8 | atlas |
| UART RX | 15 | 10 | atlas |
| I2C SDA | 2 | 3 | atlas |
| I2C SCL | 3 | 5 | atlas |
| SPI MOSI | 10 | 19 | atlas |
| SPI MISO | 9 | 21 | atlas |
| SPI SCLK | 11 | 23 | atlas |
| SPI CE0 | 8 | 24 | atlas |
| Request input | 27 | 13 | vector |
| Ack output | 22 | 15 | vector |

GPIO0/GPIO1 on physical pins 27/28 are reserved for HAT EEPROM ID and are not
used in the first stage.

## Dry Run Examples

```bash
ros2 launch pi_peripheral_lab atlas_gpio_output.launch.py
ros2 launch pi_peripheral_lab atlas_pwm_scope.launch.py
ros2 launch pi_peripheral_lab atlas_frequency_counter.launch.py
ros2 launch pi_peripheral_lab atlas_adc_reader.launch.py
```

## HIL Examples

Only use `dry_run:=false` after wiring the circuit and completing the safety
checklist in the matching lab document.

```bash
ros2 launch pi_peripheral_lab atlas_pwm_scope.launch.py dry_run:=false
ros2 launch pi_peripheral_lab atlas_uart_tx.launch.py dry_run:=false
ros2 launch pi_peripheral_lab atlas_can_sender.launch.py dry_run:=false
```

## Labs

1. [Pin map and electrical safety](docs/labs/01_pin_map_safety.md)
2. [GPIO output and input](docs/labs/02_gpio_output_input.md)
3. [Function generator GPIO input and frequency measurement](docs/labs/03_function_generator_input.md)
4. [PWM and RC low-pass filtering](docs/labs/04_pwm_rc_filter.md)
5. [ADC sampling](docs/labs/05_adc_sampling.md)
6. [DAC and analog output](docs/labs/06_dac_output.md)
7. [UART](docs/labs/07_uart.md)
8. [SPI](docs/labs/08_spi.md)
9. [I2C](docs/labs/09_i2c.md)
10. [CAN](docs/labs/10_can.md)
11. [RS485](docs/labs/11_rs485.md)
12. [Load driving](docs/labs/12_load_driver.md)
13. [PS5 lab controller](docs/labs/13_ps5_controller.md)

## Engineering Reuse Boundary

Reusable modules:

- `pin_map.py`
- `waveform.py`
- `protocol_bits.py`
- `circuit_models.py`
- hardware adapter patterns from `hardware_adapters.py`

Teaching-only assets:

- lab launch files
- lab YAML defaults
- HIL documents
- lab ROS nodes that publish explanatory JSON status

Production robot drivers should reuse only the appropriate logic or adapter
ideas, then provide separate launch files, parameters, safety review, and tests.
