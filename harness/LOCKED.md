# Harness Lock

This harness operations baseline is locked.

Future sessions must not modify protected harness files unless the user explicitly requests a harness unlock or harness evolution task.

Protected files are listed in `harness/lock-manifest.sha256`. `harness/check.sh` verifies those hashes before deploy, build, or test work begins.

Allowed without unlocking:

- Add or edit robot project packages under `ros2_ws/src/`.
- Edit robot behavior, algorithms, drivers, tests, package README files, and project documentation.
- Add shared configuration under `config/` when it does not require changing harness deployment rules.

Requires explicit unlock:

- Any change under `harness/`.
- Changes to `AGENTS.md`, because it defines the future-session operating guardrails.
- Changes to `Makefile`, because it is the harness command entrypoint.

Not protected by this lock:

- `ros2_ws/src/**`
- `docs/**`
- `config/**`
- package source files, package tests, package launch files, and package README files.

This is an accidental-change guardrail, not a security boundary. A user can still deliberately unlock files and update the manifest.
