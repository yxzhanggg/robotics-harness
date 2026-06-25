#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/lib.sh
source "${SCRIPT_DIR}/lib.sh"

TALKER_DEVICE="${TALKER_DEVICE:-nexus}"
LISTENER_DEVICE="${LISTENER_DEVICE:-atlas}"
TIMEOUT_SECONDS="${DISCOVERY_TIMEOUT_SECONDS:-20}"

if [[ "${TALKER_DEVICE}" == "${LISTENER_DEVICE}" ]]; then
  die "talker and listener devices must be different"
fi
is_device "${TALKER_DEVICE}" || die "unknown talker device: ${TALKER_DEVICE}"
is_device "${LISTENER_DEVICE}" || die "unknown listener device: ${LISTENER_DEVICE}"

TALKER_HOST="$(ssh_host_for "${TALKER_DEVICE}")"
LISTENER_HOST="$(ssh_host_for "${LISTENER_DEVICE}")"
TALKER_PREFIX="$(remote_ros_source_prefix "${TALKER_DEVICE}")"
LISTENER_PREFIX="$(remote_ros_source_prefix "${LISTENER_DEVICE}")"
REMOTE_LOG="/tmp/${PROJECT_NAME}_dds_listener_${TALKER_DEVICE}_to_${LISTENER_DEVICE}.log"

info "DDS discovery test: talker=${TALKER_DEVICE}, listener=${LISTENER_DEVICE}, domain=${ROS_DOMAIN_ID}, rmw=${RMW_IMPLEMENTATION}"

if ! device_online "${TALKER_DEVICE}"; then
  fail "${TALKER_DEVICE}: required talker host unavailable"
fi
if ! device_online "${LISTENER_DEVICE}"; then
  fail "${LISTENER_DEVICE}: required listener host unavailable"
fi
[[ "${FAIL_COUNT}" -eq 0 ]] || { summary; exit 1; }

cleanup() {
  ssh_bash "${TALKER_HOST}" "pkill -f 'ros2 run demo_nodes_cpp [t]alker' >/dev/null 2>&1 || true" >/dev/null 2>&1 || true
  ssh_bash "${LISTENER_HOST}" "pkill -f 'ros2 run demo_nodes_cpp [l]istener' >/dev/null 2>&1 || true" >/dev/null 2>&1 || true
}
trap cleanup EXIT

info "${TALKER_DEVICE}: starting demo_nodes_cpp talker in background"
ssh_bash "${TALKER_HOST}" "${TALKER_PREFIX} pkill -f 'ros2 run demo_nodes_cpp [t]alker' >/dev/null 2>&1 || true; nohup ros2 run demo_nodes_cpp talker >/tmp/${PROJECT_NAME}_dds_talker.log 2>&1 &"

info "${LISTENER_DEVICE}: listening for cross-machine DDS messages"
ssh_bash "${LISTENER_HOST}" "${LISTENER_PREFIX} rm -f ${REMOTE_LOG}; timeout ${TIMEOUT_SECONDS}s ros2 run demo_nodes_cpp listener >${REMOTE_LOG} 2>&1 || true"

LISTENER_OUTPUT="$(ssh_bash "${LISTENER_HOST}" "cat ${REMOTE_LOG} 2>/dev/null || true")"
printf '%s\n' "${LISTENER_OUTPUT}" | sed "s/^/${LISTENER_DEVICE}: /"

if grep -q 'I heard' <<<"${LISTENER_OUTPUT}"; then
  pass "DDS discovery works: ${LISTENER_DEVICE} received talker messages from ${TALKER_DEVICE}"
else
  fail "DDS discovery failed: ${LISTENER_DEVICE} did not receive demo talker messages from ${TALKER_DEVICE}"
  warn "Likely cause: WiFi/AP multicast isolation blocks DDS discovery. Use FastDDS Discovery Server or static peer configuration."
  warn "Configure this in harness/env.sh for managed commands and, later, a shared FastDDS XML profile referenced from inventory-managed deployments."
fi

finish_with_summary
