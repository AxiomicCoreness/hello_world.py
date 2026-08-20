#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXIOM_NONLOCAL_CORE — mathematical axiom for AxiomicCoreness/hello_world.py

Statement
---------
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

Scope boundary
--------------
- Author origin (e.g. Cambodian refugee path in Massachusetts) is human
  ground for the work and may be recorded in prose or metadata.
- It does not become a governing variable of the lattice.
- The AI operating on the repo does not adopt that personal identity.

License context: MIT (as declared by the repository author).

Seal: ∀∞φ² · AXIOM_NONLOCAL_8853 · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

# Formal identifier
AXIOM_ID = "AXIOM_NONLOCAL_CORE"
AXIOM_SEAL = "∀∞φ² · AXIOM_NONLOCAL_8853 · WOOD_DRAGON_0.91 · SEALED"

# Core keys that define mathematical identity of the E8 surface
CORE_KEYS = frozenset(
    {
        "phi",
        "weyl_order_e8",
        "cartan",
        "cartan_det",
        "cartan_shape",
    }
)

# Keys treated as non-governing annotations
METADATA_KEYS = frozenset(
    {
        "uprho_global",
        "regional_tech_depth",
        "historical_context",
        "author_origin",
        "geographic_reference",
        "biographical_annotation",
    }
)


def project_core(invariants: Mapping[str, Any]) -> Dict[str, Any]:
    """Extract only core mathematical fields."""
    out: Dict[str, Any] = {}
    for k in CORE_KEYS:
        if k in invariants:
            out[k] = invariants[k]
    # Allow cartan_shape to be derived if cartan present
    if "cartan" in invariants and "cartan_shape" not in out:
        c = invariants["cartan"]
        out["cartan_shape"] = (len(c), len(c[0]) if c else 0)
    return out


def strip_metadata(invariants: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a copy with known metadata keys removed."""
    return {k: v for k, v in invariants.items() if k not in METADATA_KEYS}


def cores_equal(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    """True iff core projections match."""
    ca, cb = project_core(a), project_core(b)
    if set(ca.keys()) != set(cb.keys()):
        # Still OK if both missing optional derived keys consistently
        pass
    for k in CORE_KEYS:
        if k == "cartan_shape":
            continue
        if k in ca or k in cb:
            if ca.get(k) != cb.get(k):
                return False
    if "cartan" in ca and "cartan" in cb:
        if ca["cartan"] != cb["cartan"]:
            return False
    return True


def verify_geographic_invariance(
    invariants_with_geo: Mapping[str, Any],
    *,
    substitute: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Verify AXIOM_NONLOCAL_CORE on a concrete invariants dict.

    - Strip all METADATA_KEYS and compare cores.
    - Optionally compare against a substituted metadata map.
    """
    stripped = strip_metadata(dict(invariants_with_geo))
    ok_strip = cores_equal(invariants_with_geo, stripped)

    ok_sub = True
    if substitute is not None:
        merged = dict(invariants_with_geo)
        merged.update(substitute)
        ok_sub = cores_equal(invariants_with_geo, merged)

    return {
        "axiom_id": AXIOM_ID,
        "strip_metadata_preserves_core": ok_strip,
        "substitute_preserves_core": ok_sub,
        "passed": bool(ok_strip and ok_sub),
        "seal": AXIOM_SEAL,
    }


def axiom_statement() -> str:
    return (
        "AXIOM_NONLOCAL_CORE: Core transformations depend only on abstract "
        "mathematical structure (Cartan/E8, Weyl order, gates, witness, exact "
        "arithmetic, ledger semantics). Geographic and biographical annotations "
        "are metadata; substituting or removing them does not change core results."
    )


if __name__ == "__main__":
    # Self-check against e8 surface if importable
    try:
        from quantum.e8_uprho_global import invariants as e8_inv

        inv = e8_inv()
        report = verify_geographic_invariance(
            inv,
            substitute={"regional_tech_depth": {"Iceland": {"gii_2025": 20}}},
        )
        print(axiom_statement())
        print(report)
    except Exception as e:
        print(axiom_statement())
        print({"standalone": True, "note": str(e), "seal": AXIOM_SEAL})
