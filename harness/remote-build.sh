#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/lib.sh
source "${SCRIPT_DIR}/lib.sh"

TARGET="${1:-}"
[[ -n "${TARGET}" ]] || die "usage: harness/remote-build.sh <device|group>"

build_device() {
  local device="$1"
  local host
  local distro
  local remote_ws
  local remote_ws_expr
  local build_jobs
  local package_args
  local worker_args=""
  local makeflags=""

  host="$(ssh_host_for "${device}")"
  distro="$(device_ros_distro "${device}")"
  remote_ws="$(remote_ws_for "${device}")"
  remote_ws_expr="$(remote_path_expr "${remote_ws}")"
  build_jobs="$(device_build_jobs "${device}")"
  package_args="$(package_args_for_device "${device}" "--packages-up-to")"

  if [[ "${build_jobs}" =~ ^[0-9]+$ ]] && [[ "${build_jobs}" -gt 0 ]]; then
    worker_args="--parallel-workers ${build_jobs}"
    makeflags="export MAKEFLAGS=-j${build_jobs};"
  fi

  info "${device}: running rosdep install and colcon build"
  ssh_bash "${host}" "set -euo pipefail; source /opt/ros/${distro}/setup.bash; cd ${remote_ws_expr}; rosdep install --from-paths src --ignore-src -y; ${makeflags} colcon build --symlink-install ${worker_args} ${package_args}"
  pass "${device}: remote build complete"
}

for device in $(expand_targets "${TARGET}"); do
  build_device "${device}"
done

finish_with_summary
