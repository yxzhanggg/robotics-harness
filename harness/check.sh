#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=harness/lib.sh
source "${SCRIPT_DIR}/lib.sh"

TARGET="${1:-}"
[[ -n "${TARGET}" ]] || die "usage: harness/check.sh <device|group>"

local_lint() {
  info "local: running best-effort lint"

  if command -v shellcheck >/dev/null 2>&1; then
    shellcheck "${SCRIPT_DIR}"/*.sh
    pass "local: shellcheck passed"
  else
    warn "local: shellcheck not installed; skipping shell lint"
  fi

  python3 - "${INVENTORY_FILE}" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
required = ["devices:", "groups:", "package_groups:"]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit(f"missing required inventory sections: {', '.join(missing)}")
PY
  pass "local: inventory structure check passed"

  python_files=()
  while IFS= read -r file; do
    python_files+=("${file}")
  done < <(find "${PROJECT_ROOT}" -path "${PROJECT_ROOT}/.git" -prune -o -name '*.py' -print)
  if [[ "${#python_files[@]}" -gt 0 ]]; then
    python3 -m py_compile "${python_files[@]}"
    pass "local: python syntax check passed"
  else
    pass "local: no python files to compile"
  fi
}

local_lint
"${SCRIPT_DIR}/deploy.sh" "${TARGET}"
"${SCRIPT_DIR}/remote-build.sh" "${TARGET}"
"${SCRIPT_DIR}/remote-test.sh" "${TARGET}"

pass "check: ${TARGET} passed"
finish_with_summary
