#!/usr/bin/env bash
# Supervisor: keeps 127.0.0.1:8085 (deepseek-r2 llama-server) and 127.0.0.1:6680 (bridge) up.
# Checks every 10 s by listening port; restarts via the launch scripts if a port is gone.
# Single instance (flock). Stop: kill "$(cat "$RUN_DIR/keepalive.pid")"
# Env: RUN_DIR (pid/lock/log location), LLAMA_LAUNCH, BRIDGE_LAUNCH (default: sibling scripts).
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="${RUN_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/sovereign-bridge}"
mkdir -p "$RUN_DIR"
LOCK="$RUN_DIR/keepalive.lock"
exec 9>"$LOCK"
flock -n 9 || { echo "keepalive already running"; exit 0; }
echo $$ > "$RUN_DIR/keepalive.pid"
LOG="$RUN_DIR/keepalive.log"
LLAMA_LAUNCH="${LLAMA_LAUNCH:-$SCRIPT_DIR/launch-8085-deepseek-r2.sh}"
BRIDGE_LAUNCH="${BRIDGE_LAUNCH:-$SCRIPT_DIR/launch-6680-deepseek-r2.sh}"
listening() { ss -ltn "sport = :$1" | grep -q "127.0.0.1:$1"; }
log() { echo "$(date '+%F %T %Z') $*" >> "$LOG"; }
log "keepalive start pid $$"
while true; do
  if ! listening 8085; then
    log "8085 down -> restarting llama-server"
    nohup setsid "$LLAMA_LAUNCH" >> "$RUN_DIR/llama-8085.log" 2>&1 < /dev/null &
    for _ in $(seq 1 60); do listening 8085 && break; sleep 2; done
    listening 8085 && log "8085 up" || log "8085 still down after 120 s"
  fi
  if ! listening 6680; then
    log "6680 down -> restarting bridge"
    nohup setsid "$BRIDGE_LAUNCH" >> "$RUN_DIR/bridge.log" 2>&1 < /dev/null &
    for _ in $(seq 1 30); do listening 6680 && break; sleep 1; done
    listening 6680 && log "6680 up" || log "6680 still down after 30 s (see $RUN_DIR/bridge.log)"
  fi
  sleep 10
done
