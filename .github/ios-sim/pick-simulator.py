#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Print "<udid>\t<name>\t<runtime>" for the iPhone simulator to use: iPhone 12 if installed,
else the nearest available iPhone (13, 14, 15, 16, SE, then any), newest iOS runtime first."""
import json
import re
import subprocess
import sys

data = json.loads(subprocess.check_output(["xcrun", "simctl", "list", "devices", "available", "-j"]))
devices = []
for runtime, devs in data["devices"].items():
    m = re.search(r"iOS-(\d+)-(\d+)", runtime)
    if not m:
        continue
    ver = (int(m.group(1)), int(m.group(2)))
    for d in devs:
        if d.get("isAvailable") and d["name"].startswith("iPhone"):
            devices.append((ver, runtime, d))

prefs = ["iPhone 12", "iPhone 13", "iPhone 14", "iPhone 15", "iPhone 16", "iPhone 16e", "iPhone SE (3rd generation)"]

def rank(item):
    ver, _, d = item
    name = d["name"]
    p = prefs.index(name) if name in prefs else len(prefs)
    return (p, tuple(-v for v in ver))

if not devices:
    sys.exit("no available iPhone simulator")
ver, runtime, d = sorted(devices, key=rank)[0]
print(f"{d['udid']}\t{d['name']}\t{runtime.rsplit('.', 1)[-1]}")
