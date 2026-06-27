# robotics_fleet_ops

Runtime operations tools for the robotics harness.

Commands:

```bash
ros2 run robotics_fleet_ops fleet_ops up all --collect-rosout
ros2 run robotics_fleet_ops fleet_ops status all
ros2 run robotics_fleet_ops fleet_ops logs all --output-dir fleet_logs
ros2 run robotics_fleet_ops fleet_ops service render all
ros2 run robotics_fleet_ops fleet_ops security check all
```

The tools use SSH aliases `nexus`, `atlas`, and `vector`. They do not install
packages or edit remote source trees. `service install` is the only command that
writes a user-level systemd unit, and it writes under `~/.config/systemd/user/`
on the selected Ubuntu target.
