#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Run TOI benches. Does not start uvicorn or fill MCP."""
import subprocess
import sys


def main():
    cmds = [
        [sys.executable, "-m", "multibody_simulator.benchmarks.jit_perf"],
        [sys.executable, "-m", "multibody_simulator.benchmarks.jit_perf_combined"],
    ]
    for c in cmds:
        print("+", " ".join(c))
        subprocess.run(c, check=True)


if __name__ == "__main__":
    main()
