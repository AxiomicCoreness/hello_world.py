#!/usr/bin/env python3
"""Root CLI shim — python harness.py --local"""
from tests.harness import main

if __name__ == "__main__":
    raise SystemExit(main())
