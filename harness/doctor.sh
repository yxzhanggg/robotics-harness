#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/lib.sh
source "${SCRIPT_DIR}/lib.sh"

TARGET="${1:-all}"
TIME_WARN_SECONDS="${TIME_WARN_SECONDS:-2}"

abs_diff() {
  local a="$1"
  local b="$2"
  local diff=$((a - b))
  if [[ "${diff}" -lt 0 ]]; then
    diff=$((-diff))
  fi
  printf '%s\n' "${diff}"
}

clock_probe() {
  local host="$1"
  local start
  local remote_time
  local end
  local rtt
  local drift
  local midpoint
  local offset

  start="$(date +%s)"
  remote_time="$(ssh_bash "${host}" "date +%s")"
  end="$(date +%s)"

  if [[ ! "${remote_time}" =~ ^[0-9]+$ ]]; then
    printf 'status=fail remote_time=%s\n' "${remote_time:-unset}"
    return 0
  fi

  if [[ "${remote_time}" -lt "${start}" ]]; then
    drift=$((start - remote_time))
  elif [[ "${remote_time}" -gt "${end}" ]]; then
    drift=$((remote_time - end))
  else
    drift=0
  fi

  rtt=$((end - start))
  midpoint=$(((start + end) / 2))
  offset=$((remote_time - midpoint))

  printf 'status=ok drift=%s offset=%s rtt=%s remote_time=%s local_start=%s local_end=%s\n' \
    "${drift}" "${offset}" "${rtt}" "${remote_time}" "${start}" "${end}"
}

