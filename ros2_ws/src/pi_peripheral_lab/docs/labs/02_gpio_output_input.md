# 02 GPIO Output And Input

## Objective / Goal

Generate a square wave on atlas GPIO17 and observe it with a scope. Use vector
as a peer input for request/acknowledge timing.

## Learning Points

GPIO output, input, pull-up, pull-down, floating input, edge detection,
debouncing, and why two outputs must not be directly connected.

## BOM

atlas, vector, breadboard, jumper wires, 1 k ohm series resistors, 10 k ohm pull
resistors, oscilloscope.

## Circuit Diagram

```text
atlas GPIO17 pin 11 -- 1 k ohm -- vector GPIO27 pin 13
atlas GPIO24 pin 18 -- 1 k ohm -- vector GPIO22 pin 15
atlas GND pin 6  ---------------- vector GND pin 6
```

## Wiring Table

| From | To | Note |
| --- | --- | --- |
| atlas pin 11 GPIO17 | vector pin 13 GPIO27 | request |
| vector pin 15 GPIO22 | atlas pin 18 GPIO24 | ack |
| atlas pin 6 GND | vector pin 6 GND | common reference |

Do not connect atlas 5 V to vector 5 V.

## Oscilloscope Setup

Probe atlas GPIO17 for request. Optional second channel probes vector GPIO22
ack. Scope ground connects to common GND.

## Function Generator Setup

Not used in this lab.

## Run Commands

On vector:

```bash
ros2 launch pi_peripheral_lab vector_handshake_peer.launch.py dry_run:=false
```

On atlas:

```bash
ros2 launch pi_peripheral_lab atlas_handshake_main.launch.py dry_run:=false
ros2 topic echo /pin_lab/gpio_handshake/main
```

## Expected Waveform

Request toggles at the configured rate. Ack follows request after peer polling
latency. Edges remain between 0 V and 3.3 V.

## Common Mistakes

- Configuring both ends of one wire as outputs.
- Forgetting common ground.
- Leaving an input floating without a known pull state.

## Safety Checklist

- One side of each signal is output and the other is input.
- Series resistors are installed.
- Common GND is connected.
- No 5 V rail is connected between Pis.

## HIL Pass/Fail Criteria

Pass: `/pin_lab/gpio_handshake/main` reports matched request/ack states and the
scope shows 0 V to 3.3 V waveforms.

Fail: request and ack mismatch persistently, a line is stuck, or voltage exceeds
GPIO limits.

## Engineering Reuse

Teaching experiment: handshake nodes and launch files.

Reusable module: dry GPIO edge counting and pin safety validation.
