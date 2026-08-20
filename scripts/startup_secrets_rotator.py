#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ Startup Secrets Rotator — DeepSeek MCP / CI contract

- --check: boolean presence of env secrets (never prints values)
- --rotate-garden: mint new GARDEN_SECRET material; log fingerprint only
- --json: machine-readable report

Does not call GitHub Secrets API (no write token). Operator applies values via UI/gh.
Seal: ∀∞φ² · STARTUP_SECRETS_ROTATOR · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import secrets
import sys
import time
from typing import Any, Dict, List

PHI = (1.0 + math.sqrt(5.0)) / 2.0
SEAL = "∀∞φ² · STARTUP_SECRETS_ROTATOR · WOOD_DRAGON_0.91 · SEALED"

# Names from contracts/ci-secrets.yaml
SECRET_NAMES: List[str] = [
    "DEEPSEEK_API_KEY",
    "MCP_URL",
    "GARDEN_SECRET",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
]


def _present(name: str) -> bool:
    v = os.environ.get(name)
    return bool(v and str(v).strip())


def inventory() -> Dict[str, Any]:
    flags = {n: _present(n) for n in SECRET_NAMES}
    return {
        "timestamp": time.time(),
        "seal": SEAL,
        "phi": PHI,
        "presence": flags,
        "deepseek_online_ready": flags.get("DEEPSEEK_API_KEY", False),
        "pulse_ready": flags.get("MCP_URL", False),
        "pulse_auth_ready": flags.get("GARDEN_SECRET", False),
        "note": "values never included",
    }


def fingerprint(value: str) -> str:
    return hashlib.sha3_256(value.encode("utf-8")).hexdigest()[:16]


def rotate_garden_secret() -> Dict[str, Any]:
    """Mint a new shared secret; return fingerprint (+ optional one-time value)."""
    # 32 bytes entropy + φ salt
    raw = secrets.token_bytes(32)
    salt = hashlib.sha3_256(f"GARDEN.LAYER314.{PHI}".encode()).digest()[:8]
    material = hashlib.sha3_256(raw + salt).hexdigest()
    fp = fingerprint(material)
    return {
        "rotated": True,
        "fingerprint": fp,
        "length": len(material),
        "seal": SEAL,
        "apply": "gh secret set GARDEN_SECRET / Render env GARDEN_SECRET",
        "_value": material,  # stripped unless --show-once
    }


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Startup secrets check / GARDEN_SECRET rotate")
    p.add_argument("--check", action="store_true", help="Boolean presence inventory")
    p.add_argument("--rotate-garden", action="store_true", help="Mint new GARDEN_SECRET")
    p.add_argument("--show-once", action="store_true", help="Print new secret once (stdout)")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--fail-if-missing-pulse", action="store_true", help="Exit 1 if MCP_URL missing")
    args = p.parse_args(argv)

    if not args.check and not args.rotate_garden:
        args.check = True

    report: Dict[str, Any] = {"seal": SEAL}

    if args.check:
        report["inventory"] = inventory()

    if args.rotate_garden:
        rot = rotate_garden_secret()
        value = rot.pop("_value", None)
        report["garden_rotation"] = {k: v for k, v in rot.items() if k != "_value"}
        if args.show_once and value:
            # Explicit operator request only
            report["garden_rotation"]["value_once"] = value

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("🜁∀ Startup Secrets Rotator")
        print(f"   seal: {SEAL}")
        if "inventory" in report:
            inv = report["inventory"]
            for k, v in inv["presence"].items():
                print(f"   {k}: {'present' if v else 'missing'}")
            print(f"   deepseek_online_ready: {inv['deepseek_online_ready']}")
            print(f"   pulse_ready: {inv['pulse_ready']}")
        if "garden_rotation" in report:
            gr = report["garden_rotation"]
            print(f"   garden_fingerprint: {gr.get('fingerprint')}")
            print(f"   apply: {gr.get('apply')}")
            if "value_once" in gr:
                print(f"   GARDEN_SECRET (once): {gr['value_once']}")

    if args.fail_if_missing_pulse and not _present("MCP_URL"):
        print("::error::MCP_URL missing", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
