#!/usr/bin/env bash
# Regenerate src/test/resources/lif_rk4_golden_traces.txt from the REAL root
# LIFRK4 (src/main/java/com/fruitfly/brain/LIFRK4.java). Run from anywhere in
# the repo, with JDK 17 on PATH. Then run `mvn -B test` in games/teavm-rhythm:
# LifRk4ParityTest fails if the game's LifNeuron port no longer matches.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"          # games/teavm-rhythm
root="$(cd "$here/../.." && pwd)"                 # repo root
src="$root/src/main/java/com/fruitfly/brain/LIFRK4.java"
out="$here/src/test/resources/lif_rk4_golden_traces.txt"
[ -f "$src" ] || { echo "missing $src" >&2; exit 1; }
label="src/main/java/com/fruitfly/brain/LIFRK4.java"
if git -C "$root" rev-parse --git-dir >/dev/null 2>&1; then
  commit="$(git -C "$root" rev-parse --short=8 HEAD)"
  blob="$(git -C "$root" hash-object "$src")"
  label="$label@$commit blob=$blob"
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
javac --release 17 -d "$tmp" "$src" "$here/tools/LifGoldenTraceGen.java"
java -cp "$tmp" LifGoldenTraceGen "$out" "$label"
echo "wrote $out ($(wc -l < "$out") lines) from $label"