check_device() {
  local device="$1"
  local host
  local distro
  local ros_variant
  local arch_expected
  local role
  local remote_ws
  local remote_ws_expr
  local ros_setup
  local clock_report
  local remote_report

  host="$(ssh_host_for "${device}")"
  distro="$(device_ros_distro "${device}")"
  ros_variant="$(device_ros_variant "${device}")"
  arch_expected="$(device_arch "${device}")"
  role="$(device_role "${device}")"
  remote_ws="$(remote_ws_for "${device}")"
  remote_ws_expr="$(remote_path_expr "${remote_ws}")"
  ros_setup="$(ros_env_setup_snippet "${device}")"

  info "${device}: checking ${host} (${role})"
  if ! device_online "${device}"; then
    return 0
  fi
  pass "${device}: SSH reachable"

  clock_report="$(clock_probe "${host}")"
  remote_report="$(ssh_bash "${host}" "set -euo pipefail
if [ -d /opt/ros/${distro} ]; then echo ROS_DIR=present; else echo ROS_DIR=missing; fi
if [ -f /opt/ros/${distro}/setup.bash ]; then ${ros_setup} fi
echo ROS_DISTRO=\${ROS_DISTRO:-unset}
echo RMW_IMPLEMENTATION=\${RMW_IMPLEMENTATION:-unset}
echo ROS_DOMAIN_ID=\${ROS_DOMAIN_ID:-unset}
echo ARCH=\$(uname -m)
echo ROS_VARIANT_EXPECTED=${ros_variant}
if command -v rviz2 >/dev/null 2>&1; then echo RVIZ2=present; else echo RVIZ2=missing; fi
if ros2 interface show std_msgs/msg/String >/dev/null 2>&1; then echo STD_MSGS_STRING=present; else echo STD_MSGS_STRING=missing; fi
if ros2 topic --help >/dev/null 2>&1; then echo ROS2_TOPIC_CLI=present; else echo ROS2_TOPIC_CLI=missing; fi
if command -v rosdep >/dev/null 2>&1; then echo ROSDEP_CMD=present; else echo ROSDEP_CMD=missing; fi
if [ -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then echo ROSDEP_INIT=present; else echo ROSDEP_INIT=missing; fi
if [ -d \"\$HOME/.ros/rosdep/sources.cache\" ]; then echo ROSDEP_CACHE=present; else echo ROSDEP_CACHE=missing; fi
echo GROUPS=\$(id -nG)
if compgen -G '/dev/input/js*' >/dev/null; then echo JOYSTICKS=present; else echo JOYSTICKS=missing; fi
if [ -d ${remote_ws_expr}/src ]; then
  META_COUNT=\$(find ${remote_ws_expr}/src \\( -name '.DS_Store' -o -name '._*' \\) -print -quit | wc -l | tr -d ' ')
else
  META_COUNT=src_missing
fi
echo META_COUNT=\${META_COUNT}
")"

  printf '%s\n' "${remote_report}" | sed "s/^/${device}: /"

  if grep -q '^ROS_DIR=present$' <<<"${remote_report}"; then
    pass "${device}: /opt/ros/${distro} exists"
  else
    fail "${device}: /opt/ros/${distro} missing"
  fi

  local ros_dist
  ros_dist="$(awk -F= '/^ROS_DISTRO=/{print $2}' <<<"${remote_report}")"
  if [[ "${ros_dist}" == "${distro}" ]]; then
    pass "${device}: ROS_DISTRO=${ros_dist}"
  else
    fail "${device}: expected ROS_DISTRO=${distro}, got ${ros_dist:-unset}"
  fi

  local remote_arch
  remote_arch="$(awk -F= '/^ARCH=/{print $2}' <<<"${remote_report}")"
  case "${arch_expected}:${remote_arch}" in
    x86_64:x86_64|arm64:aarch64|arm64:arm64)
      pass "${device}: architecture ${remote_arch} matches inventory ${arch_expected}"
      ;;
    *)
      fail "${device}: architecture ${remote_arch:-unknown} does not match inventory ${arch_expected}"
      ;;
  esac

  pass "${device}: inventory ros_variant=${ros_variant}"
  case "${ros_variant}" in
    desktop)
      if grep -q '^RVIZ2=present$' <<<"${remote_report}"; then
        pass "${device}: desktop marker rviz2 present"
      else
        warn "${device}: inventory expects desktop ROS install, but rviz2 was not found"
      fi
      ;;
    base)
      pass "${device}: ros-base target; desktop-only packages are not assumed"
      ;;
    *)
      warn "${device}: unknown ros_variant=${ros_variant:-unset} in inventory"
      ;;
  esac

  if grep -q '^STD_MSGS_STRING=present$' <<<"${remote_report}"; then
    pass "${device}: std_msgs/msg/String available"
  else
    fail "${device}: std_msgs/msg/String missing"
  fi
  if grep -q '^ROS2_TOPIC_CLI=present$' <<<"${remote_report}"; then
    pass "${device}: ros2 topic CLI available"
  else
    fail "${device}: ros2 topic CLI missing"
  fi

  local remote_domain
  remote_domain="$(awk -F= '/^ROS_DOMAIN_ID=/{print $2}' <<<"${remote_report}")"
  if [[ "${remote_domain}" == "${ROS_DOMAIN_ID}" ]]; then
    pass "${device}: ROS_DOMAIN_ID=${remote_domain}"
  else
    warn "${device}: remote shell ROS_DOMAIN_ID=${remote_domain:-unset}; harness will export ${ROS_DOMAIN_ID} for managed commands"
  fi

  local remote_rmw
  remote_rmw="$(awk -F= '/^RMW_IMPLEMENTATION=/{print $2}' <<<"${remote_report}")"
  if [[ "${remote_rmw}" == "${RMW_IMPLEMENTATION}" ]]; then
    pass "${device}: RMW_IMPLEMENTATION=${remote_rmw}"
  else
    warn "${device}: remote shell RMW_IMPLEMENTATION=${remote_rmw:-unset}; harness will export ${RMW_IMPLEMENTATION} for managed commands"
  fi

  local clock_status
  local drift
  local offset
  local rtt
  clock_status="$(awk '{for (i=1; i<=NF; i++) if ($i ~ /^status=/) {sub(/^status=/, "", $i); print $i}}' <<<"${clock_report}")"
  drift="$(awk '{for (i=1; i<=NF; i++) if ($i ~ /^drift=/) {sub(/^drift=/, "", $i); print $i}}' <<<"${clock_report}")"
  offset="$(awk '{for (i=1; i<=NF; i++) if ($i ~ /^offset=/) {sub(/^offset=/, "", $i); print $i}}' <<<"${clock_report}")"
  rtt="$(awk '{for (i=1; i<=NF; i++) if ($i ~ /^rtt=/) {sub(/^rtt=/, "", $i); print $i}}' <<<"${clock_report}")"
  if [[ "${clock_status}" != "ok" ]]; then
    warn "${device}: clock probe failed (${clock_report})"
  elif [[ "${drift}" -le "${TIME_WARN_SECONDS}" ]]; then
    pass "${device}: clock drift ${drift}s (offset≈${offset}s, ssh_rtt≈${rtt}s)"
  else
    warn "${device}: clock drift at least ${drift}s (offset≈${offset}s, ssh_rtt≈${rtt}s); install/enable chrony, especially on Raspberry Pi without hardware RTC"
  fi

  if grep -q '^ROSDEP_CMD=present$' <<<"${remote_report}"; then
    pass "${device}: rosdep command present"
  else
    fail "${device}: rosdep command missing"
  fi
  if grep -q '^ROSDEP_INIT=present$' <<<"${remote_report}"; then
    pass "${device}: rosdep initialized"
  else
    warn "${device}: rosdep init file missing"
  fi
  if grep -q '^ROSDEP_CACHE=present$' <<<"${remote_report}"; then
    pass "${device}: rosdep cache present"
  else
    warn "${device}: rosdep update cache missing"
  fi

  local groups_line
  groups_line="$(awk -F= '/^GROUPS=/{print $2}' <<<"${remote_report}")"
  if [[ "${device}" == "nexus" ]]; then
    if [[ " ${groups_line} " == *" input "* ]]; then
      pass "${device}: user is in input group"
    else
      warn "${device}: user is not in input group; reading DualSense joystick may fail"
    fi
    if grep -q '^JOYSTICKS=present$' <<<"${remote_report}"; then
      pass "${device}: /dev/input/js* present"
    else
      warn "${device}: no /dev/input/js* found; connect DualSense if testing teleop input"
    fi
  else
    if [[ " ${groups_line} " == *" dialout "* ]]; then
      pass "${device}: user is in dialout group"
    else
      warn "${device}: user is not in dialout group; serial/motor access may fail"
    fi
  fi

  local meta_count
  meta_count="$(awk -F= '/^META_COUNT=/{print $2}' <<<"${remote_report}")"
  case "${meta_count}" in
    0)
      pass "${device}: no macOS metadata found in remote src mirror"
      ;;
    src_missing)
      warn "${device}: ${remote_ws}/src does not exist yet"
      ;;
    *)
      warn "${device}: macOS metadata files exist in ${remote_ws}/src; run harness/clean-remote-meta.sh ${device}"
      ;;
  esac
}

TARGETS="$(expand_targets "${TARGET}")"
for device in ${TARGETS}; do
  check_device "${device}"
done

finish_with_summary
