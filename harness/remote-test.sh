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
  local ros_setup

  host="$(ssh_host_for "${device}")"
  remote_ws="$(remote_ws_for "${device}")"
  remote_ws_expr="$(remote_path_expr "${remote_ws}")"
  package_args="$(package_args_for_device "${device}" "--packages-select")"
  ros_setup="$(ros_env_setup_snippet "${device}")"

  info "${device}: running colcon test"
  ssh_bash "${host}" "set -euo pipefail; ${ros_setup} cd ${remote_ws_expr}; colcon test ${package_args}; colcon test-result --all"
  pass "${device}: remote tests complete"
}

TARGETS="$(expand_targets "${TARGET}")"
for device in ${TARGETS}; do
  test_device "${device}"
done

finish_with_summary
