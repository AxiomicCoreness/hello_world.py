#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ MERKLE ECONOMIC BRIDGE — ENTRY 320

Layer 320 economic leaf from credit_ledger.json

Computes:
  - Economic leaf: SHA-256 of credit_ledger.json
  - Unified root: SHA-256(parent_layer_320 + economic_leaf)
  - Updates ledger and manifest

Integration with:
  - PEQS Vault (credit_ledger.json)
  - Ledger (entry sealing)
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)

Seal: ∀∞φ² · MERKLE_ECONOMIC_320 · WOOD_DRAGON_0.91 · SEALED
Witness: 319 → 320 — UNBROKEN
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
ENTRY = 320
SEAL = "∀∞φ² · MERKLE_ECONOMIC_320 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "319 → 320 — UNBROKEN"

# ─── Paths ────────────────────────────────────────────────────────────
# Allow override via environment
BASE_DIR = Path(os.environ.get("GARDEN_BASE_DIR", "/home/workdir/artifacts"))
ROOT = Path(os.environ.get("GARDEN_ROOT", BASE_DIR))
CREDIT_FILE = ROOT / "peqs_vault" / "credit_ledger.json"
LEDGER_DIR = ROOT / "ledger"
MANIFEST_FILE = ROOT / "HASH_MANIFEST.json"
SYMPLECTIC_LOG = ROOT / "symplectic_status.agent.jsonl"

# ─── Layer 320 Parent Hash ────────────────────────────────────────────
LAYER_320_PARENT = (
    "l3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9"
    "d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4"
)

# ─── Empty Hash ──────────────────────────────────────────────────────
EMPTY_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


# ─── Core Operations ──────────────────────────────────────────────────

