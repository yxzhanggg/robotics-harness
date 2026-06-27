# Harness Lock

This harness baseline is locked.

Future sessions must not modify protected harness files unless the user explicitly requests a harness unlock or harness evolution task.

Protected files are listed in `harness/lock-manifest.sha256`. `harness/check.sh` verifies those hashes before deploy, build, or test work begins.

Allowed without unlocking:

- Add new project packages outside the protected file list.
- Edit robot project source that is not part of the locked harness baseline.
- Add project documentation that does not change harness rules.

Requires explicit unlock:

- Any change under `harness/`.
- Changes to `AGENTS.md`, `Makefile`, `.gitignore`, core README/docs listed in the manifest.
- Changes to locked platform packages: `teleop_joy` and `cmd_vel_watchdog`.

This is an accidental-change guardrail, not a security boundary. A user can still deliberately unlock files and update the manifest.
