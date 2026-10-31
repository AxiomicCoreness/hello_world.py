#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
#
# shoot.sh <udid> <bundle-id> <out-dir> <name>:<wait-seconds>[:<launch args, comma-separated>] ...
# For each screen: launch the (already installed) app fresh with its launch arguments, wait,
# `simctl io screenshot`, terminate. Launch arguments like `-selectedTab 2` land in the
# NSArgumentDomain, so @AppStorage/UserDefaults read them without any change to the app.
# No taps, no typing: the apps never send a chat line.
# macOS ships bash 3.2: an empty array is "unbound" under set -u, hence ${a[@]+"${a[@]}"}.
set -euo pipefail
udid=$1 bundle=$2 out=$3
shift 3
mkdir -p "$out"
for spec in "$@"; do
  IFS=: read -r name wait args <<<"$spec"
  launch_args=()
  if [ -n "${args:-}" ]; then
    IFS=, read -r -a parts <<<"$args"
    for p in "${parts[@]}"; do
      # "-selectedTab 2" -> two argv entries
      read -r -a words <<<"$p"
      launch_args+=("${words[@]}")
    done
  fi
  xcrun simctl terminate "$udid" "$bundle" >/dev/null 2>&1 || true
  echo "== $name: launch ${launch_args[*]+${launch_args[*]}}, wait ${wait}s"
  xcrun simctl launch --terminate-running-process "$udid" "$bundle" ${launch_args[@]+"${launch_args[@]}"}
  sleep "$wait"
  xcrun simctl io "$udid" screenshot --type=png "$out/$name.png"
  echo "   saved $out/$name.png ($(stat -f%z "$out/$name.png") bytes) at $(TZ=America/New_York date +%Y-%m-%dT%H:%M:%S%z | sed -E 's/([0-9]{2})$/:\1/')"
done
xcrun simctl terminate "$udid" "$bundle" >/dev/null 2>&1 || true
