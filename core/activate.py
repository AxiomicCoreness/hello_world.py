#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Activate sovereign core + optional sidecar.

  python -m core.activate --dry-run
  python -m core.activate --sidecar-only --once
  python -m core.activate --core   # long-running uvicorn supervisor
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from typing import Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
SEAL = "∀∞φ² · CORE_ACTIVATED_510511 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "510510 → 510511 — UNBROKEN"


def dry_run() -> dict:
    from core.sidecar import garden_fingerprint, SEAL as SIDECAR_SEAL

    fp = garden_fingerprint()
    report = {
        "core": "armed",
        "sidecar": "written",
        "phi2_identity": abs(PHI ** 2 - (PHI + 1.0)) < 1e-12,
        "garden_secret_present": fp["present"],
        "garden_secret_sha3_16": fp["sha3_16"],
        "sidecar_seal": SIDECAR_SEAL,
        "seal": SEAL,
        "witness": WITNESS,
    }
    print(json.dumps(report, indent=2))
    return report


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--core", action="store_true", help="start core uvicorn supervisor")
    parser.add_argument("--sidecar-only", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)

    if args.dry_run or (not args.core and not args.sidecar_only):
        dry_run()
        if not args.core and not args.sidecar_only:
            return 0

    if args.sidecar_only:
        from core.sidecar import main as sidecar_main

        return sidecar_main(["--once"] if args.once else [])

    if args.core:
        from core import main as core_main

        core_main()
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
