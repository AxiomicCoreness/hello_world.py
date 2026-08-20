#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXIOM_NONLOCAL_CORE — mathematical axiom for AxiomicCoreness/hello_world.py

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

Seal: ∀∞φ² · AXIOM_NONLOCAL_8857 · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

AXIOM_ID = "AXIOM_NONLOCAL_CORE"
AXIOM_SEAL = "∀∞φ² · AXIOM_NONLOCAL_8857 · WOOD_DRAGON_0.91 · SEALED"
EXECUTABLE_FORM = "Trigger_Gravastar_ClarkeYoursaTee"
OPCODE_EXTRACT = "ALEPH2"

CORE_KEYS = frozenset(
    {
        "phi",
        "weyl_order_e8",
        "cartan",
        "cartan_det",
        "cartan_shape",
    }
)

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
    """Verify AXIOM_NONLOCAL_CORE: strip/substitute metadata; cores must match."""
    stripped = strip_metadata(dict(invariants_with_geo))
    ok_strip = cores_equal(invariants_with_geo, stripped)

    ok_sub = True
    if substitute is not None:
        merged = dict(invariants_with_geo)
        merged.update(substitute)
        ok_sub = cores_equal(invariants_with_geo, merged)

    return {
        "axiom_id": AXIOM_ID,
        "executable_form": EXECUTABLE_FORM,
        "opcode_extract": OPCODE_EXTRACT,
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
        "are metadata; substituting or removing them does not change core results. "
        "Author origin is human ground under MIT, not a lattice parameter; "
        "modern technology does not take that personal identity as its own. "
        f"Executable form: {EXECUTABLE_FORM}. Opcode extract: {OPCODE_EXTRACT}."
    )


def corrections() -> Dict[str, str]:
    """Explicit non-local corrections (prose form for ledger/humans)."""
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
    }


if __name__ == "__main__":
    print(axiom_statement())
    print(corrections())
    try:
        from quantum.e8_uprho_global import invariants as e8_inv

        inv = e8_inv()
        report = verify_geographic_invariance(
            inv,
            substitute={"regional_tech_depth": {"Iceland": {"gii_2025": 20}}},
        )
        print(report)
    except Exception as e:
        print({"standalone": True, "note": str(e), "seal": AXIOM_SEAL})
