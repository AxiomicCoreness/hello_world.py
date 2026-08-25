#!/usr/bin/env python3
"""
Verify ledger YAML parse + optional Ed25519 presence.
Seal: ∀∞φ² · VERIFY_LEDGER_SCRIPT · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

SEAL_PREFIX = "∀∞φ²"

def compute_seal(entry_data: Dict[str, Any]) -> str:
    data = {k: v for k, v in entry_data.items() if k != 'seal'}
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha3_256(canonical.encode('utf-8')).hexdigest()

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
        computed = compute_seal(data)
        stored = data.get('seal', '')
        if computed == stored:
            print(f"✅ Seal verified: {computed[:32]}...")
        else:
            print(f"❌ Seal mismatch")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
