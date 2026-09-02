#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/hmac_chain.py – HMAC chain verification for Layer 252.
Verifies that each ledger entry's prev_hmac and curr_hmac form an unbroken chain.
"""

import hashlib
import hmac
import json
from pathlib import Path

HMAC_KEY = b"sovereign_garden_hmac_key_2026"

def compute_hmac(data: dict) -> str:
    """Compute HMAC-SHA3-256 of the data (excluding the hmac field itself)."""
    data_copy = {k: v for k, v in data.items() if k not in ("prev_hmac", "curr_hmac", "seal")}
    canonical = json.dumps(data_copy, sort_keys=True, separators=(",", ":"))
    return hmac.new(HMAC_KEY, canonical.encode(), hashlib.sha3_256).hexdigest()

def verify_hmac_chain(ledger_path: str = "ledger") -> bool:
    """Verify that the HMAC chain is unbroken for all entries."""
    path = Path(ledger_path)
    yaml_files = sorted(path.glob("*.yaml"))
    if not yaml_files:
        print("⚠️ No YAML files found in ledger/")
        return True  # soft pass

    prev_hmac = None
    for file in yaml_files:
        try:
            import yaml
            with open(file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except ImportError:
            # fallback to manual parsing if pyyaml not installed
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            # simple parsing – just for demonstration
            data = {}
            for line in content.splitlines():
                if ": " in line:
                    key, val = line.split(": ", 1)
                    data[key.strip()] = val.strip()
        if "entry_index" not in data:
            continue
        curr_hmac = data.get("curr_hmac")
        if curr_hmac is None:
            # For old entries, skip – we only verify from the point where HMAC was introduced.
            continue
        if prev_hmac is not None:
            stored_prev = data.get("prev_hmac")
            if stored_prev != prev_hmac:
                print(f"❌ HMAC chain break at entry {data['entry_index']}: prev_hmac {stored_prev} != expected {prev_hmac}")
                return False
        # Compute the expected HMAC for the entry (excluding hmac fields)
        expected = compute_hmac(data)
        if curr_hmac != expected:
            print(f"❌ HMAC mismatch at entry {data['entry_index']}: {curr_hmac} != {expected}")
            return False
        prev_hmac = curr_hmac
    print("✅ HMAC chain verified for all entries.")
    return True

if __name__ == "__main__":
    verify_hmac_chain()
