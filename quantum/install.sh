#!/bin/bash
set -e

echo "🜁∀ INSTALLING SOVEREIGN GARDEN DEPENDENCIES..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

if [ -n "${GARDEN_LOG_DIR:-}" ]; then
  LOG_DIR="$GARDEN_LOG_DIR"
elif [ -w /var/log ] 2>/dev/null || mkdir -p /var/log 2>/dev/null; then
  LOG_DIR="/var/log"
else
  LOG_DIR="$ROOT/logs"
fi
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/garden_web.log"
PID_FILE="$LOG_DIR/garden_web.pid"

if command -v pip3 >/dev/null 2>&1; then
  pip3 install --user flask eth-account 2>/dev/null || pip3 install flask eth-account
else
  echo "ERROR: pip3 not found" >&2
  exit 1
fi

if [ -w /etc/environment ] 2>/dev/null; then
  grep -q "PYTHONPATH=.*$ROOT" /etc/environment 2>/dev/null \
    || echo "PYTHONPATH=$ROOT:\${PYTHONPATH}" >> /etc/environment
else
  grep -q "PYTHONPATH=.*$ROOT" "$HOME/.bashrc" 2>/dev/null \
    || echo "export PYTHONPATH=$ROOT:\$PYTHONPATH" >> "$HOME/.bashrc"
fi
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"

if command -v systemctl >/dev/null 2>&1 && [ -d /etc/systemd/system ]; then
  if [ -f "$ROOT/quantum/systemd/ouroboros_mint.service" ]; then
    sudo cp "$ROOT/quantum/systemd/ouroboros_mint.service" /etc/systemd/system/ || true
    sudo cp "$ROOT/quantum/systemd/ouroboros_mint.timer" /etc/systemd/system/ || true
    sudo systemctl daemon-reload || true
    sudo systemctl enable --now ouroboros_mint.timer || true
  fi
fi

pkill -f "python3 -m peqs_vault.app" 2>/dev/null || true
sleep 0.5
nohup env PYTHONPATH="$ROOT" python3 -m peqs_vault.app > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo "✅ SOVEREIGN GARDEN DEPLOYED."
echo "🌐 Dashboard available at http://127.0.0.1:5000"
echo "📝 Web log: $LOG_FILE"
