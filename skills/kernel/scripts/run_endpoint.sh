#!/usr/bin/env bash
# Compile Endpoint.java to /tmp/endpoint_classes and start it on 127.0.0.1:8025 in the background.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
JAVA_HOME="${JAVA_HOME:-/opt/jdk-17}"
OUT=/tmp/endpoint_classes; LOG=/tmp/endpoint.log; PIDF=/tmp/endpoint.pid
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then echo "[=] already running pid $(cat "$PIDF")"; exit 0; fi
mkdir -p "$OUT"
"$JAVA_HOME/bin/javac" -d "$OUT" "$HERE/scripts/java/com/fruitfly/brain/Endpoint.java"
nohup "$JAVA_HOME/bin/java" -Djava.awt.headless=true -Dhost=127.0.0.1 -Dport=8025 \
  -Dschema="$HERE/assets/render_schema.json" -cp "$OUT" com.fruitfly.brain.Endpoint >"$LOG" 2>&1 &
echo $! > "$PIDF"
for _ in $(seq 1 50); do curl -fs http://127.0.0.1:8025/healthz >/dev/null 2>&1 && break; sleep 0.2; done
echo "[+] pid $(cat "$PIDF"), log $LOG"; cat "$LOG"
