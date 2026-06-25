# 0001. Record Architecture Decisions

Date: 2026-06-25

## Status

Accepted

## Context

This project controls multiple ROS2 Jazzy machines from a macOS development authority. macOS cannot build or run ROS2. The target machines differ by CPU architecture, and Raspberry Pi targets have limited build resources.

## Decision

Use macOS as the only Git and editing authority. Synchronize source only to Ubuntu targets with rsync. Build and test on each target locally. Use tmux for long-running ROS2 sessions. Use inventory-driven device names, groups, build jobs, and package deployment policy.

## Consequences

Build artifacts never cross architecture boundaries. Remote workspaces are disposable mirrors of source. Every target can have a different package selection and build parallelism limit.
