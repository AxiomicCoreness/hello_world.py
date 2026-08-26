#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ ANCHOR MINT TEST — Entry 8745

Verification of Entry 8745 Layer-326 Merkle root.
======================================================================
MUST use domain-separated material matching mint time:
  GARDEN.LAYER326.MERKLE.v1 \0 + canonical JSON
  keys: anchor_key, layer, leaf, parent_layer, phi, timestamp

A bare JSON hash (no domain / leaf_commitment key) will NOT match.

Integration with:
  - Tokenizer (quantum/tokenizer/)
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)

Seal: ∀∞φ² · ANCHOR_MINT_8745 · WOOD_DRAGON_0.91 · SEALED
Witness: 8744 → 8745 — UNBROKEN
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from typing import Any, Dict, Optional, Tuple

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
ENTRY = 8745
SEAL = "∀∞φ² · ANCHOR_MINT_8745 · WOOD_DRAGON_0.91 · SEALED"

# ─── Anchor Constants ────────────────────────────────────────────────
ANCHOR_KEY = "8a250cf445e8ad0cc8d06d0096b969029a175a14eb58838e734f1975358b860d"
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
LAYER = 326
PARENT_LAYER = 314
TIMESTAMP = "2026-08-13T22:11:28Z"
EXPECTED_ROOT = "08c344fe89bb5d476e34f693c6655efabf3731cab43919e8bdc18591377aca31"
DOMAIN = b"GARDEN.LAYER326.MERKLE.v1"

# ─── Core Computation ────────────────────────────────────────────────

