#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MANIFEST="${SCRIPT_DIR}/lock-manifest.sha256"

if [[ ! -f "${MANIFEST}" ]]; then
  printf 'FAIL harness lock manifest missing: %s\n' "${MANIFEST}" >&2
  exit 1
fi

python3 - "${PROJECT_ROOT}" "${MANIFEST}" <<'PY'
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = Path(sys.argv[2])
failures = []
protected = set()
checked = 0

for line_no, raw_line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    try:
        expected, rel_path = line.split(None, 1)
    except ValueError:
        failures.append(f"{manifest}:{line_no}: malformed manifest line")
        continue

    protected.add(rel_path)
    if expected == "LOCK_MANIFEST":
        if rel_path != "harness/lock-manifest.sha256":
            failures.append(f"{manifest}:{line_no}: LOCK_MANIFEST must target harness/lock-manifest.sha256")
        continue

    path = root / rel_path
    if not path.is_file():
        failures.append(f"{rel_path}: missing")
        continue

    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    checked += 1
    if actual != expected:
        failures.append(f"{rel_path}: hash mismatch")

harness_dir = root / "harness"
if harness_dir.is_dir():
    for path in sorted(harness_dir.rglob("*")):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root).as_posix()
        if rel_path not in protected:
            failures.append(f"{rel_path}: unprotected harness file")

if failures:
    print("FAIL harness lock verification failed", file=sys.stderr)
    for failure in failures:
        print(f"  - {failure}", file=sys.stderr)
    print(
        "Protected harness files changed. Revert the change or ask explicitly "
        "for a harness unlock/update.",
        file=sys.stderr,
    )
    raise SystemExit(1)

print(f"PASS harness lock verified ({checked} files)")
PY
