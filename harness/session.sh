#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/lib.sh
source "${SCRIPT_DIR}/lib.sh"

DEVICE="${1:-}"
ACTION="${2:-up}"

[[ -n "${DEVICE}" ]] || die "usage: harness/session.sh <device> [up|attach|down]"
is_device "${DEVICE}" || die "session target must be a single device, not a group: ${DEVICE}"

HOST="$(ssh_host_for "${DEVICE}")"
REMOTE_WS="$(remote_ws_for "${DEVICE}")"
REMOTE_WS_EXPR="$(remote_path_expr "${REMOTE_WS}")"
SESSION_NAME="${TMUX_SESSION_PREFIX}_${DEVICE}"
ROS_PREFIX="$(remote_ros_source_prefix "${DEVICE}")"

tmux_send_pane() {
  local pane="$1"
  local command="$2"
  printf 'tmux send-keys -t %q:%s %q C-m; ' "${SESSION_NAME}" "${pane}" "${command}"
}

case "${ACTION}" in
  up)
    info "${DEVICE}: creating tmux session ${SESSION_NAME}"
    if [[ "${DEVICE}" == "nexus" ]]; then
      ssh_bash "${HOST}" "set -euo pipefail; tmux has-session -t ${SESSION_NAME} 2>/dev/null && exit 0; tmux new-session -d -s ${SESSION_NAME} -n ops; tmux split-window -h -t ${SESSION_NAME}:0; tmux select-layout -t ${SESSION_NAME}:0 even-horizontal; $(tmux_send_pane 0.0 "${ROS_PREFIX} cd ${REMOTE_WS_EXPR}; printf 'teleop placeholder only; no real node is started\n'; exec bash") $(tmux_send_pane 0.1 "${ROS_PREFIX} cd ${REMOTE_WS_EXPR}; printf 'topic monitor placeholder only; no real node is started\n'; exec bash")"
    else
      ssh_bash "${HOST}" "set -euo pipefail; tmux has-session -t ${SESSION_NAME} 2>/dev/null && exit 0; tmux new-session -d -s ${SESSION_NAME} -n ops; tmux split-window -h -t ${SESSION_NAME}:0; tmux select-layout -t ${SESSION_NAME}:0 even-horizontal; $(tmux_send_pane 0.0 "${ROS_PREFIX} cd ${REMOTE_WS_EXPR}; printf 'driver placeholder only; no real node is started\n'; exec bash") $(tmux_send_pane 0.1 "${ROS_PREFIX} cd ${REMOTE_WS_EXPR}; printf 'cmd_vel watchdog placeholder only; no real node is started\n'; exec bash")"
    fi
    pass "${DEVICE}: tmux session ready"
    ;;
  attach)
    info "${DEVICE}: attaching tmux session ${SESSION_NAME}"
    ssh_tty "${HOST}" "tmux attach -t ${SESSION_NAME}"
    ;;
  down)
    info "${DEVICE}: killing tmux session ${SESSION_NAME}"
    ssh_bash "${HOST}" "tmux kill-session -t ${SESSION_NAME} 2>/dev/null || true"
    pass "${DEVICE}: tmux session stopped"
    ;;
  *)
    die "unknown session action: ${ACTION}"
    ;;
esac

finish_with_summary
