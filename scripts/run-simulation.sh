#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run-simulation.sh — ClarkeYoursaTee / Sovereign Brain
# ---------------------------------------------------------------------------
# Purpose : Run the Sovereign Brain jar; auto-build if the jar is missing.
# Invoke  : ./scripts/run-simulation.sh [args...]
# Output  : SLF4J/logback log to stdout; no files written.
# Deps    : JDK 17 (java on PATH); Maven (only if jar absent).
# Notes   : args are forwarded verbatim to SovereignMain.
# ---------------------------------------------------------------------------
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f target/sovereign-brain-1.0.0-SOVEREIGN.jar ]]; then
    echo "⚠️  JAR not found, running build first..."
    ./scripts/build.sh
fi

java -jar target/sovereign-brain-1.0.0-SOVEREIGN.jar "$@"
