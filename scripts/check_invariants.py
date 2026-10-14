#!/usr/bin/env python3
"""CLI for the structure invariants catalogue."""
from __future__ import annotations

import argparse
import sys

from invariants import CHECKS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on", choices=["error", "warning", "any"], default="error")
    args = parser.parse_args()

    failed = 0
    for inv in CHECKS:
        result = inv.check()
        mark = "PASS" if result.passed else "FAIL"
        print(f"[{mark}] {result.name:<24} {result.detail}")
        if not result.passed:
            failed += 1
            if result.remediation:
                print(f"         remediation: {result.remediation}")

    if args.fail_on == "any" and failed:
        return 1
    if args.fail_on == "error" and failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
