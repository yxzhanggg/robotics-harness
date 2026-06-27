# 07 UART

## Objective / Goal

Transmit UART from atlas TX to vector RX and observe 8N1 serial signaling on a
scope.

## Learning Points

UART 8N1, baud rate, start bit, stop bit, bit time, idle high line state,
permissions, and system serial enablement.

## BOM

atlas, vector, jumper wires, 1 k ohm series resistors, oscilloscope.

## Circuit Diagram

```text
atlas GPIO14 TX pin 8 -- 1 k ohm -- vector GPIO15 RX pin 10
atlas GND pin 6 ------------------- vector GND pin 6
optional vector TX pin 8 ---------- atlas RX pin 10
```

## Wiring Table

| From | To |
| --- | --- |
| atlas pin 8 TXD | vector pin 10 RXD |
| atlas pin 6 GND | vector pin 6 GND |

## Oscilloscope Setup

Probe atlas TX. Idle should be high. Measure bit time as approximately
`1 / baud_rate`.

## Function Generator Setup

Not used.

## Run Commands

On vector:

```bash
ros2 launch pi_peripheral_lab vector_uart_rx.launch.py dry_run:=false
ros2 topic echo /pin_lab/uart/rx
```

On atlas:

```bash
ros2 launch pi_peripheral_lab atlas_uart_tx.launch.py dry_run:=false
ros2 topic echo /pin_lab/uart/tx
```

## Expected Waveform

TX idles high, start bit goes low, eight data bits transmit LSB first, then a
stop bit high.

## Common Mistakes

- TX connected to TX instead of RX.
- Missing common ground.
- `/dev/serial0` not enabled or user lacks permissions.
- Using 5 V USB-TTL adapters on Pi GPIO.

## Safety Checklist

- Only 3.3 V UART levels touch Pi GPIO.
- Common ground is connected.
- Serial port enablement is reviewed manually; this package does not edit
  system configuration.

## HIL Pass/Fail Criteria

Pass: vector receives text and scope bit time matches baud rate.

Fail: no idle high, wrong bit time, or received framing is corrupt.

## Engineering Reuse

Teaching experiment: UART TX/RX nodes.

Reusable module: `protocol_bits.uart_8n1_frame` and serial adapter pattern.
