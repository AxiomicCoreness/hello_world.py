#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# build.sh — ClarkeYoursaTee / Sovereign Brain
# ---------------------------------------------------------------------------
# Purpose : Build the Maven jar for the Sovereign Brain.
# Invoke  : ./scripts/build.sh   (from repo root or from scripts/)
# Output  : target/sovereign-brain-1.0.0-SOVEREIGN.jar
# Deps    : JDK 17, Maven 3.9+
# Notes   : -q suppresses non-error Maven output; set -euo pipefail aborts on
#           any failure including unset variables.
# ---------------------------------------------------------------------------
set -euo pipefail

cd "$(dirname "$0")/.."
mvn -q clean package
echo "✅ Build complete: target/sovereign-brain-1.0.0-SOVEREIGN.jar"
