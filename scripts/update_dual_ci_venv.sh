#!/usr/bin/env bash
# Update local .venv for dual CI (control lane + bin-layer lane).
# Does not commit .venv. Does not bind 0.0.0.0. MCP stays unfilled.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
VENV="${VENV_DIR:-.venv}"
"$PY" -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements-control.txt
if [ "${DUAL_CI_RUNTIME:-0}" = "1" ] && [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt || true
fi
python -m pip show pytest pyyaml fastapi >/dev/null
echo "dual-ci venv ready: $VENV"
echo "MCP FILLED=false DUAL_ASGI=127.0.0.1:8024"
