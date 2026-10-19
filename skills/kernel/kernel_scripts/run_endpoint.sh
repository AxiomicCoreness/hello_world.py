#!/usr/bin/env bash
# Compile Endpoint.java to /tmp/endpoint_classes and start it on 127.0.0.1:8025 in the background.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
JAVA_HOME="${JAVA_HOME:-/opt/jdk-17}"
OUT=/tmp/endpoint_classes; LOG=/tmp/endpoint.log; PIDF=/tmp/endpoint.pid
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then echo "[=] already running pid $(cat "$PIDF")"; exit 0; fi
if (exec 3<>/dev/tcp/127.0.0.1/8025) 2>/dev/null; then
  echo "[!] 127.0.0.1:8025 is already in use by a process not in $PIDF; not starting" >&2; exit 1
fi
mkdir -p "$OUT"
"$JAVA_HOME/bin/javac" -d "$OUT" "$HERE/kernel_scripts/java/com/fruitfly/brain/Endpoint.java"
nohup "$JAVA_HOME/bin/java" -Djava.awt.headless=true -Dhost=127.0.0.1 -Dport=8025 \
  -Dschema="$HERE/assets/render_schema.json" -cp "$OUT" com.fruitfly.brain.Endpoint >"$LOG" 2>&1 &
PID=$!; echo "$PID" > "$PIDF"
ok=0
for _ in $(seq 1 50); do
  kill -0 "$PID" 2>/dev/null || break
  curl -fs http://127.0.0.1:8025/healthz >/dev/null 2>&1 && { ok=1; break; }
  sleep 0.2
done
if [ "$ok" != 1 ] || ! kill -0 "$PID" 2>/dev/null; then
  echo "[!] endpoint failed to start (pid $PID); log $LOG:" >&2; cat "$LOG" >&2; rm -f "$PIDF"; exit 1
fi
echo "[+] pid $PID, log $LOG"; cat "$LOG"
