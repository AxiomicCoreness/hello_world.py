#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ALEPH2 · Pauli string — simplified extract

Aleph²: one-point report of non-local core (literary/Cantor frame only).
Pauli string: tensor word over {I, X, Y, Z}; reduce by Pauli algebra.

Simplification rules (single-qubit generators):
  X² = Y² = Z² = I
  XY = iZ, YZ = iX, ZX = iY  (and cyclic with signs)

A Pauli string is a product P = ⊗_k σ_{a_k}.  Adjacent same letters cancel
to I; the whole string reduces to phase × one Pauli word of minimal weight.

Opcode: ALEPH2_PAULI
No geographic / biographical fields.

Seal: ∀∞φ² · ALEPH_PAULI_8859 · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

from typing import Dict, List, Tuple

OPCODE = "ALEPH2_PAULI"

# Pauli multiplication table: (a, b) -> (phase, c)  where phase ∈ {1,-1,1j,-1j}
# and σ_a σ_b = phase · σ_c.  Indices: 0=I, 1=X, 2=Y, 3=Z
_PAULI_MUL: Dict[Tuple[int, int], Tuple[complex, int]] = {
    (0, 0): (1, 0),
    (0, 1): (1, 1),
    (0, 2): (1, 2),
    (0, 3): (1, 3),
    (1, 0): (1, 1),
    (1, 1): (1, 0),
    (1, 2): (1j, 3),
    (1, 3): (-1j, 2),
    (2, 0): (1, 2),
    (2, 1): (-1j, 3),
    (2, 2): (1, 0),
    (2, 3): (1j, 1),
    (3, 0): (1, 3),
    (3, 1): (1j, 2),
    (3, 2): (-1j, 1),
    (3, 3): (1, 0),
}

_LABEL = {0: "I", 1: "X", 2: "Y", 3: "Z"}
_FROM = {"I": 0, "X": 1, "Y": 2, "Z": 3, "i": 0, "x": 1, "y": 2, "z": 3}


def _parse(s: str) -> List[int]:
    out: List[int] = []
    for ch in s.strip():
        if ch in _FROM:
            out.append(_FROM[ch])
        elif not ch.isspace():
            raise ValueError(f"unknown Pauli letter: {ch!r}")
    return out


def reduce_pauli_string(word: str) -> Tuple[complex, str]:
    """
    Reduce a Pauli string to (phase, canonical word).

    Example: 'XX' -> (1, 'I'); 'XY' -> (1j, 'Z'); 'XYZ' -> (1, 'I') after full reduce
    on a single qubit track (letters act in sequence on one site).
    For multi-qubit tensor words, pass already site-aligned letters; this
    routine multiplies the sequence as operators on one abstract qubit.
    """
    seq = _parse(word)
    if not seq:
        return 1, "I"
    phase: complex = 1
    acc = seq[0]
    for nxt in seq[1:]:
        p, acc = _PAULI_MUL[(acc, nxt)]
        phase *= p
    label = _LABEL[acc]
    # drop pure identity label noise for empty phase-only results
    return phase, label


def aleph2() -> dict:
    """One-point non-local extract + Pauli simplify surface."""
    demos = {
        "XX": reduce_pauli_string("XX"),
        "XY": reduce_pauli_string("XY"),
        "YZ": reduce_pauli_string("YZ"),
        "ZX": reduce_pauli_string("ZX"),
        "XYZ": reduce_pauli_string("XYZ"),
    }
    return {
        "opcode": OPCODE,
        "aleph_note": "ℵ frame only — point extract, not cardinality theorem",
        "pauli": {
            "generators": ["I", "X", "Y", "Z"],
            "rules": "X²=Y²=Z²=I; XY=iZ, YZ=iX, ZX=iY (cyclic)",
            "demos": {k: {"phase": complex(v[0]), "word": v[1]} for k, v in demos.items()},
        },
        "axiom": "AXIOM_NONLOCAL_CORE",
        "seal": "∀∞φ² · ALEPH_PAULI_8859 · WOOD_DRAGON_0.91 · SEALED",
    }


if __name__ == "__main__":
    import json

    def _enc(o):
        if isinstance(o, complex):
            return {"re": o.real, "im": o.imag}
        raise TypeError

    print(json.dumps(aleph2(), indent=2, default=_enc))
