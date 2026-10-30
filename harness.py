#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Root CLI shim — python harness.py --local"""
from tests.harness import main

if __name__ == "__main__":
    raise SystemExit(main())
