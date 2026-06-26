#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/lib.sh
source "${SCRIPT_DIR}/lib.sh"

TALKER_DEVICE="${TALKER_DEVICE:-nexus}"
LISTENER_DEVICE="${LISTENER_DEVICE:-atlas}"
TIMEOUT_SECONDS="${DISCOVERY_TIMEOUT_SECONDS:-15}"
TOPIC_NAME="/harness_discovery"
MESSAGE_DATA="ping"
REMOTE_LOG="/tmp/${PROJECT_NAME}_dds_echo_${TALKER_DEVICE}_to_${LISTENER_DEVICE}.log"
REMOTE_PID="/tmp/${PROJECT_NAME}_dds_pub_${TALKER_DEVICE}_to_${LISTENER_DEVICE}.pid"
REMOTE_PUB_LOG="/tmp/${PROJECT_NAME}_dds_pub_${TALKER_DEVICE}_to_${LISTENER_DEVICE}.log"
PUB_PKILL_PATTERN="ros2 topic pub -r 2 /[h]arness_discovery"
ECHO_PKILL_PATTERN="ros2 topic echo /[h]arness_discovery"

if [[ "${TALKER_DEVICE}" == "${LISTENER_DEVICE}" ]]; then
  die "talker and listener devices must be different"
fi
is_device "${TALKER_DEVICE}" || die "unknown talker device: ${TALKER_DEVICE}"
is_device "${LISTENER_DEVICE}" || die "unknown listener device: ${LISTENER_DEVICE}"

TALKER_HOST="$(ssh_host_for "${TALKER_DEVICE}")"
LISTENER_HOST="$(ssh_host_for "${LISTENER_DEVICE}")"
TALKER_PREFIX="$(remote_ros_source_prefix "${TALKER_DEVICE}")"
LISTENER_PREFIX="$(remote_ros_source_prefix "${LISTENER_DEVICE}")"

info "DDS discovery test: talker=${TALKER_DEVICE}, listener=${LISTENER_DEVICE}, topic=${TOPIC_NAME}, domain=${ROS_DOMAIN_ID}, rmw=${RMW_IMPLEMENTATION}"

if ! device_online "${TALKER_DEVICE}"; then
  fail "${TALKER_DEVICE}: required talker host unavailable"
fi
if ! device_online "${LISTENER_DEVICE}"; then
  fail "${LISTENER_DEVICE}: required listener host unavailable"
fi
[[ "${FAIL_COUNT}" -eq 0 ]] || { summary; exit 1; }

cleanup() {
  ssh_bash "${TALKER_HOST}" "set -euo pipefail; if [ -f ${REMOTE_PID} ]; then kill \$(cat ${REMOTE_PID}) >/dev/null 2>&1 || true; rm -f ${REMOTE_PID}; fi; pkill -f '${PUB_PKILL_PATTERN}' >/dev/null 2>&1 || true" >/dev/null 2>&1 || true
  ssh_bash "${LISTENER_HOST}" "pkill -f '${ECHO_PKILL_PATTERN}' >/dev/null 2>&1 || true" >/dev/null 2>&1 || true
}
trap cleanup EXIT

cleanup

info "${TALKER_DEVICE}: starting ros2 topic pub in background"
ssh_bash "${TALKER_HOST}" "${TALKER_PREFIX} rm -f ${REMOTE_PID} ${REMOTE_PUB_LOG}; nohup ros2 topic pub -r 2 ${TOPIC_NAME} std_msgs/msg/String \"{data: '${MESSAGE_DATA}'}\" >${REMOTE_PUB_LOG} 2>&1 </dev/null & echo \$! > ${REMOTE_PID}"

sleep 2

info "${LISTENER_DEVICE}: running ros2 topic echo with ${TIMEOUT_SECONDS}s timeout"
ssh_bash "${LISTENER_HOST}" "${LISTENER_PREFIX} rm -f ${REMOTE_LOG}; timeout ${TIMEOUT_SECONDS}s ros2 topic echo ${TOPIC_NAME} std_msgs/msg/String >${REMOTE_LOG} 2>&1 || true"

LISTENER_OUTPUT="$(ssh_bash "${LISTENER_HOST}" "cat ${REMOTE_LOG} 2>/dev/null || true")"
printf '%s\n' "${LISTENER_OUTPUT}" | sed "s/^/${LISTENER_DEVICE}: /"

if grep -q "data: ${MESSAGE_DATA}" <<<"${LISTENER_OUTPUT}"; then
  pass "DDS discovery works: ${LISTENER_DEVICE} received ${TOPIC_NAME} from ${TALKER_DEVICE}"
else
  fail "DDS discovery failed: ${LISTENER_DEVICE} did not receive ${TOPIC_NAME} from ${TALKER_DEVICE} within ${TIMEOUT_SECONDS}s"
  warn "Likely cause: WiFi/AP multicast isolation blocks DDS discovery. Use FastDDS Discovery Server or static peer configuration."
  warn "Configure this in harness/env.sh for managed commands and, later, a shared FastDDS XML profile referenced from inventory-managed deployments."
fi

finish_with_summary