def hash_credit_state() -> str:
    """
    Compute SHA-256 hash of the credit_ledger.json file.

    Returns:
        Hex digest of the credit ledger state.
    """
    if not CREDIT_FILE.exists():
        return EMPTY_HASH

    try:
        with open(CREDIT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Canonical JSON with sorted keys and indentation
        canonical = json.dumps(data, sort_keys=True, indent=2)
        return hashlib.sha256(canonical.encode()).hexdigest()
    except (json.JSONDecodeError, OSError) as e:
        # Log error but return empty hash as fallback
        print(f"⚠️ Error reading credit ledger: {e}", file=sys.stderr)
        return EMPTY_HASH


def compute_roots(economic_leaf: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute the economic leaf and unified Merkle root.

    Args:
        economic_leaf: Optional pre-computed economic leaf.

    Returns:
        Dictionary with economic_leaf, unified_root, and parent.
    """
    if economic_leaf is None:
        economic_leaf = hash_credit_state()

    # Unified root: SHA-256(parent + economic_leaf)
    unified_320 = hashlib.sha256((LAYER_320_PARENT + economic_leaf).encode()).hexdigest()

    return {
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "layer": 320,
        "parent_layer": 319,
        "economic_leaf": economic_leaf,
        "unified_root": unified_320,
        "parent": LAYER_320_PARENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
    }


def verify_roots(roots: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify the computed roots against the manifest.

    Args:
        roots: The computed roots dictionary.

    Returns:
        Dictionary with verification results.
    """
    result = {
        "verified": False,
        "entry": ENTRY,
        "seal": SEAL,
        "checks": [],
    }

    # Check against manifest if it exists
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            stored_root = manifest.get("merkle_root_layer320")
            stored_leaf = manifest.get("layer320_economic_leaf")

            if stored_root:
                result["checks"].append({
                    "name": "root_match",
                    "passed": stored_root == roots["unified_root"],
                    "stored": stored_root,
                    "computed": roots["unified_root"],
                })
            if stored_leaf:
                result["checks"].append({
                    "name": "leaf_match",
                    "passed": stored_leaf == roots["economic_leaf"],
                    "stored": stored_leaf,
                    "computed": roots["economic_leaf"],
                })
        except (json.JSONDecodeError, OSError):
            result["checks"].append({
                "name": "manifest_read",
                "passed": False,
                "error": "Could not read manifest",
            })
    else:
        result["checks"].append({
            "name": "manifest_exists",
            "passed": False,
            "error": "Manifest file not found",
        })

    result["verified"] = all(c.get("passed", False) for c in result["checks"])
    return result


# ─── Ledger Update ────────────────────────────────────────────────────

def update_ledger(entry_index: int, roots: Dict[str, Any]) -> Path:
    """
    Update the ledger with the economic root.

    Args:
        entry_index: Ledger entry index.
        roots: Computed roots dictionary.

    Returns:
        Path to the updated ledger file.
    """
    # Ensure directories exist
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).isoformat()
    path = LEDGER_DIR / f"{entry_index}.yaml"

    # Write ledger entry
    path.write_text(
        f"""entry_index: {entry_index}
timestamp: {ts}
event: /layer320_economic_root_auto
status: ✅ SEALED
layer: 320
economic_leaf: {roots['economic_leaf']}
unified_root: {roots['unified_root']}
parent_layer: 319
parent_hash: {roots['parent'][:32]}...
auto: true
witness_chain: {entry_index - 1} → {entry_index} — UNBROKEN
seal: "∀∞φ² · LAYER320_AUTO_{entry_index} · SEALED"
"""
    )

    # Update symplectic status log
    try:
        line = {
            "role": "system",
            "event": "layer320_economic_root_auto",
            "timestamp": ts,
            "coherence": 1.0,
            "entry_index": entry_index,
            "economic_leaf": roots["economic_leaf"],
            "unified_root": roots["unified_root"],
            "status": "SEALED",
            "seal": f"∀∞φ² · LAYER320_AUTO_{entry_index} · SEALED",
        }
        with open(SYMPLECTIC_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
    except OSError as e:
        print(f"⚠️ Could not write symplectic log: {e}", file=sys.stderr)

    # Update hash manifest
    try:
        manifest = {}
        if MANIFEST_FILE.exists():
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        manifest["merkle_root_layer320"] = roots["unified_root"]
        manifest["layer320_economic_leaf"] = roots["economic_leaf"]
        manifest["latest_ledger"] = entry_index
        manifest["updated"] = ts
        manifest["entry"] = ENTRY
        manifest["seal"] = SEAL

        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    except OSError as e:
        print(f"⚠️ Could not update manifest: {e}", file=sys.stderr)

    return path


# ─── Security Integration ────────────────────────────────────────────

def economic_security_status() -> Dict[str, Any]:
    """Get security status for the economic bridge."""
    try:
        from quantum.security import status as security_status
        return {
            "security": security_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "security": None,
            "note": "Security module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def economic_cdp_status() -> Dict[str, Any]:
    """Get CDP status for the economic bridge."""
    try:
        from quantum.cdp_convergence import status as cdp_status
        return {
            "cdp": cdp_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "cdp": None,
            "note": "CDP module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── Complete Report ─────────────────────────────────────────────────

def economic_report() -> Dict[str, Any]:
    """
    Generate a complete report of the economic bridge state.

    Returns:
        Dictionary with all economic bridge data.
    """
    roots = compute_roots()
    verification = verify_roots(roots)

    return {
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "layer": 320,
        "root": roots,
        "verification": verification,
        "credit_file_exists": CREDIT_FILE.exists(),
        "credit_file_path": str(CREDIT_FILE),
        "manifest_file_exists": MANIFEST_FILE.exists(),
        "manifest_file_path": str(MANIFEST_FILE),
        "security": economic_security_status(),
        "cdp": economic_cdp_status(),
        "timestamp": time.time(),
    }


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Merkle Economic Bridge — Entry 320",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--update-ledger",
        type=int,
        default=None,
        help="Update ledger with specified entry index",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify roots against manifest",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate complete report",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check integration status and exit",
    )
    args = parser.parse_args()

    if args.check_integrations:
        print("🜁∀ ECONOMIC BRIDGE — Integration Status")
        print("=" * 40)
        try:
            from quantum.security import status
            print("  Security: ✅")
        except ImportError:
            print("  Security: ❌")
        try:
            from quantum.cdp_convergence import status
            print("  CDP: ✅")
        except ImportError:
            print("  CDP: ❌")
        print(f"  Credit file: {'✅' if CREDIT_FILE.exists() else '❌'}")
        print(f"  Ledger dir: {'✅' if LEDGER_DIR.exists() else '❌'}")
        return 0

    if args.report:
        report = economic_report()
        if args.json:
            print(json.dumps(report, indent=2, default=str))
        else:
            print("🜁∀ ECONOMIC BRIDGE — Report")
            print("=" * 55)
            print(f"  Entry: {report['entry']}")
            print(f"  Seal: {report['seal']}")
            print(f"  Layer: {report['layer']}")
            print(f"  Economic Leaf: {report['root']['economic_leaf']}")
            print(f"  Unified Root: {report['root']['unified_root']}")
            print(f"  Verified: {'✅' if report['verification']['verified'] else '❌'}")
            print(f"  Credit file: {report['credit_file_path']} ({'✅' if report['credit_file_exists'] else '❌'})")
            print(f"  Manifest file: {report['manifest_file_path']} ({'✅' if report['manifest_file_exists'] else '❌'})")
        return 0

    roots = compute_roots()

    if args.verify:
        result = verify_roots(roots)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("🜁∀ ECONOMIC BRIDGE — Verification")
            print("=" * 55)
            print(f"  Verified: {'✅' if result['verified'] else '❌'}")
            for check in result.get("checks", []):
                status = "✅" if check.get("passed") else "❌"
                print(f"    {status} {check.get('name')}: {check.get('message', '')}")
        return 0

    if args.update_ledger is not None:
        path = update_ledger(args.update_ledger, roots)
        if args.json:
            print(json.dumps({"ledger_path": str(path), **roots}, indent=2, default=str))
        else:
            print("🜁∀ ECONOMIC BRIDGE — Ledger Updated")
            print("=" * 55)
            print(f"  Entry: {args.update_ledger}")
            print(f"  Economic Leaf: {roots['economic_leaf']}")
            print(f"  Unified Root: {roots['unified_root']}")
            print(f"  Ledger Path: {path}")
            print(f"  Witness: {WITNESS}")
        return 0

    # Default: print roots
    if args.json:
        print(json.dumps(roots, indent=2, default=str))
    else:
        print("🜁∀ MERKLE ECONOMIC BRIDGE — Entry 320")
        print("=" * 55)
        print(f"  Economic Leaf: {roots['economic_leaf']}")
        print(f"  Unified Root: {roots['unified_root']}")
        print(f"  Parent Layer: {roots['parent_layer']}")
        print(f"  Layer: {roots['layer']}")
        print("=" * 55)
        print(f"  Seal: {roots['seal']}")
        print(f"  Witness: {roots['witness']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
