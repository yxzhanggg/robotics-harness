#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/lib.sh
source "${SCRIPT_DIR}/lib.sh"

TARGET="${1:-all}"
TIME_WARN_SECONDS="${TIME_WARN_SECONDS:-2}"

controller_epoch() {
  date +%s
}

abs_diff() {
  local a="$1"
  local b="$2"
  local diff=$((a - b))
  if [[ "${diff}" -lt 0 ]]; then
    diff=$((-diff))
  fi
  printf '%s\n' "${diff}"
}

check_device() {
  local device="$1"
  local host
  local distro
  local arch_expected
  local role
  local remote_ws
  local remote_ws_expr
  local ctl_time
  local remote_report

  host="$(ssh_host_for "${device}")"
  distro="$(device_ros_distro "${device}")"
  arch_expected="$(device_arch "${device}")"
  role="$(device_role "${device}")"
  remote_ws="$(remote_ws_for "${device}")"
  remote_ws_expr="$(remote_path_expr "${remote_ws}")"

  info "${device}: checking ${host} (${role})"
  if ! device_online "${device}"; then
    return 0
  fi
  pass "${device}: SSH reachable"

  ctl_time="$(controller_epoch)"
  remote_report="$(ssh_bash "${host}" "set -euo pipefail
if [ -d /opt/ros/${distro} ]; then echo ROS_DIR=present; else echo ROS_DIR=missing; fi
if [ -f /opt/ros/${distro}/setup.bash ]; then source /opt/ros/${distro}/setup.bash; fi
echo ROS_DISTRO=\${ROS_DISTRO:-unset}
echo RMW_IMPLEMENTATION=\${RMW_IMPLEMENTATION:-unset}
echo ROS_DOMAIN_ID=\${ROS_DOMAIN_ID:-unset}
echo ARCH=\$(uname -m)
echo EPOCH=\$(date +%s)
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

  grep -q '^ROS_DIR=present$' <<<"${remote_report}" \
    && pass "${device}: /opt/ros/${distro} exists" \
    || fail "${device}: /opt/ros/${distro} missing"

  local ros_dist
  ros_dist="$(awk -F= '/^ROS_DISTRO=/{print $2}' <<<"${remote_report}")"
  [[ "${ros_dist}" == "${distro}" ]] \
    && pass "${device}: ROS_DISTRO=${ros_dist}" \
    || fail "${device}: expected ROS_DISTRO=${distro}, got ${ros_dist:-unset}"

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

  local remote_time
  remote_time="$(awk -F= '/^EPOCH=/{print $2}' <<<"${remote_report}")"
  local drift
  drift="$(abs_diff "${ctl_time}" "${remote_time:-0}")"
  if [[ "${drift}" -le "${TIME_WARN_SECONDS}" ]]; then
    pass "${device}: clock drift ${drift}s"
  else
    warn "${device}: clock drift ${drift}s; install/enable chrony, especially on Raspberry Pi without hardware RTC"
  fi

  grep -q '^ROSDEP_CMD=present$' <<<"${remote_report}" \
    && pass "${device}: rosdep command present" \
    || fail "${device}: rosdep command missing"
  grep -q '^ROSDEP_INIT=present$' <<<"${remote_report}" \
    && pass "${device}: rosdep initialized" \
    || warn "${device}: rosdep init file missing"
  grep -q '^ROSDEP_CACHE=present$' <<<"${remote_report}" \
    && pass "${device}: rosdep cache present" \
    || warn "${device}: rosdep update cache missing"

  local groups_line
  groups_line="$(awk -F= '/^GROUPS=/{print $2}' <<<"${remote_report}")"
  if [[ "${device}" == "nexus" ]]; then
    if [[ " ${groups_line} " == *" input "* ]]; then
      pass "${device}: user is in input group"
    else
      warn "${device}: user is not in input group; reading DualSense joystick may fail"
    fi
    grep -q '^JOYSTICKS=present$' <<<"${remote_report}" \
      && pass "${device}: /dev/input/js* present" \
      || warn "${device}: no /dev/input/js* found; connect DualSense if testing teleop input"
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

for device in $(expand_targets "${TARGET}"); do
  check_device "${device}"
done

finish_with_summary
