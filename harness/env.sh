#!/usr/bin/env bash
set -euo pipefail

export PROJECT_NAME="robotics_harness"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export HARNESS_DIR
export PROJECT_ROOT="$(cd "${HARNESS_DIR}/.." && pwd)"
export LOCAL_ROS_WS="${PROJECT_ROOT}/ros2_ws"
export LOCAL_ROS_SRC="${LOCAL_ROS_WS}/src"
export DEFAULT_REMOTE_WS="/home/zyx/robotics_ws"
export INVENTORY_FILE="${HARNESS_DIR}/inventory.yaml"
export RSYNC_EXCLUDE_FILE="${HARNESS_DIR}/rsync-exclude.txt"

export SSH_CONNECT_TIMEOUT="${SSH_CONNECT_TIMEOUT:-5}"
export SSH_BATCH_MODE="${SSH_BATCH_MODE:-yes}"
export SSH_OPTS="-o BatchMode=${SSH_BATCH_MODE} -o ConnectTimeout=${SSH_CONNECT_TIMEOUT} -o ServerAliveInterval=5 -o ServerAliveCountMax=1"

export TMUX_SESSION_PREFIX="${PROJECT_NAME}"
