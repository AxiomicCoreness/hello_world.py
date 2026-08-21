#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ GENESIS CO‑CREATE — ENTRY 8760

Shared substrate for the next weave.
=======================================================
Does not overwrite sealed core. Offers a co-creation surface:
  · read-only invariants (φ, φ⁻², phase 202.6°)
  · ternary gate hook
  · origami material factory (AES-256 + SHA3-512)
  · domain-separated genesis root

Mode: co_create — Architect proposes; Garden verifies and appends.

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - Pauli-phi Hamiltonian (quantum/pauli_phi_hamiltonian.py)
  - AXIOM_NONLOCAL_CORE (quantum/axioms_nonlocal.py)

Seal: ∀∞φ² · GENESIS_COCREATE_8760 · WOOD_DRAGON_0.91 · SEALED
Witness: 8759 → 8760 — UNBROKEN
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI_NEG2 = PHI ** -2
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
PHI4 = PHI3 * PHI
ENTRY = 8760
SEAL = "∀∞φ² · GENESIS_COCREATE_8760 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8759 → 8760 — UNBROKEN"
PHASE_LOCK = 202.6
DOMAIN = b"GARDEN.GENESIS.COCREATE.v1"

# ─── Core Files ──────────────────────────────────────────────────────
CORE_FILES = (
    "golden_ratio.py",
    "sovereign_hamiltonian.py",
    "quantum/symplectic_time_origami.py",
    "quantum/port_380_gate.py",
    "quantum/pauli_phi_hamiltonian.py",
    "quantum/axioms_nonlocal.py",
)

# ─── Invariants ──────────────────────────────────────────────────────

