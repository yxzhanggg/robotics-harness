#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/env.sh
source "${SCRIPT_DIR}/env.sh"

if [[ -t 1 ]]; then
  COLOR_PASS=$'\033[0;32m'
  COLOR_WARN=$'\033[0;33m'
  COLOR_FAIL=$'\033[0;31m'
  COLOR_INFO=$'\033[0;36m'
  COLOR_RESET=$'\033[0m'
else
  COLOR_PASS=""
  COLOR_WARN=""
  COLOR_FAIL=""
  COLOR_INFO=""
  COLOR_RESET=""
fi

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

info() {
  printf '%sINFO%s %s\n' "${COLOR_INFO}" "${COLOR_RESET}" "$*"
}

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf '%sPASS%s %s\n' "${COLOR_PASS}" "${COLOR_RESET}" "$*"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf '%sWARN%s %s\n' "${COLOR_WARN}" "${COLOR_RESET}" "$*" >&2
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf '%sFAIL%s %s\n' "${COLOR_FAIL}" "${COLOR_RESET}" "$*" >&2
}

die() {
  fail "$*"
  exit 1
}

summary() {
  printf 'SUMMARY pass=%s warn=%s fail=%s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
}

finish_with_summary() {
  summary
  [[ "${FAIL_COUNT}" -eq 0 ]]
}

require_command() {
  local cmd="$1"
  command -v "${cmd}" >/dev/null 2>&1 || die "missing required command: ${cmd}"
}

inventory_query() {
  local query="$1"
  python3 - "${INVENTORY_FILE}" "${query}" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
query = sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines()


def indent_of(line):
    return len(line) - len(line.lstrip(" "))


def clean_value(value):
    value = value.strip()
    if not value:
        return ""
    if value[0:1] in ('"', "'") and value[-1:] == value[0]:
        return value[1:-1]
    return value


def top_section(name):
    start = None
    base_indent = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if indent_of(line) == 0 and stripped == f"{name}:":
            start = idx + 1
            base_indent = indent_of(line)
            break
    if start is None:
        return []
    end = len(lines)
    for idx in range(start, len(lines)):
        stripped = lines[idx].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if indent_of(lines[idx]) <= base_indent:
            end = idx
            break
    return lines[start:end]


def section_block(parent, key):
    section = top_section(parent)
    start = None
    key_indent = None
    for idx, line in enumerate(section):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == f"{key}:":
            start = idx + 1
            key_indent = indent_of(line)
            break
    if start is None:
        return []
    end = len(section)
    for idx in range(start, len(section)):
        stripped = section[idx].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if indent_of(section[idx]) <= key_indent:
            end = idx
            break
    return section[start:end]


def mapping_keys(parent):
    keys = []
    for line in top_section(parent):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- "):
            continue
        if indent_of(line) == 2 and stripped.endswith(":"):
            keys.append(stripped[:-1])
    return keys


def group_items(group):
    items = []
    for line in section_block("groups", group):
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(clean_value(stripped[2:]))
    return items


def package_group_items(group):
    section = top_section("package_groups")
    target = f"{group}:"
    for idx, line in enumerate(section):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if indent_of(line) == 2 and stripped.startswith(target):
            suffix = stripped[len(target):].strip()
            if suffix == "[]":
                return []
            items = []
            for sub in section[idx + 1:]:
                sub_stripped = sub.strip()
                if not sub_stripped or sub_stripped.startswith("#"):
                    continue
                if indent_of(sub) <= indent_of(line):
                    break
                if sub_stripped.startswith("- "):
                    items.append(clean_value(sub_stripped[2:]))
            return items
    return []


def device_value(device, key):
    for line in section_block("devices", device):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if indent_of(line) == 4 and stripped.startswith(f"{key}:"):
            return clean_value(stripped.split(":", 1)[1])
    return ""


def deploy_list(device, list_name):
    in_deploy = False
    in_list = False
    values = []
    deploy_indent = None
    list_indent = None
    for line in section_block("devices", device):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ind = indent_of(line)
        if ind == 4 and stripped == "deploy_packages:":
            in_deploy = True
            deploy_indent = ind
            continue
        if in_deploy and ind <= deploy_indent:
            break
        if not in_deploy:
            continue
        if ind == 6 and stripped.startswith(f"{list_name}:"):
            suffix = stripped.split(":", 1)[1].strip()
            if suffix == "[]":
                return []
            in_list = True
            list_indent = ind
            continue
        if in_list:
            if ind <= list_indent:
                break
            if stripped.startswith("- "):
                values.append(clean_value(stripped[2:]))
    return values


if query == "devices":
    print("\n".join(mapping_keys("devices")))
elif query.startswith("group:"):
    print("\n".join(group_items(query.split(":", 1)[1])))
elif query.startswith("package_group:"):
    print("\n".join(package_group_items(query.split(":", 1)[1])))
elif query.startswith("device:"):
    _, device, key = query.split(":", 2)
    print(device_value(device, key))
elif query.startswith("deploy:"):
    _, device, list_name = query.split(":", 2)
    print("\n".join(deploy_list(device, list_name)))
else:
    raise SystemExit(f"unknown inventory query: {query}")
PY
}

all_devices() {
  inventory_query "devices"
}

group_devices() {
  local group="$1"
  inventory_query "group:${group}"
}

is_device() {
  local needle="$1"
  local device
  while IFS= read -r device; do
    [[ "${device}" == "${needle}" ]] && return 0
  done < <(all_devices)
  return 1
}

is_group() {
  [[ -n "$(group_devices "$1")" ]]
}

