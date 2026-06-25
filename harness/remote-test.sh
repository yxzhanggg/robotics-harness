#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/lib.sh
source "${SCRIPT_DIR}/lib.sh"

TARGET="${1:-}"
[[ -n "${TARGET}" ]] || die "usage: harness/remote-test.sh <device|group>"

test_device() {
  local device="$1"
  local host
  local distro
  local remote_ws
  local remote_ws_expr
  local package_args

  host="$(ssh_host_for "${device}")"
  distro="$(device_ros_distro "${device}")"
  remote_ws="$(remote_ws_for "${device}")"
  remote_ws_expr="$(remote_path_expr "${remote_ws}")"
  package_args="$(package_args_for_device "${device}" "--packages-select")"

  info "${device}: running colcon test"
  ssh_bash "${host}" "set -euo pipefail; source /opt/ros/${distro}/setup.bash; cd ${remote_ws_expr}; colcon test ${package_args}; colcon test-result --all"
  pass "${device}: remote tests complete"
}

for device in $(expand_targets "${TARGET}"); do
  test_device "${device}"
done

finish_with_summary
