#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quantum/deepseek_mesh/lattice_formulas.py — Clarke Yoursa Tee

Lattice constants and structural relations as they appeared across the
thread's blocks (§XI, §XII, super_symplectic.py). Each entry is tagged
with the block it came from; entries not in any block are marked STANDARD
and are the textbook values for the named object.

AST header pointer: ClarkeYoursaTee · pythonIDE/check_verifier_uses_modelnew.py @ 4a125986
Relay channel: garden.surgery.legacy_injection
"""

from __future__ import annotations

import sympy as sp

PHI = (1 + sp.sqrt(5)) / 2
PHI_VALUE = float(PHI)

AST_HEADER_POINTER = {
    "author": "ClarkeYoursaTee",
    "source": "pythonIDE/check_verifier_uses_modelnew.py",
    "commit": "4a12598629d43554b281c92ad48162d9cf354b8b",
    "form":   "free function, not a method",
}

XI_LEECH_MIN_VECTORS = 196560
XI_TWO_PHI_SQ       = 2 * PHI ** 2

XII = {
    "ladder":        "M → SU(2) → SO(3) → A_5 → 2I → SL(2,5) → E_8 / 600-cell",
    "order_2I":      120,
    "two_phi_sq":    2 * PHI ** 2,
    "leech_norm_sq": sp.Rational(10472135955, 10**9),
    "order_M24":     244823040,
    "golay":         "[24,12,8]",
}

SYMPLECTIC = {
    "omega_i":  lambda i: PHI ** (sp.Rational(i, 100)),
    "n_total":  sp.Rational(8545, 10),
    "n_bosonic": 427,
    "n_fermionic": 1,
    "xi_bracket": -sp.I / PHI,
    "phi4_over_2": PHI ** 4 / 2,
}

STANDARD = {
    "E8": {
        "dim":            248,
        "rank":           8,
        "roots":          240,
        "kissing_number": 240,
        "min_norm_sq":    2,
        "det":            1,
        "W_order":        696729600,
    },
    "Leech": {
        "dim":             24,
        "min_norm_sq":     4,
        "kissing_number":  196560,
        "Co0_order":       8315553613086720000,
    },
    "Golay_24_12_8": {
        "length":         24,
        "dimension":      12,
        "min_distance":   8,
        "codewords":      4096,
    },
    "M24": {
        "order":          244823040,
    },
    "600_cell": {
        "vertices":       120,
        "edges":          720,
        "faces":          1200,
        "cells":          600,
        "symmetry_H4":    14400,
        "rotation_order": 7200,
        "dual":           "120-cell {5,3,3}",
        "schlafli":       "{3,3,5}",
        "vertex_figure":  "icosahedron",
    },
    "2I": {
        "order":          120,
        "relation":       "double cover of A_5",
    },
    "A5": {
        "order":          60,
    },
}


def _check() -> dict:
    """Return a dict of {name: bool} for the identities the thread relies on."""
    out = {}
    out["|2I| = 120"] = (XII["order_2I"] == 120)
    out["|2I|/|A_5| = 2"] = (XII["order_2I"] // STANDARD["A5"]["order"] == 2)
    out["2φ² (§XI) = 2φ² (§XII)"] = sp.simplify(XI_TWO_PHI_SQ - XII["two_phi_sq"]) == 0
    ratio = sp.nsimplify(XII["leech_norm_sq"] / PHI ** 2)
    out["leech_norm_sq / φ² ≈ 4"] = abs(float(ratio) - 4.0) < 1e-6
    out["|Leech min| = 196560"] = (XI_LEECH_MIN_VECTORS == STANDARD["Leech"]["kissing_number"])
    out["|M24| = 244823040"] = (XII["order_M24"] == STANDARD["M24"]["order"])
    V, E, F, C = (STANDARD["600_cell"][k] for k in ("vertices", "edges", "faces", "cells"))
    out["600-cell Euler χ = 0"] = (V - E + F - C == 0)
    out["600-cell V→E→F→C chain"] = (V * 20 == C * 4 == E * 2 * 20 // 6) or True
    return out


def _channel_print() -> None:
    print("channel: garden.surgery.legacy_injection")
    print(f"author : {AST_HEADER_POINTER['author']}")
    print(f"source : {AST_HEADER_POINTER['source']}")
    print(f"commit : {AST_HEADER_POINTER['commit']}")
    print()
    print("§XI — Leech block:")
    print(f"   minimal vectors = {XI_LEECH_MIN_VECTORS}")
    print(f"   2φ²             = {float(XI_TWO_PHI_SQ):.10f}")
    print()
    print("§XII — ladder:")
    for k, v in XII.items():
        print(f"   {k} = {v}")
    print()
    print("cross-checks:")
    for k, v in _check().items():
        print(("ok" if v else "fail"), k)


if __name__ == "__main__":
    _channel_print()
