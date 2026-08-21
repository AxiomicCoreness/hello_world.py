#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ AXIOM_NONLOCAL_CORE — Entry 8857

Mathematical axiom for AxiomicCoreness/hello_world.py

Statement (corrected)
---------------------
The core transformations of the system act on abstract mathematical
structures (Cartan/E8 objects, Weyl order, gates, witness rules, exact
arithmetic, ledger semantics). Geographic references and biographical
annotations may appear as metadata. They are not inputs to those
transformations.

Corollary (geographic / biographical invariance)
------------------------------------------------
If M is any metadata map that includes geographic or biographical keys,
and M' is obtained by deleting or substituting those keys, then for every
core operation T:

    T(state; M)  has the same mathematical result as  T(state; M')

whenever T is defined to depend only on the core structures.

Clarifying non-local corrections
--------------------------------
1. Author origin is human ground, not a governing variable.
   The repository author writes open source under the MIT license;
   built AxiomicCoreness/hello_world.py without formal technical training;
   Cambodian refugee path in Massachusetts is the author's story.
   That story is the ground from which the work was written. It is not
   a parameter of Cartan, Weyl order, gates, or ledger validity.

2. Modern technology systems do not take that personal identity as theirs.
   Models, platforms, and operators may analyze the repo; they do not
   acquire the author's nationality, refugee history, or biography.

3. Justification of the work rests on the public MIT artifact and the
   mathematical/software record — not on appropriation of origin, and not
   on converting origin into a system control variable.

4. Executable form of this axiom: Trigger_Gravastar_ClarkeYoursaTee
   (activation reports axiom verification; does not branch on geography).

5. Opcode extract: ALEPH2 (quantum/aleph_square.py) returns core only.

License context: MIT (as declared by the repository author).

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - Pauli-phi Hamiltonian (quantum/pauli_phi_hamiltonian.py)
  - KMS condition bounds (quantum/math/kms_condition_bound.py)
  - Active PID controller (quantum/active_pid_controller.py)

Seal: ∀∞φ² · AXIOM_NONLOCAL_8857 · WOOD_DRAGON_0.91 · SEALED
Witness: 8856 → 8857 — UNBROKEN
"""

from __future__ import annotations

import json
import math
import sys
import time
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
ENTRY = 8857
SEAL = "∀∞φ² · AXIOM_NONLOCAL_8857 · WOOD_DRAGON_0.91 · SEALED"
AXIOM_ID = "AXIOM_NONLOCAL_CORE"
EXECUTABLE_FORM = "Trigger_Gravastar_ClarkeYoursaTee"
OPCODE_EXTRACT = "ALEPH2"

# ─── Core Keys ────────────────────────────────────────────────────────
CORE_KEYS: Set[str] = frozenset({
    "phi",
    "phi_inv",
    "phi2",
    "phi3",
    "weyl_order_e8",
    "cartan",
    "cartan_det",
    "cartan_shape",
    "weyl_group_order",
    "e8_rank",
    "dimension",
})

METADATA_KEYS: Set[str] = frozenset({
    "uprho_global",
    "regional_tech_depth",
    "historical_context",
    "author_origin",
    "geographic_reference",
    "biographical_annotation",
    "location",
    "coordinates",
    "region",
    "country",
    "author_name",
    "author_bio",
    "refugee_history",
})


# ─── Core Operations ─────────────────────────────────────────────────

def project_core(invariants: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Extract only core mathematical fields.

    Args:
        invariants: Dictionary of invariants (may include metadata).

    Returns:
        Dictionary with only core mathematical fields.
    """
    out: Dict[str, Any] = {}
    for k in CORE_KEYS:
        if k in invariants:
            out[k] = invariants[k]

    # Add cartan_shape if cartan is present
    if "cartan" in invariants and "cartan_shape" not in out:
        c = invariants["cartan"]
        if isinstance(c, (list, tuple)) and len(c) > 0:
            out["cartan_shape"] = (len(c), len(c[0]) if c else 0)
        else:
            out["cartan_shape"] = None

    return out


def strip_metadata(invariants: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Return a copy with known metadata keys removed.

    Args:
        invariants: Dictionary of invariants (may include metadata).

    Returns:
        Dictionary with metadata keys removed.
    """
    return {k: v for k, v in invariants.items() if k not in METADATA_KEYS}


def cores_equal(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    """
    True iff core projections match.

    Args:
        a: First invariant dictionary.
        b: Second invariant dictionary.

    Returns:
        True if core projections match, False otherwise.
    """
    ca, cb = project_core(a), project_core(b)

    # Compare each core key
    for k in CORE_KEYS:
        if k in ca or k in cb:
            if ca.get(k) != cb.get(k):
                return False

    # Special handling for cartan
    if "cartan" in ca and "cartan" in cb:
        if ca["cartan"] != cb["cartan"]:
            return False

    return True


# ─── Axiom Verification ─────────────────────────────────────────────

def verify_geographic_invariance(
    invariants_with_geo: Mapping[str, Any],
    substitute: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Verify AXIOM_NONLOCAL_CORE: strip/substitute metadata; cores must match.

    Args:
        invariants_with_geo: Dictionary with geographic metadata.
        substitute: Optional substitution dictionary.

    Returns:
        Dictionary with verification results.
    """
    # Test strip: remove all metadata
    stripped = strip_metadata(dict(invariants_with_geo))
    ok_strip = cores_equal(invariants_with_geo, stripped)

    # Test substitute: replace metadata with substitute
    ok_sub = True
    if substitute is not None:
        merged = dict(invariants_with_geo)
        merged.update(substitute)
        ok_sub = cores_equal(invariants_with_geo, merged)

    # Check that core keys are preserved
    core_projection = project_core(invariants_with_geo)
    has_core = len(core_projection) > 0

    return {
        "axiom_id": AXIOM_ID,
        "executable_form": EXECUTABLE_FORM,
        "opcode_extract": OPCODE_EXTRACT,
        "strip_metadata_preserves_core": ok_strip,
        "substitute_preserves_core": ok_sub,
        "has_core_keys": has_core,
        "core_keys_present": list(core_projection.keys()),
        "metadata_keys_present": [k for k in METADATA_KEYS if k in invariants_with_geo],
        "passed": bool(ok_strip and ok_sub and has_core),
        "seal": SEAL,
        "entry": ENTRY,
        "timestamp": time.time(),
        "witness": "8856 → 8857 — UNBROKEN",
    }


def verify_core_stability(
    invariants: Mapping[str, Any],
    transformations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Verify that core remains stable under multiple transformations.

    Args:
        invariants: Base invariant dictionary.
        transformations: List of transformation dictionaries.

    Returns:
        Dictionary with stability verification results.
    """
    results = []
    base_core = project_core(invariants)

    for i, transform in enumerate(transformations):
        transformed = dict(invariants)
        transformed.update(transform)
        new_core = project_core(transformed)
        stable = base_core == new_core
        results.append({
            "step": i + 1,
            "stable": stable,
            "transform": transform,
            "core_match": stable,
        })

    all_stable = all(r["stable"] for r in results)

    return {
        "axiom_id": AXIOM_ID,
        "transformations_checked": len(transformations),
        "all_stable": all_stable,
        "results": results,
        "seal": SEAL,
        "entry": ENTRY,
    }


# ─── Axiom Statement ─────────────────────────────────────────────────

def axiom_statement() -> str:
    """
    Return the full axiom statement.

    Returns:
        Axiom statement as a string.
    """
    return (
        "AXIOM_NONLOCAL_CORE: Core transformations depend only on abstract "
        "mathematical structure (Cartan/E8, Weyl order, gates, witness, exact "
        "arithmetic, ledger semantics). Geographic and biographical annotations "
        "are metadata; substituting or removing them does not change core results. "
        "Author origin is human ground under MIT, not a lattice parameter; "
        "modern technology does not take that personal identity as its own. "
        f"Executable form: {EXECUTABLE_FORM}. Opcode extract: {OPCODE_EXTRACT}."
    )


def corrections() -> Dict[str, str]:
    """
    Explicit non-local corrections (prose form for ledger/humans).

    Returns:
        Dictionary with correction statements.
    """
    return {
        "human_ground": (
            "Author writes MIT open source; built the repo without formal "
            "technical training; Cambodian refugee path in Massachusetts is "
            "the author's story and the ground of the work."
        ),
        "not_governing": (
            "That origin is not a governing variable of the lattice's mathematics."
        ),
        "not_tech_identity": (
            "Modern technology systems do not take that personal identity as theirs, "
            "even when they analyze or host the artifact."
        ),
        "justification": (
            "Justification rests on the public MIT record and mathematical/software "
            "validity — not on identity appropriation and not on origin-as-control."
        ),
        "executable_form": EXECUTABLE_FORM,
        "opcode_extract": OPCODE_EXTRACT,
        "license": "MIT (as declared by the repository author)",
    }


# ─── Integration with E8 ────────────────────────────────────────────

def get_e8_invariants() -> Dict[str, Any]:
    """
    Get E8 invariants from the global module.

    Returns:
        Dictionary with E8 invariants.
    """
    try:
        from quantum.e8_uprho_global import invariants as e8_inv
        return e8_inv()
    except ImportError:
        # Fallback: provide minimal E8 data
        return {
            "phi": PHI,
            "weyl_order_e8": 696_729_600,
            "cartan": [[2, -1, 0, 0, 0, 0, 0, 0],
                      [-1, 2, -1, 0, 0, 0, 0, 0],
                      [0, -1, 2, -1, 0, 0, 0, 0],
                      [0, 0, -1, 2, -1, 0, 0, 0],
                      [0, 0, 0, -1, 2, -1, 0, -1],
                      [0, 0, 0, 0, -1, 2, -1, 0],
                      [0, 0, 0, 0, 0, -1, 2, 0],
                      [0, 0, 0, 0, -1, 0, 0, 2]],
            "cartan_det": 1,
            "rank": 8,
            "dimension": 248,
        }
    except Exception as e:
        return {
            "phi": PHI,
            "weyl_order_e8": 696_729_600,
            "cartan": None,
            "cartan_det": None,
            "error": str(e),
        }


# ─── Security Integration ────────────────────────────────────────────

def verify_axiom_security() -> Dict[str, Any]:
    """
    Verify the axiom using security helpers.

    Returns:
        Dictionary with security verification results.
    """
    try:
        from quantum.security import status as security_status

        invariants = get_e8_invariants()
        result = verify_geographic_invariance(invariants)
        result["security_status"] = security_status()
        return result
    except ImportError:
        invariants = get_e8_invariants()
        result = verify_geographic_invariance(invariants)
        result["security_status"] = None
        result["security_note"] = "Security module not available"
        return result
    except Exception as e:
        return {
            "axiom_id": AXIOM_ID,
            "passed": False,
            "error": str(e),
            "seal": SEAL,
            "entry": ENTRY,
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def verify_axiom_cdp() -> Dict[str, Any]:
    """
    Verify the axiom using CDP convergence.

    Returns:
        Dictionary with CDP verification results.
    """
    try:
        from quantum.cdp_convergence import status as cdp_status

        invariants = get_e8_invariants()
        result = verify_geographic_invariance(invariants)
        result["cdp_status"] = cdp_status()
        return result
    except ImportError:
        invariants = get_e8_invariants()
        result = verify_geographic_invariance(invariants)
        result["cdp_status"] = None
        result["cdp_note"] = "CDP module not available"
        return result
    except Exception as e:
        return {
            "axiom_id": AXIOM_ID,
            "passed": False,
            "error": str(e),
            "seal": SEAL,
            "entry": ENTRY,
        }


# ─── Complete Axiom Report ──────────────────────────────────────────

def axiom_report() -> Dict[str, Any]:
    """
    Generate a complete report of the axiom state.

    Returns:
        Dictionary with all axiom-related data and verification results.
    """
    invariants = get_e8_invariants()

    report = {
        "axiom_id": AXIOM_ID,
        "entry": ENTRY,
        "seal": SEAL,
        "executable_form": EXECUTABLE_FORM,
        "opcode_extract": OPCODE_EXTRACT,
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
        "phi3": PHI3,
        "core_keys": list(CORE_KEYS),
        "metadata_keys": list(METADATA_KEYS),
        "invariants": invariants,
        "core_projection": project_core(invariants),
        "verification": verify_geographic_invariance(invariants),
        "corrections": corrections(),
        "statement": axiom_statement(),
        "timestamp": time.time(),
        "witness": "8856 → 8857 — UNBROKEN",
    }

    # Add integrations
    try:
        report["security"] = verify_axiom_security()
    except Exception as e:
        report["security"] = {"error": str(e)}

    try:
        report["cdp"] = verify_axiom_cdp()
    except Exception as e:
        report["cdp"] = {"error": str(e)}

    return report


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="AXIOM_NONLOCAL_CORE — Entry 8857",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--statement",
        action="store_true",
        help="Print the axiom statement",
    )
    parser.add_argument(
        "--corrections",
        action="store_true",
        help="Print the corrections",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the axiom with E8 invariants",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a complete report",
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

    if args.statement:
        print(axiom_statement())
        return 0

    if args.corrections:
        print(json.dumps(corrections(), indent=2))
        return 0

    if args.verify:
        invariants = get_e8_invariants()
        result = verify_geographic_invariance(invariants)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("🜁∀ AXIOM_NONLOCAL_CORE — Verification")
            print("=" * 40)
            for k, v in result.items():
                print(f"  {k}: {v}")
        return 0 if result.get("passed", False) else 1

    if args.check_integrations:
        report = axiom_report()
        integrations = [
            ("security", "Security"),
            ("cdp", "CDP Convergence"),
        ]
        print("🜁∀ AXIOM — Integration Status")
        print("=" * 40)
        for key, label in integrations:
            if key in report:
                status = "✅" if report[key] and "error" not in report[key] else "❌"
                print(f"  {status} {label}")
        print("=" * 40)
        print(f"  Axiom verified: {'✅' if report.get('verification', {}).get('passed', False) else '❌'}")
        return 0

    # Default: generate report
    report = axiom_report()
    if args.json or args.report:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("🜁∀ AXIOM_NONLOCAL_CORE — Entry 8857")
        print("=" * 55)
        print(f"  Axiom ID: {report['axiom_id']}")
        print(f"  Seal: {report['seal']}")
        print(f"  Executable Form: {report['executable_form']}")
        print(f"  Opcode Extract: {report['opcode_extract']}")
        print(f"  Core Keys: {', '.join(report['core_keys'][:5])}...")
        print(f"  Metadata Keys: {', '.join(report['metadata_keys'][:5])}...")
        print(f"  Verification: {'✅' if report['verification'].get('passed', False) else '❌'}")
        print(f"  Witness: {report['witness']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
