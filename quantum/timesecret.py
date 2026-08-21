#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ TIMESECRET — ENTRY 8753

Temporal nonce locked to domain-separated Merkle layer.

Timesecret generates a temporal nonce that is locked to a specific
domain-separated Merkle layer, providing a verifiable time-bound
commitment.

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - Merkle Economic Bridge (quantum/merkle_economic_bridge.py)
  - Digest Policy (quantum/digest_policy.py)

Seal: ∀∞φ² · TIMESECRET_8753 · WOOD_DRAGON_0.91 · SEALED
Witness: 8752 → 8753 — UNBROKEN
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
ENTRY = 8753
SEAL = "∀∞φ² · TIMESECRET_8753 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8752 → 8753 — UNBROKEN"

DOMAIN = b"GARDEN.TIMESECRET.v1"
DEFAULT_LAYER = 329
DEFAULT_PARENT_ROOT = "c5c7646295eec7c88fb00aa6a3f384afdc04c679e6abb31954c8d0cd54fba3dc"


# ─── Core Functions ──────────────────────────────────────────────────

def mint_timesecret(
    parent_root: str,
    layer: int = DEFAULT_LAYER,
    timestamp: Optional[str] = None,
    include_phi: bool = True,
) -> Dict[str, Any]:
    """
    Mint a timesecret nonce locked to a domain-separated Merkle layer.

    Args:
        parent_root: Parent Merkle root (64 hex chars).
        layer: Layer number.
        timestamp: ISO timestamp (default: current UTC time).
        include_phi: Whether to include phi in the payload.

    Returns:
        Dictionary with nonce, timestamp, layer, and parent_root.

    Raises:
        ValueError: If parent_root is not a valid SHA-256 hex digest.
    """
    # Validate parent root
    if len(parent_root) != 64:
        raise ValueError(f"parent_root must be 64 hex chars, got {len(parent_root)}")
    if any(c not in "0123456789abcdef" for c in parent_root.lower()):
        raise ValueError("parent_root must be hex")

    # Generate timestamp
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build payload
    payload: Dict[str, Any] = {
        "layer": layer,
        "parent_root": parent_root,
        "timestamp": timestamp,
        "entry": ENTRY,
        "seal": SEAL,
    }
    if include_phi:
        payload["phi"] = PHI

    # Canonical JSON
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    # Generate nonce
    nonce = hashlib.sha256(DOMAIN + b"\0" + body).hexdigest()
    assert len(nonce) == 64, f"Nonce must be 64 hex chars, got {len(nonce)}"

    return {
        "nonce": nonce,
        "nonce_len": len(nonce),
        "timestamp": timestamp,
        "layer": layer,
        "parent_root": parent_root,
        "phi": PHI if include_phi else None,
        "domain": DOMAIN.decode(),
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
    }


