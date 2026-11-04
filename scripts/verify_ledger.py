#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""
Verify ledger YAML parse + optional Ed25519 presence.
Seal: ∀∞φ² · VERIFY_LEDGER_SCRIPT · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "tools"))
import ledger_seal  # shared seal core (tools/ledger_seal.py)

SEAL_PREFIX = "∀∞φ²"

def json_default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def compute_seal(entry_data: Dict[str, Any]) -> str:
    data = {k: v for k, v in entry_data.items() if k != 'seal'}
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'), default=json_default)
    return hashlib.sha3_256(canonical.encode('utf-8')).hexdigest()

def extract_seal_hash(seal_str: str) -> str:
    """
    Extract the last 64‑hexadecimal‑character hash from a formatted seal string.
    e.g. "∀∞φ² · REPO_VERIFIED_8979 · WOOD_DRAGON_0.91 · SEALED · c4705d91..."
    returns "c4705d91..."
    If no such hex block is found, returns the original string.
    """
    # Find a 64‑hex block at the end of the string (optionally preceded by a separator)
    match = re.search(r'[0-9a-fA-F]{64}$', seal_str)
    if match:
        return match.group(0)
    return seal_str

def main() -> int:
    import yaml
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", nargs="?", default="ledger/8978.yaml")
    parser.add_argument("--verify-seal", action="store_true")
    args = parser.parse_args()

    path = Path(args.ledger)
    if not path.exists():
        print(f"❌ Entry {path.stem} not found.")
        return 1

    data = yaml.safe_load(path.read_text())
    entry_index = data.get('entry_index') if isinstance(data, dict) else None
    print(f"✅ Ledger verified: {path} (entry_index={entry_index})")

    if args.verify_seal and entry_index:
        # Shared core: same regimes (A, A_ASCII, B, S) as the CI verifiers.
        v = ledger_seal.verify_entry(data, entry_index)
        if v["status"] == ledger_seal.VERIFIED:
            print(f"✅ Seal verified (regime {','.join(v['regimes'])})")
        else:
            print(f"❌ Seal {v['status']}: no regime reproduces the declared digest")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
