#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/lib.sh
source "${SCRIPT_DIR}/lib.sh"

usage() {
  cat <<'EOF'
Usage: harness/deploy.sh [--dry-run] <device|group>

Synchronize local ros2_ws/src/ to the target /home/zyx/robotics_ws/src/.
EOF
}

DRY_RUN=0
TARGET=""
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      TARGET="$1"
      shift
      ;;
  esac
done

[[ -n "${TARGET}" ]] || { usage; exit 2; }
require_command rsync

[[ -d "${LOCAL_ROS_SRC}" ]] || die "local source path does not exist: ${LOCAL_ROS_SRC}"
if ! find "${LOCAL_ROS_SRC}" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
  die "local source path is empty; refusing rsync --delete to remote mirrors: ${LOCAL_ROS_SRC}"
fi

deploy_device() {
  local device="$1"
  local host
  local remote_ws
  local remote_ws_expr
  local remote_rsync_ws
  local packages=()
  local pkg
  local rsync_args=()

  host="$(ssh_host_for "${device}")"
  remote_ws="$(remote_ws_for "${device}")"
  remote_ws_expr="$(remote_path_expr "${remote_ws}")"
  remote_rsync_ws="$(remote_rsync_path "${host}" "${remote_ws}")"

  info "${device}: preparing remote source directory"
  ssh_bash "${host}" "set -euo pipefail; mkdir -p ${remote_ws_expr}/src"

  while IFS= read -r pkg; do
    [[ -z "${pkg}" ]] && continue
    packages+=("${pkg}")
  done < <(device_selected_packages "${device}")

  rsync_args=(-az --delete "--exclude-from=${RSYNC_EXCLUDE_FILE}")
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    rsync_args+=(--dry-run --itemize-changes)
  fi

  if [[ "${#packages[@]}" -eq 0 ]]; then
    info "${device}: deploy policy has no package filter yet; syncing full source tree"
    rsync "${rsync_args[@]}" "${LOCAL_ROS_SRC}/" "${host}:${remote_rsync_ws}/src/"
  else
    info "${device}: syncing selected packages: $(join_by_space "${packages[@]}")"
    local tmpdir
    tmpdir="$(mktemp -d)"
    trap 'rm -rf "${tmpdir}"' RETURN
    mkdir -p "${tmpdir}/src"
    for pkg in "${packages[@]}"; do
      [[ -e "${LOCAL_ROS_SRC}/${pkg}" ]] || die "${device}: selected package does not exist locally: ${pkg}"
      rsync -a "--exclude-from=${RSYNC_EXCLUDE_FILE}" "${LOCAL_ROS_SRC}/${pkg}" "${tmpdir}/src/"
    done
    rsync "${rsync_args[@]}" "${tmpdir}/src/" "${host}:${remote_rsync_ws}/src/"
  fi

  pass "${device}: deploy complete"
}

TARGETS="$(expand_targets "${TARGET}")"
for device in ${TARGETS}; do
  deploy_device "${device}"
done

finish_with_summary