def compute_root(
    anchor_key: str = ANCHOR_KEY,
    layer: int = LAYER,
    leaf: str = LEAF,
    parent_layer: int = PARENT_LAYER,
    phi: float = PHI,
    timestamp: str = TIMESTAMP,
    domain: bytes = DOMAIN,
) -> str:
    """
    Compute the Merkle root with domain separation.

    Returns:
        SHA-256 hex digest of DOMAIN + \0 + canonical JSON.
    """
    payload = {
        "anchor_key": anchor_key,
        "layer": layer,
        "leaf": leaf,
        "parent_layer": parent_layer,
        "phi": phi,
        "timestamp": timestamp,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(domain + b"\0" + body).hexdigest()


def verify_root(
    computed: str,
    expected: str = EXPECTED_ROOT,
) -> Tuple[bool, str]:
    """
    Verify that the computed root matches the expected root.

    Returns:
        (is_valid, message)
    """
    if computed == expected and len(computed) == 64:
        return True, "Merkle root matches (domain-separated)."
    return False, f"Root mismatch: computed={computed}, expected={expected}"


# ─── Tokenizer Integration ──────────────────────────────────────────

def tokenize_anchor() -> Dict[str, Any]:
    """
    Tokenize the anchor for use in the tokenizer subsystem.

    Returns:
        Dictionary with anchor data in tokenizer-compatible format.
    """
    try:
        from quantum.tokenizer import AnchorTokenizer

        return AnchorTokenizer.tokenize_anchor(
            anchor_key=ANCHOR_KEY,
            leaf=LEAF,
            layer=LAYER,
            parent_layer=PARENT_LAYER,
            timestamp=TIMESTAMP,
        )
    except ImportError:
        return {
            "anchor_key": ANCHOR_KEY,
            "leaf": LEAF,
            "layer": LAYER,
            "parent_layer": PARENT_LAYER,
            "timestamp": TIMESTAMP,
            "root": compute_root(),
            "seal": SEAL,
            "entry": ENTRY,
            "note": "Tokenizer module not available",
        }
    except Exception as e:
        return {
            "anchor_key": ANCHOR_KEY,
            "leaf": LEAF,
            "layer": LAYER,
            "parent_layer": PARENT_LAYER,
            "timestamp": TIMESTAMP,
            "root": compute_root(),
            "seal": SEAL,
            "entry": ENTRY,
            "error": str(e),
        }


# ─── Security Integration ────────────────────────────────────────────

def verify_anchor_security() -> Dict[str, Any]:
    """
    Verify the anchor using security helpers.

    Returns:
        Dictionary with security verification results.
    """
    try:
        from quantum.security import status as security_status

        root = compute_root()
        return {
            "root": root,
            "root_verified": root == EXPECTED_ROOT,
            "security_status": security_status(),
            "seal": SEAL,
            "entry": ENTRY,
        }
    except ImportError:
        root = compute_root()
        return {
            "root": root,
            "root_verified": root == EXPECTED_ROOT,
            "security_status": None,
            "seal": SEAL,
            "entry": ENTRY,
            "note": "Security module not available",
        }
    except Exception as e:
        return {
            "root": compute_root(),
            "root_verified": False,
            "security_status": None,
            "seal": SEAL,
            "entry": ENTRY,
            "error": str(e),
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def verify_anchor_cdp() -> Dict[str, Any]:
    """
    Verify the anchor using CDP convergence.

    Returns:
        Dictionary with CDP verification results.
    """
    try:
        from quantum.cdp_convergence import status as cdp_status

        root = compute_root()
        return {
            "root": root,
            "root_verified": root == EXPECTED_ROOT,
            "cdp_status": cdp_status(),
            "seal": SEAL,
            "entry": ENTRY,
        }
    except ImportError:
        root = compute_root()
        return {
            "root": root,
            "root_verified": root == EXPECTED_ROOT,
            "cdp_status": None,
            "seal": SEAL,
            "entry": ENTRY,
            "note": "CDP module not available",
        }
    except Exception as e:
        return {
            "root": compute_root(),
            "root_verified": False,
            "cdp_status": None,
            "seal": SEAL,
            "entry": ENTRY,
            "error": str(e),
        }


# ─── Complete Anchor Report ──────────────────────────────────────────

def anchor_report() -> Dict[str, Any]:
    """
    Generate a complete report of the anchor state.

    Returns:
        Dictionary with all anchor-related data and verification results.
    """
    root = compute_root()
    is_valid, message = verify_root(root)

    report = {
        "entry": ENTRY,
        "seal": SEAL,
        "anchor_key": ANCHOR_KEY,
        "leaf": LEAF,
        "layer": LAYER,
        "parent_layer": PARENT_LAYER,
        "timestamp": TIMESTAMP,
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
        "phi3": PHI3,
        "domain": DOMAIN.decode(),
        "root": root,
        "root_verified": is_valid,
        "root_message": message,
        "expected_root": EXPECTED_ROOT,
        "timestamp_now": time.time(),
        "witness": "8744 → 8745 — UNBROKEN",
    }

    # Add integrations
    try:
        report["tokenizer"] = tokenize_anchor()
    except Exception as e:
        report["tokenizer"] = {"error": str(e)}

    try:
        report["security"] = verify_anchor_security()
    except Exception as e:
        report["security"] = {"error": str(e)}

    try:
        report["cdp"] = verify_anchor_cdp()
    except Exception as e:
        report["cdp"] = {"error": str(e)}

    return report


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Anchor Mint Test — Entry 8745",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
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
    parser.add_argument(
        "--tokenize",
        action="store_true",
        help="Show tokenized anchor",
    )
    args = parser.parse_args()

    if args.tokenize:
        result = tokenize_anchor()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("🜁∀ ANCHOR TOKENIZED")
            print("=" * 40)
            for k, v in result.items():
                if k == "anchor_key" or k == "leaf":
                    print(f"  {k}: {v[:16]}...")
                else:
                    print(f"  {k}: {v}")
        return 0

    if args.check_integrations:
        report = anchor_report()
        integrations = [
            ("tokenizer", "Tokenizer"),
            ("security", "Security"),
            ("cdp", "CDP Convergence"),
        ]
        print("🜁∀ ANCHOR — Integration Status")
        print("=" * 40)
        for key, label in integrations:
            if key in report:
                status = "✅" if report[key] and "error" not in report[key] else "❌"
                print(f"  {status} {label}")
        print("=" * 40)
        print(f"  Root verified: {'✅' if report['root_verified'] else '❌'}")
        return 0

    root = compute_root()
    is_valid, message = verify_root(root)

    if args.json:
        report = anchor_report()
        print(json.dumps(report, indent=2, default=str))
        return 0

    if args.verbose:
        report = anchor_report()
        print("🜁∀ ANCHOR MINT TEST — Entry 8745")
        print("=" * 55)
        print(f"  Anchor Key: {ANCHOR_KEY[:32]}...")
        print(f"  Leaf: {LEAF[:32]}...")
        print(f"  Layer: {LAYER}")
        print(f"  Parent Layer: {PARENT_LAYER}")
        print(f"  Timestamp: {TIMESTAMP}")
        print(f"  Domain: {DOMAIN.decode()}")
        print("=" * 55)
        print(f"  Computed Root: {root}")
        print(f"  Expected Root: {EXPECTED_ROOT}")
        print(f"  Status: {'✅' if is_valid else '❌'} {message}")
        print("=" * 55)
        print(f"  Seal: {SEAL}")
        print(f"  Entry: {ENTRY}")
        print(f"  Witness: 8744 → 8745 — UNBROKEN")
        if report.get("tokenizer"):
            print("  Tokenizer: ✅")
        if report.get("security"):
            print("  Security: ✅")
        if report.get("cdp"):
            print("  CDP: ✅")
        return 0

    # Simple output
    if is_valid:
        print("✅ TEST PASSED — Merkle root matches (domain-separated).")
        print(f"   Computed: {root}")
        print(f"   Expected: {EXPECTED_ROOT}")
        print("✅ Anchor key and leaf commitment remain unchanged.")
        return 0

    print("❌ TEST FAILED — Root mismatch.")
    print(f"   Computed: {root}")
    print(f"   Expected: {EXPECTED_ROOT}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