expand_targets() {
  local target="${1:-all}"
  local device
  if is_device "${target}"; then
    printf '%s\n' "${target}"
    return 0
  fi
  if is_group "${target}"; then
    group_devices "${target}"
    return 0
  fi
  die "unknown device or group: ${target}"
}

device_value() {
  local device="$1"
  local key="$2"
  inventory_query "device:${device}:${key}"
}

device_ssh_host() {
  device_value "$1" "ssh_host"
}

device_remote_ws() {
  device_value "$1" "remote_ws"
}

device_ros_distro() {
  device_value "$1" "ros_distro"
}

device_build_jobs() {
  device_value "$1" "build_jobs"
}

device_arch() {
  device_value "$1" "arch"
}

device_role() {
  device_value "$1" "role"
}

device_deploy_groups() {
  inventory_query "deploy:${1}:include_groups"
}

device_deploy_include_packages() {
  inventory_query "deploy:${1}:include_packages"
}

device_deploy_exclude_packages() {
  inventory_query "deploy:${1}:exclude_packages"
}

package_group_members() {
  inventory_query "package_group:${1}"
}

list_contains() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    [[ "${item}" == "${needle}" ]] && return 0
  done
  return 1
}

append_unique() {
  local needle="$1"
  shift
  if list_contains "${needle}" "$@"; then
    return 1
  fi
  printf '%s\n' "${needle}"
}

device_selected_packages() {
  local device="$1"
  local selected=()
  local excludes=()
  local group
  local pkg

  while IFS= read -r group; do
    [[ -z "${group}" ]] && continue
    while IFS= read -r pkg; do
      [[ -z "${pkg}" ]] && continue
      if ! list_contains "${pkg}" "${selected[@]}"; then
        selected+=("${pkg}")
      fi
    done < <(package_group_members "${group}")
  done < <(device_deploy_groups "${device}")

  while IFS= read -r pkg; do
    [[ -z "${pkg}" ]] && continue
    if ! list_contains "${pkg}" "${selected[@]}"; then
      selected+=("${pkg}")
    fi
  done < <(device_deploy_include_packages "${device}")

  while IFS= read -r pkg; do
    [[ -z "${pkg}" ]] && continue
    excludes+=("${pkg}")
  done < <(device_deploy_exclude_packages "${device}")

  for pkg in "${selected[@]}"; do
    if ! list_contains "${pkg}" "${excludes[@]}"; then
      printf '%s\n' "${pkg}"
    fi
  done
}

package_args_for_device() {
  local device="$1"
  local mode="${2:---packages-up-to}"
  local packages=()
  local pkg
  while IFS= read -r pkg; do
    [[ -z "${pkg}" ]] && continue
    packages+=("${pkg}")
  done < <(device_selected_packages "${device}")

  if [[ "${#packages[@]}" -eq 0 ]]; then
    return 0
  fi

  printf '%s' "${mode}"
  for pkg in "${packages[@]}"; do
    printf ' %q' "${pkg}"
  done
}

ssh_host_for() {
  local device="$1"
  local host
  host="$(device_ssh_host "${device}")"
  [[ -n "${host}" ]] || die "device ${device} has no ssh_host"
  printf '%s\n' "${host}"
}

remote_ws_for() {
  local device="$1"
  local ws
  ws="$(device_remote_ws "${device}")"
  [[ -n "${ws}" ]] || die "device ${device} has no remote_ws"
  printf '%s\n' "${ws}"
}

ssh_quick() {
  local host="$1"
  shift
  # shellcheck disable=SC2086
  ssh ${SSH_OPTS} "${host}" "$@"
}

shell_quote() {
  printf '%q' "$1"
}

remote_path_expr() {
  local path="$1"
  if [[ "${path}" == "~" ]]; then
    printf '$HOME'
  elif [[ "${path}" == "~/"* ]]; then
    printf '$HOME/%s' "$(printf '%q' "${path#~/}")"
  else
    printf '%q' "${path}"
  fi
}

ssh_bash() {
  local host="$1"
  local script="$2"
  ssh_quick "${host}" "bash -lc $(shell_quote "${script}")"
}

ssh_tty() {
  local host="$1"
  shift
  # shellcheck disable=SC2086
  ssh -t ${SSH_OPTS} "${host}" "$@"
}

device_online() {
  local device="$1"
  local host
  host="$(ssh_host_for "${device}")"
  if ssh_quick "${host}" "true" >/dev/null 2>&1; then
    return 0
  fi
  warn "${device}: offline or SSH unavailable; skipping"
  return 1
}

join_by_space() {
  local first=1
  local item
  for item in "$@"; do
    if [[ "${first}" -eq 1 ]]; then
      printf '%s' "${item}"
      first=0
    else
      printf ' %s' "${item}"
    fi
  done
}

remote_env_prefix() {
  printf 'export ROS_DOMAIN_ID=%q RMW_IMPLEMENTATION=%q;' "${ROS_DOMAIN_ID}" "${RMW_IMPLEMENTATION}"
}

remote_ros_source_prefix() {
  local device="$1"
  local distro
  local remote_ws
  local remote_ws_expr
  local env_prefix
  distro="$(device_ros_distro "${device}")"
  remote_ws="$(remote_ws_for "${device}")"
  remote_ws_expr="$(remote_path_expr "${remote_ws}")"
  env_prefix="$(remote_env_prefix)"
  printf 'set -euo pipefail; %s source /opt/ros/%q/setup.bash; if [ -f %s/install/setup.bash ]; then source %s/install/setup.bash; fi; ' "${env_prefix}" "${distro}" "${remote_ws_expr}" "${remote_ws_expr}"
}
