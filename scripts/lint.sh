#!/usr/bin/env bash
# scripts/lint.sh — one-surface lint gate.
# 1. runs Java + Python + kernel gates
# 2. appends a fixed-form lint block to notes_to_kernel.md
# 3. pipes the summary through wired_kernel.adjudicate()
set -euo pipefail

cd "$(dirname "$0")/.."

KERNEL="${KERNEL:-wired_kernel.py}"
NOTES="${NOTES:-notes_to_kernel.md}"
LOG="${LOG:-.lint.log}"
FAIL=0

: > "$LOG"

run_gate() {                      # $1=name  $2..=command
    local name="$1"; shift
    printf '[%s] %s\n' "$name" "$*" | tee -a "$LOG"
    if "$@" >>"$LOG" 2>&1; then
        printf '  ✅ %s\n' "$name" | tee -a "$LOG"
        printf '%s:VERIFIED\n' "$name"
    else
        printf '  ❌ %s\n' "$name" | tee -a "$LOG"
        printf '%s:FALSE\n' "$name"
        FAIL=1
    fi
}

append_block() {                  # the lint block: 5 lines, fixed shape
    local ts
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    {
        printf '\n'
        printf '## lint block — %s\n' "$ts"
        printf 'java:%s\n'   "$1"
        printf 'python:%s\n' "$2"
        printf 'kernel:%s\n' "$3"
        printf 'status:%s\n' "$4"
    } >> "$NOTES"
}

mapfile -t RESULTS < <(
    {
        run_gate "mvn-test"    mvn -B -q test
        run_gate "py-compile"  python3 -m compileall -q scripts
        run_gate "kernel-self" python3 "$KERNEL"
    }
)

pick() { printf '%s\n' "${RESULTS[@]}" | awk -F: -v n="$1" '$1==n{print $2; exit}'; }

J="$(pick mvn-test)"
P="$(pick py-compile)"
K="$(pick kernel-self)"
S="PASS"; [ "$FAIL" = "1" ] && S="FAIL"

append_block "${J:-MISSING}" "${P:-MISSING}" "${K:-MISSING}" "$S"
printf '\n📝 appended lint block to %s\n' "$NOTES"

python3 - "$KERNEL" "$NOTES" <<'PY'
import importlib.util, json, pathlib, sys

kernel_path, notes_path = sys.argv[1], sys.argv[2]

spec = importlib.util.spec_from_file_location("wired_kernel", kernel_path)
mod  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

raw        = pathlib.Path(notes_path).read_text(encoding="utf-8")
last_block = raw.strip().split("\n\n")[-1]

digests = []
for line in last_block.splitlines():
    token = line.split(":", 1)[-1].strip()
    if token and all(c in "0123456789abcdefABCDEF" for c in token):
        digests.append(token)

record = mod.adjudicate(
    text=last_block,
    provided_bytes=last_block.encode("utf-8"),
    hex_digests=digests,
)

print(json.dumps(record, indent=2, default=str))
sys.exit(0 if record["verdict"] != "FALSE" else 1)
PY

exit "$FAIL"