def verify_timesecret(
    nonce: str,
    parent_root: str,
    layer: int = DEFAULT_LAYER,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify a timesecret nonce against its parent root and layer.

    Args:
        nonce: The nonce to verify (64 hex chars).
        parent_root: Expected parent root (64 hex chars).
        layer: Expected layer number.
        timestamp: Expected timestamp (optional).

    Returns:
        Dictionary with verification results.
    """
    # Validate inputs
    if len(nonce) != 64:
        raise ValueError(f"nonce must be 64 hex chars, got {len(nonce)}")
    if len(parent_root) != 64:
        raise ValueError(f"parent_root must be 64 hex chars, got {len(parent_root)}")

    # Recompute nonce
    if timestamp is None:
        # Try to extract timestamp from nonce? Not possible directly.
        # We need the original timestamp to verify.
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    recomputed = mint_timesecret(
        parent_root=parent_root,
        layer=layer,
        timestamp=timestamp,
    )

    matches = recomputed["nonce"] == nonce

    return {
        "verified": matches,
        "provided_nonce": nonce,
        "computed_nonce": recomputed["nonce"],
        "parent_root": parent_root,
        "layer": layer,
        "timestamp": timestamp,
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
    }


def timesecret_chain(
    start_root: str,
    start_layer: int,
    count: int = 5,
) -> Dict[str, Any]:
    """
    Generate a chain of timesecrets.

    Args:
        start_root: Starting Merkle root.
        start_layer: Starting layer.
        count: Number of timesecrets to generate.

    Returns:
        Dictionary with chain of timesecrets.
    """
    chain = []
    current_root = start_root
    current_layer = start_layer

    for i in range(count):
        ts = mint_timesecret(
            parent_root=current_root,
            layer=current_layer + i,
        )
        chain.append(ts)
        # Use the nonce as the next parent root
        current_root = ts["nonce"]

    return {
        "chain": chain,
        "count": count,
        "start_root": start_root,
        "start_layer": start_layer,
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
    }


# ─── Security Integration ────────────────────────────────────────────

def timesecret_security_status() -> Dict[str, Any]:
    """Get security status for timesecret."""
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

def timesecret_cdp_status() -> Dict[str, Any]:
    """Get CDP status for timesecret."""
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


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Timesecret — Entry 8753",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--mint",
        action="store_true",
        help="Mint a timesecret",
    )
    parser.add_argument(
        "--parent",
        type=str,
        default=DEFAULT_PARENT_ROOT,
        help="Parent Merkle root",
    )
    parser.add_argument(
        "--layer",
        type=int,
        default=DEFAULT_LAYER,
        help="Layer number",
    )
    parser.add_argument(
        "--verify",
        type=str,
        help="Verify a nonce",
    )
    parser.add_argument(
        "--chain",
        type=int,
        default=0,
        help="Generate a chain of N timesecrets",
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
        print("🜁∀ TIMESECRET — Integration Status")
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
        try:
            from quantum.digest_policy import assert_full_sha256_hex
            print("  Digest Policy: ✅")
        except ImportError:
            print("  Digest Policy: ❌")
        return 0

    if args.chain > 0:
        result = timesecret_chain(
            start_root=args.parent,
            start_layer=args.layer,
            count=args.chain,
        )
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("🜁∀ TIMESECRET CHAIN — Entry 8753")
            print("=" * 55)
            print(f"  Count: {result['count']}")
            print(f"  Start Root: {result['start_root'][:32]}...")
            print(f"  Start Layer: {result['start_layer']}")
            for i, ts in enumerate(result['chain']):
                print(f"    [{i}] Layer {ts['layer']}: {ts['nonce'][:32]}...")
            print(f"  Seal: {result['seal']}")
        return 0

    if args.verify:
        result = verify_timesecret(
            nonce=args.verify,
            parent_root=args.parent,
            layer=args.layer,
        )
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("🜁∀ TIMESECRET VERIFICATION — Entry 8753")
            print("=" * 55)
            print(f"  Verified: {'✅' if result['verified'] else '❌'}")
            print(f"  Provided Nonce: {result['provided_nonce']}")
            print(f"  Computed Nonce: {result['computed_nonce']}")
            print(f"  Parent Root: {result['parent_root'][:32]}...")
            print(f"  Layer: {result['layer']}")
            print("=" * 55)
            print(f"  Seal: {result['seal']}")
        return 0

    if args.mint:
        result = mint_timesecret(
            parent_root=args.parent,
            layer=args.layer,
        )
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("🜁∀ TIMESECRET MINT — Entry 8753")
            print("=" * 55)
            print(f"  Nonce: {result['nonce']}")
            print(f"  Timestamp: {result['timestamp']}")
            print(f"  Layer: {result['layer']}")
            print(f"  Parent Root: {result['parent_root'][:32]}...")
            print("=" * 55)
            print(f"  Seal: {result['seal']}")
            print(f"  Entry: {result['entry']}")
            print(f"  Witness: {result['witness']}")
        return 0

    # Default: show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
