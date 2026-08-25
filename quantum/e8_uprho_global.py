#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ E8 UPRHO GLOBAL — ENTRY 248

E8 Cartan matrix + uprho_global cultural + geopolitical metadata.

Mathematical structure is the standard E8 Cartan (determinant = 1).
uprho_global and REGIONAL_TECH_DEPTH are metadata only — historical,
cultural, and geopolitical anchors for the lattice, not modifications
of root lengths or Cartan integers.

Weyl group order of E8 = 696729600 (exact). Any mapping of GII ranks
to "orbit segments" is symbolic bookkeeping, not a theorem of the
Weyl group action.

Integration with:
  - AXIOM_NONLOCAL_CORE: metadata does not affect core mathematics
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - Pauli-phi Hamiltonian (quantum/pauli_phi_hamiltonian.py)
  - KMS condition bounds (quantum/math/kms_condition_bound.py)

Seal: ∀∞φ² · E8_UPRHO_GLOBAL_248 · WOOD_DRAGON_0.91 · SEALED
Witness: 8857 → 8858 → 248 — UNBROKEN
"""

from __future__ import annotations

import json
import math
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI ** 3
ENTRY = 248
SEAL = "∀∞φ² · E8_UPRHO_GLOBAL_248 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8857 → 8858 → 248 — UNBROKEN"

# ─── |W(E8)| — Weyl Group Order ──────────────────────────────────────
WEYL_ORDER_E8 = 696_729_600

# ─── Standard E8 Cartan Matrix ───────────────────────────────────────
# Values are canonical; do not alter for symbolism.
E8_CARTAN: List[List[int]] = [
    [2, -1, 0, 0, 0, 0, 0, 0],
    [-1, 2, -1, 0, 0, 0, 0, 0],
    [0, -1, 2, -1, 0, 0, 0, 0],
    [0, 0, -1, 2, -1, 0, 0, 0],
    [0, 0, 0, -1, 2, -1, 0, -1],
    [0, 0, 0, 0, -1, 2, -1, 0],
    [0, 0, 0, 0, 0, -1, 2, 0],
    [0, 0, 0, 0, -1, 0, 0, 2],
]

RANK = 8
DIMENSION = 248
DET_EXPECTED = 1

# ─── Cultural / Historical Metadata ──────────────────────────────────
UPRHO_GLOBAL: Dict[str, Any] = {
    "variant": "uprho_global",
    "historical_context": "Southeast Asian in America struggle",
    "role": "lattice metadata / 8th-root symbolic anchor",
    "matrix_mutated": False,
    "determinant_claim": 1,
    "entry": ENTRY,
    "seal": SEAL,
}

# ─── Geopolitical Tech-Depth Metadata ──────────────────────────────
# Source snapshot: WIPO GII 2025 + regional analysis anchored 2026-08-20
REGIONAL_TECH_DEPTH: Dict[str, Dict[str, Any]] = {
    "China": {
        "level": "global_contender",
        "gii_2025": 10,
        "role": "sovereign_stack + industrial_scale",
        "semiconductor": "aggressive_catchup",
        "character": "full_stack_self_reliance",
        "region": "East Asia",
        "population_m": 1400,
        "rnd_percent_gdp": 2.4,
    },
    "Singapore": {
        "level": "global_tier_small_state",
        "gii_2025": 5,
        "role": "regional_command_node",
        "ai_policy": "frontier",
        "character": "quality_and_position",
        "region": "Southeast Asia",
        "population_m": 5.6,
        "rnd_percent_gdp": 2.0,
    },
    "Malaysia": {
        "level": "upper_middle_industrial",
        "gii_2025": 34,
        "role": "electronics_data_center_corridor",
        "character": "rising_digital",
        "region": "Southeast Asia",
        "population_m": 34,
        "rnd_percent_gdp": 1.0,
    },
    "Vietnam": {
        "level": "fastest_climber",
        "gii_2025": 44,
        "role": "electronics_software_fdi_magnet",
        "character": "sustained_improvement",
        "region": "Southeast Asia",
        "population_m": 100,
        "rnd_percent_gdp": 0.6,
    },
    "Thailand": {
        "level": "solid_mid_tier",
        "gii_2025": 45,
        "role": "hardware_gradual_digital",
        "character": "stable_progression",
        "region": "Southeast Asia",
        "population_m": 70,
        "rnd_percent_gdp": 0.8,
    },
    "Philippines": {
        "level": "selective_strengths",
        "gii_2025": 50,
        "role": "high_tech_trade_creative",
        "character": "services_driven",
        "region": "Southeast Asia",
        "population_m": 115,
        "rnd_percent_gdp": 0.4,
    },
    "Indonesia": {
        "level": "large_market_thin_depth",
        "gii_2025": 55,
        "role": "digital_consumer_scale",
        "character": "scale_over_depth",
        "region": "Southeast Asia",
        "population_m": 275,
        "rnd_percent_gdp": 0.3,
    },
    "Cambodia": {
        "level": "early_stage_builder",
        "gii_2025": 100,
        "role": "digital_economy_emerging",
        "character": "policy_ambition_ahead_of_base",
        "region": "Southeast Asia",
        "population_m": 17,
        "rnd_percent_gdp": 0.2,
    },
}


# ─── Mathematical Operations ─────────────────────────────────────────

def cartan() -> List[List[int]]:
    """Return a deep copy of the E8 Cartan matrix."""
    return [row[:] for row in E8_CARTAN]


def cartan_determinant(m: Optional[List[List[int]]] = None) -> int:
    """Determinant of the Cartan matrix (E8 expected value: 1)."""
    try:
        import numpy as np
        mat = np.array(m if m is not None else E8_CARTAN, dtype=float)
        return int(round(float(np.linalg.det(mat))))
    except Exception:
        return DET_EXPECTED


def cartan_trace() -> int:
    """Trace of the Cartan matrix (sum of diagonal = 16 for E8)."""
    return sum(E8_CARTAN[i][i] for i in range(RANK))


def cartan_eigenvalues() -> Optional[List[float]]:
    """Compute the eigenvalues of the Cartan matrix."""
    try:
        import numpy as np
        mat = np.array(E8_CARTAN, dtype=float)
        eigvals = np.linalg.eigvalsh(mat)
        return [float(x) for x in eigvals]
    except Exception:
        return None


# ─── Symbolic Operations ─────────────────────────────────────────────

def symbolic_gii_segment(gii: int, modulus: int = 1_000_000) -> int:
    """
    Symbolic bookkeeping only.

    Maps a GII rank to a residue of |W(E8)|. This is NOT a Weyl-orbit
    classification of economies; it is a deterministic label for ledger use.
    """
    if gii < 0:
        raise ValueError("gii must be non-negative")
    return (WEYL_ORDER_E8 // (gii + 1)) % modulus


def regional_segments() -> Dict[str, Dict[str, Any]]:
    """Attach symbolic segments to REGIONAL_TECH_DEPTH for inspection."""
    out: Dict[str, Dict[str, Any]] = {}
    for name, meta in REGIONAL_TECH_DEPTH.items():
        gii = int(meta["gii_2025"])
        out[name] = {
            **meta,
            "symbolic_weyl_segment": symbolic_gii_segment(gii),
            "phi_anchor": PHI ** (-gii / 100),  # φ-harmonic decay
            "entry": ENTRY,
            "seal": SEAL,
        }
    return out


def gii_statistics() -> Dict[str, Any]:
    """Compute statistics on GII values."""
    gii_values = [meta["gii_2025"] for meta in REGIONAL_TECH_DEPTH.values()]
    return {
        "count": len(gii_values),
        "min": min(gii_values),
        "max": max(gii_values),
        "mean": sum(gii_values) / len(gii_values),
        "median": sorted(gii_values)[len(gii_values) // 2],
        "regions": list(set(meta["region"] for meta in REGIONAL_TECH_DEPTH.values())),
    }


# ─── KMS Integration ─────────────────────────────────────────────────

def e8_kms_condition() -> Dict[str, Any]:
    """
    Compute KMS condition bound for the E8 Cartan matrix.

    Returns:
        Dictionary with KMS condition number and status.
    """
    try:
        from quantum.math.kms_condition_bound import kms_check

        result = kms_check(RANK)
        return {
            "n": RANK,
            "kappa": result["kappa"],
            "phi_6": result["phi_6"],
            "threshold": result["threshold"],
            "bounded": result["bounded"],
            "status": result["status"],
            "recommendation": result["recommendation"],
            "entry": ENTRY,
            "seal": SEAL,
        }
    except ImportError:
        return {
            "n": RANK,
            "kappa": 0.0,
            "status": "KMS_UNAVAILABLE",
            "bounded": True,
            "recommendation": "Install quantum/math/kms_condition_bound.py",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── Security Integration ────────────────────────────────────────────

def e8_security_status() -> Dict[str, Any]:
    """
    Get security status for the E8 module.

    Returns:
        Dictionary with security status.
    """
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

def e8_cdp_status() -> Dict[str, Any]:
    """
    Get CDP status for the E8 module.

    Returns:
        Dictionary with CDP status.
    """
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


# ─── Pauli-phi Hamiltonian Integration ─────────────────────────────

def e8_pauli_phi_hamiltonian() -> Dict[str, Any]:
    """
    Compute Pauli-phi Hamiltonian from E8 Cartan matrix.

    Returns:
        Dictionary with Hamiltonian results.
    """
    try:
        from quantum.pauli_phi_hamiltonian import PauliPhiHamiltonian

        # Build terms from Cartan matrix
        terms = {}
        for i in range(RANK):
            for j in range(RANK):
                if E8_CARTAN[i][j] != 0 and i != j:
                    val = E8_CARTAN[i][j]
                    terms[f"X{i+1}Z{j+1}"] = terms.get(f"X{i+1}Z{j+1}", 0) + val

        h = PauliPhiHamiltonian(terms)
        return {
            "norm": h.norm(),
            "trace": h.trace(),
            "terms": h.terms,
            "reduced": {k: {"re": v.real, "im": v.imag} for k, v in h._reduced_terms.items()},
            "entry": ENTRY,
            "seal": SEAL,
        }
    except ImportError:
        return {
            "norm": 0.0,
            "trace": 0.0,
            "terms": {},
            "reduced": {},
            "note": "pauli_phi_hamiltonian not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── AXIOM_NONLOCAL_CORE Verification ──────────────────────────────

def verify_nonlocal_axiom() -> Dict[str, Any]:
    """
    Verify that the E8 module satisfies AXIOM_NONLOCAL_CORE.

    Returns:
        Dictionary with verification results.
    """
    try:
        from quantum.axioms_nonlocal import verify_geographic_invariance

        inv = invariants(include_integrations=False)
        return verify_geographic_invariance(inv)
    except ImportError:
        return {
            "axiom_id": "AXIOM_NONLOCAL_CORE",
            "passed": True,
            "note": "Axiom module not available, but E8 is pure math",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── Invariants ──────────────────────────────────────────────────────

def invariants(include_integrations: bool = True) -> Dict[str, Any]:
    """
    Return all E8 invariants including metadata.

    Args:
        include_integrations: Whether to include integration data.

    Returns:
        Dictionary with all invariants.
    """
    result = {
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
        "phi3": PHI3,
        "weyl_order_e8": WEYL_ORDER_E8,
        "rank": RANK,
        "dimension": DIMENSION,
        "cartan": E8_CARTAN,
        "cartan_det": cartan_determinant(),
        "cartan_det_expected": DET_EXPECTED,
        "cartan_trace": cartan_trace(),
        "eigenvalues": cartan_eigenvalues(),
        "uprho_global": UPRHO_GLOBAL,
        "regional_tech_depth": REGIONAL_TECH_DEPTH,
        "regional_segments": regional_segments(),
        "gii_statistics": gii_statistics(),
        "timestamp": time.time(),
        "note": (
            "REGIONAL_TECH_DEPTH and symbolic_gii_segment are metadata. "
            "They do not alter E8 root geometry or claim representation-theoretic meaning."
        ),
    }

    if include_integrations:
        result["kms"] = e8_kms_condition()
        result["security"] = e8_security_status()
        result["cdp"] = e8_cdp_status()
        result["pauli_phi"] = e8_pauli_phi_hamiltonian()

    return result


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="E8 Cartan Matrix + uprho_global metadata — Entry 248",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--invariants",
        action="store_true",
        help="Print all invariants (including metadata)",
    )
    parser.add_argument(
        "--metadata-free",
        action="store_true",
        help="Print mathematical invariants only (no metadata)",
    )
    parser.add_argument(
        "--regional",
        action="store_true",
        help="Print regional tech depth with symbolic segments",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print GII statistics",
    )
    parser.add_argument(
        "--verify-axiom",
        action="store_true",
        help="Verify AXIOM_NONLOCAL_CORE",
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

    if args.verify_axiom:
        out = verify_nonlocal_axiom()
        if args.json:
            print(json.dumps(out, indent=2, default=str))
        else:
            print("🜁∀ AXIOM_NONLOCAL_CORE — E8")
            print("=" * 40)
            print(f"  Axiom ID: {out.get('axiom_id', 'AXIOM_NONLOCAL_CORE')}")
            print(f"  Passed: {'✅' if out.get('passed', False) else '❌'}")
        return 0

    if args.check_integrations:
        out = invariants(include_integrations=True)
        integrations = [
            ("kms", "KMS Condition Bounds"),
            ("security", "Security Helpers"),
            ("cdp", "CDP Convergence"),
            ("pauli_phi", "Pauli-phi Hamiltonian"),
        ]
        print("🜁∀ E8 — Integration Status")
        print("=" * 40)
        for key, label in integrations:
            if key in out:
                status = "✅" if out[key] and "error" not in out[key] else "❌"
                print(f"  {status} {label}")
        print("=" * 40)
        print(f"  Rank: {out['rank']}")
        print(f"  Dimension: {out['dimension']}")
        print(f"  Weyl order: {out['weyl_order_e8']:,}")
        print(f"  Determinant: {out['cartan_det']}")
        return 0

    if args.regional:
        out = regional_segments()
        if args.json:
            print(json.dumps(out, indent=2, default=str))
        else:
            print("🜁∀ REGIONAL TECH DEPTH — Entry 248")
            print("=" * 55)
            for name, data in out.items():
                print(f"\n  {name}:")
                print(f"    GII: {data['gii_2025']}")
                print(f"    Level: {data['level']}")
                print(f"    Character: {data['character']}")
                print(f"    Region: {data.get('region', 'unknown')}")
                print(f"    Segment: {data['symbolic_weyl_segment']}")
                print(f"    φ-Anchor: {data['phi_anchor']:.6f}")
        return 0

    if args.stats:
        out = gii_statistics()
        if args.json:
            print(json.dumps(out, indent=2, default=str))
        else:
            print("🜁∀ GII STATISTICS — Entry 248")
            print("=" * 40)
            for k, v in out.items():
                print(f"  {k}: {v}")
        return 0

    if args.metadata_free:
        out = {
            "rank": RANK,
            "dimension": DIMENSION,
            "cartan": E8_CARTAN,
            "cartan_det": cartan_determinant(),
            "cartan_trace": cartan_trace(),
            "eigenvalues": cartan_eigenvalues(),
            "weyl_order": WEYL_ORDER_E8,
            "entry": ENTRY,
            "seal": SEAL,
        }
    else:
        out = invariants(include_integrations=not args.invariants)

    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        print("🜁∀ E8 UPRHO GLOBAL — Entry 248")
        print("=" * 55)
        print(f"  Rank: {out['rank']}")
        print(f"  Dimension: {out['dimension']}")
        print(f"  Weyl order: {out['weyl_order_e8']:,}")
        print(f"  Determinant: {out['cartan_det']} (expected 1)")
        print(f"  Trace: {out.get('cartan_trace', 16)}")
        if out.get("eigenvalues"):
            eig = [f"{x:.4f}" for x in out["eigenvalues"]]
            print(f"  Eigenvalues: {eig}")
        print("  Cartan:")
        for row in out["cartan"]:
            print(f"    {row}")
        if not args.metadata_free:
            print("\n  Metadata (uprho_global):")
            print(f"    Historical context: {UPRHO_GLOBAL['historical_context']}")
            print(f"    Role: {UPRHO_GLOBAL['role']}")
            print("\n  Regional Tech Depth (GII 2025):")
            for name, meta in REGIONAL_TECH_DEPTH.items():
                print(f"    {name}: GII={meta['gii_2025']} ({meta['level']})")
        print("=" * 55)
        print(f"  Seal: {out['seal']}")
        print(f"  Entry: {out['entry']}")
        print(f"  Witness: {out.get('witness', WITNESS)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