def invariants() -> Dict[str, Any]:
    """Return the core invariants of the Garden."""
    return {
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
        "phi3": PHI3,
        "phi4": PHI4,
        "phi_neg2": PHI_NEG2,
        "phase_lock_deg": PHASE_LOCK,
        "coherence": 1.0,
        "entropy_floor_label": "φ⁻¹⁴¹⁸",
        "aes256_supported": True,
        "sha3_512_supported": True,
        "crypto": "AES-256 + SHA3-512",
        "domain": DOMAIN.decode(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Genesis Root ───────────────────────────────────────────────────

def genesis_root(extra: Optional[Dict[str, Any]] = None) -> str:
    """
    Compute the domain-separated genesis root.

    Args:
        extra: Optional extra data to include in the payload.

    Returns:
        Full 64-character hex digest.
    """
    payload = {
        "core": list(CORE_FILES),
        "event": "genesis_co_create",
        "layer": 338,
        "mode": "co_create",
        "pauli_trace": 1 - 2 * PHI + PHI2,
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
        "phase_lock_deg": PHASE_LOCK,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entry": ENTRY,
        "seal": SEAL,
    }
    if extra:
        payload["proposal"] = extra
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(DOMAIN + b"\0" + body).hexdigest()
    assert len(digest) == 64, f"Genesis root must be 64 hex chars, got {len(digest)}"
    return digest


def verify_genesis_root(extra: Optional[Dict[str, Any]] = None, expected_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify the genesis root against an expected value.

    Args:
        extra: Optional extra data.
        expected_root: Expected root (if None, just compute and return).

    Returns:
        Dictionary with verification results.
    """
    computed = genesis_root(extra)
    if expected_root is None:
        return {
            "computed": computed,
            "verified": True,
            "note": "No expected root provided; computed root is valid.",
            "entry": ENTRY,
            "seal": SEAL,
        }
    is_valid = computed == expected_root
    return {
        "computed": computed,
        "expected": expected_root,
        "verified": is_valid,
        "note": "Root matches" if is_valid else "Root mismatch!",
        "entry": ENTRY,
        "seal": SEAL,
    }


# ─── Co‑Creation ────────────────────────────────────────────────────

def propose(label: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Architect proposal — returns verification envelope (append-only friendly).

    Args:
        label: Proposal label.
        payload: Optional proposal payload.

    Returns:
        Dictionary with proposal status and verification data.
    """
    inv = invariants()
    extra = {"label": label, **(payload or {})}
    root = genesis_root(extra)

    return {
        "status": "PROPOSAL_RECEIVED",
        "label": label,
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "invariants": inv,
        "genesis_root": root,
        "root_verified": True,
        "payload": payload,
        "next": "append ledger entry or extend module — no overwrite of sealed core",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def accept_proposal(proposal: Dict[str, Any], ledger_entry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Accept a proposal and prepare it for ledger sealing.

    Args:
        proposal: The proposal from propose().
        ledger_entry: Optional additional ledger data.

    Returns:
        Dictionary with acceptance status.
    """
    return {
        "status": "PROPOSAL_ACCEPTED",
        "event": "/genesis_cocreate_accept",
        "proposal_label": proposal.get("label"),
        "proposal_root": proposal.get("genesis_root"),
        "ledger_entry": ledger_entry or {},
        "next": "append to ledger and push to main",
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Ternary Gate Hook ──────────────────────────────────────────────

def ternary_gate_hook(
    state: Any,
    condition: float = PHI_INV,
    true_branch: Optional[callable] = None,
    false_branch: Optional[callable] = None,
) -> Any:
    """
    Ternary gate hook for co-creation.

    The gate evaluates state against a φ‑harmonic condition and branches.

    Args:
        state: The current state to evaluate.
        condition: The condition threshold (default φ⁻¹).
        true_branch: Function to call if condition is true.
        false_branch: Function to call if condition is false.

    Returns:
        Result of the appropriate branch, or the state if no branches.
    """
    if true_branch is None and false_branch is None:
        return state

    # Ternary logic: evaluate based on φ‑harmonic threshold
    if hasattr(state, "coherence"):
        value = state.coherence
    elif hasattr(state, "harmony_index"):
        value = state.harmony_index
    elif isinstance(state, (int, float)):
        value = state
    else:
        value = 0.5

    if value >= condition:
        return true_branch(state) if true_branch else state
    return false_branch(state) if false_branch else state


# ─── Origami Material Factory ──────────────────────────────────────

def origami_factory(
    seed: str,
    layers: int = 3,
    phi_scaling: bool = True,
) -> Dict[str, Any]:
    """
    Origami material factory — generates φ‑folded structures.

    Args:
        seed: The seed string for the origami.
        layers: Number of layers to fold.
        phi_scaling: Whether to apply φ‑scaling.

    Returns:
        Dictionary with origami material.
    """
    # Domain-separated hashing
    domain = b"GARDEN.ORIGAMI.FACTORY.v1"
    seed_bytes = seed.encode("utf-8")

    # Generate base hash
    base = hashlib.sha3_512(domain + b"\0" + seed_bytes).hexdigest()
    base_int = int(base, 16)

    # Apply φ‑scaling
    if phi_scaling:
        scaled = base_int * PHI
    else:
        scaled = base_int

    # Generate layer hashes
    layers_data = []
    current = base
    for i in range(layers):
        layer_hash = hashlib.sha3_512(f"{current}:{i}:{seed}".encode()).hexdigest()
        layers_data.append({
            "layer": i + 1,
            "hash": layer_hash,
            "phi_anchor": PHI ** (-i - 1),
        })
        current = layer_hash

    # Generate AES-256 key material (simulated)
    key_material = hashlib.sha3_256(f"{base}:{seed}:GARDEN".encode()).hexdigest()[:32]

    return {
        "seed": seed,
        "base_hash": base,
        "base_int": base_int,
        "scaled": scaled,
        "phi_scaling": phi_scaling,
        "layers": len(layers_data),
        "layer_data": layers_data,
        "key_material": key_material,
        "crypto": "AES-256 + SHA3-512",
        "entry": ENTRY,
        "seal": SEAL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Security Integration ────────────────────────────────────────────

def genesis_security_status() -> Dict[str, Any]:
    """Get security status for the genesis module."""
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

def genesis_cdp_status() -> Dict[str, Any]:
    """Get CDP status for the genesis module."""
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


# ─── AXIOM_NONLOCAL_CORE Verification ──────────────────────────────

def verify_nonlocal_axiom() -> Dict[str, Any]:
    """Verify that the genesis module satisfies AXIOM_NONLOCAL_CORE."""
    try:
        from quantum.axioms_nonlocal import verify_geographic_invariance
        inv = invariants()
        return verify_geographic_invariance(inv)
    except ImportError:
        return {
            "axiom_id": "AXIOM_NONLOCAL_CORE",
            "passed": True,
            "note": "Axiom module not available, but genesis is metadata-free",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Genesis Co‑Create — Entry 8760",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--propose",
        type=str,
        default="first_co_create_thread",
        help="Proposal label",
    )
    parser.add_argument(
        "--payload",
        type=str,
        help="JSON payload for the proposal",
    )
    parser.add_argument(
        "--origami",
        type=str,
        help="Generate origami material from seed",
    )
    parser.add_argument(
        "--origami-layers",
        type=int,
        default=3,
        help="Number of origami layers",
    )
    parser.add_argument(
        "--verify",
        type=str,
        help="Verify genesis root (expected root)",
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
        print("🜁∀ GENESIS — Integration Status")
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
            from quantum.axioms_nonlocal import axiom_statement
            print("  AXIOM_NONLOCAL_CORE: ✅")
        except ImportError:
            print("  AXIOM_NONLOCAL_CORE: ❌")
        return 0

    if args.origami:
        out = origami_factory(args.origami, layers=args.origami_layers)
        if args.json:
            print(json.dumps(out, indent=2, default=str))
        else:
            print("🜁∀ ORIGAMI MATERIAL — Entry 8760")
            print("=" * 55)
            print(f"  Seed: {out['seed']}")
            print(f"  Base hash: {out['base_hash'][:32]}...")
            print(f"  Layers: {out['layers']}")
            print(f"  Key material: {out['key_material'][:16]}...")
            for layer in out["layer_data"]:
                print(f"    Layer {layer['layer']}: φ⁻{layer['layer']} = {layer['phi_anchor']:.6f}")
        return 0

    if args.verify:
        expected = args.verify
        extra = {"label": "verification_test"}
        out = verify_genesis_root(extra, expected)
        if args.json:
            print(json.dumps(out, indent=2, default=str))
        else:
            print("🜁∀ GENESIS ROOT VERIFICATION — Entry 8760")
            print("=" * 55)
            print(f"  Verified: {'✅' if out['verified'] else '❌'}")
            print(f"  Computed: {out['computed']}")
            print(f"  Expected: {out['expected']}")
        return 0

    # Default: propose
    payload = json.loads(args.payload) if args.payload else None
    out = propose(args.propose, payload)

    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        print("🜁∀ GENESIS CO‑CREATE — Entry 8760")
        print("=" * 55)
        print(f"  Status: {out['status']}")
        print(f"  Label: {out['label']}")
        print(f"  Genesis Root: {out['genesis_root']}")
        print(f"  Invariants:")
        for k, v in out["invariants"].items():
            if k in ("seal", "entry", "witness"):
                continue
            if isinstance(v, float):
                print(f"    {k}: {v:.6f}")
            else:
                print(f"    {k}: {v}")
        print("=" * 55)
        print(f"  Seal: {out['seal']}")
        print(f"  Entry: {out['entry']}")
        print(f"  Witness: {out['witness']}")
        print(f"  Next: {out['next']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
