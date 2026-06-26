#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/lib.sh
source "${SCRIPT_DIR}/lib.sh"

TARGET="${1:-all}"

TARGETS="$(expand_targets "${TARGET}")"
for device in ${TARGETS}; do
  host="$(ssh_host_for "${device}")"
  remote_ws="$(remote_ws_for "${device}")"
  remote_ws_expr="$(remote_path_expr "${remote_ws}")"
  if ! device_online "${device}"; then
    continue
  fi
  info "${device}: deleting macOS metadata from remote source mirror"
  ssh_bash "${host}" "set -euo pipefail; if [ -d ${remote_ws_expr}/src ]; then find ${remote_ws_expr}/src \\( -name '.DS_Store' -o -name '._*' \\) -delete; fi"
  pass "${device}: metadata cleanup complete"
done

finish_with_summary
