#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ALEPH2 · Pauli string + non-Abelian commutation

Aleph²: one-point report of non-local core (literary/Cantor frame only).
Pauli algebra: multiplication table + commutation / anticommutation.

Non-Abelian relations (su(2)):
  [X, Y] = 2i Z
  [Y, Z] = 2i X
  [Z, X] = 2i Y

Anticommutators:
  {X, Y} = {Y, Z} = {Z, X} = 0
  {X, X} = {Y, Y} = {Z, Z} = 2 I

Opcode: ALEPH2_PAULI
No geographic / biographical fields.

Seal: ∀∞φ² · PAULI_COMM_8902 · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

from typing import Dict, List, Tuple

OPCODE = "ALEPH2_PAULI"

# Indices: 0=I, 1=X, 2=Y, 3=Z
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
    """Reduce a Pauli string to (phase, canonical letter)."""
    seq = _parse(word)
    if not seq:
        return 1, "I"
    phase: complex = 1
    acc = seq[0]
    for nxt in seq[1:]:
        p, acc = _PAULI_MUL[(acc, nxt)]
        phase *= p
    return phase, _LABEL[acc]


def commutator(a: str, b: str) -> Tuple[complex, str]:
    """
    Non-Abelian commutator [A, B] = AB - BA.

    Returns (phase, letter) such that [A,B] = phase · letter.
    Canonical results:
      [X,Y] = 2i Z
      [Y,Z] = 2i X
      [Z,X] = 2i Y
    """
    ia, ib = _FROM[a.upper()], _FROM[b.upper()]
    # AB
    p_ab, c_ab = _PAULI_MUL[(ia, ib)]
    # BA
    p_ba, c_ba = _PAULI_MUL[(ib, ia)]
    # AB - BA
    if c_ab == c_ba:
        phase = p_ab - p_ba
        if phase == 0:
            return 0, "I"
        return phase, _LABEL[c_ab]
    # different support — should not occur for Pauli generators
    raise ValueError(f"unexpected support: {[c_ab, c_ba]}")


def anticommutator(a: str, b: str) -> Tuple[complex, str]:
    """{A, B} = AB + BA.  Diagonal → 2I; off-diagonal → 0."""
    ia, ib = _FROM[a.upper()], _FROM[b.upper()]
    p_ab, c_ab = _PAULI_MUL[(ia, ib)]
    p_ba, c_ba = _PAULI_MUL[(ib, ia)]
    if c_ab == c_ba:
        phase = p_ab + p_ba
        if phase == 0:
            return 0, "I"
        return phase, _LABEL[c_ab]
    raise ValueError(f"unexpected support: {[c_ab, c_ba]}")


def aleph2() -> dict:
    """One-point non-local extract + Pauli algebra surface."""
    demos_reduce = {
        "XX": reduce_pauli_string("XX"),
        "XY": reduce_pauli_string("XY"),
        "YZ": reduce_pauli_string("YZ"),
        "ZX": reduce_pauli_string("ZX"),
    }
    demos_comm = {
        "[X,Y]": commutator("X", "Y"),
        "[Y,Z]": commutator("Y", "Z"),
        "[Z,X]": commutator("Z", "X"),
    }
    demos_acomm = {
        "{X,Y}": anticommutator("X", "Y"),
        "{X,X}": anticommutator("X", "X"),
    }
    return {
        "opcode": OPCODE,
        "aleph_note": "ℵ frame only — point extract, not cardinality theorem",
        "pauli": {
            "generators": ["I", "X", "Y", "Z"],
            "product_rules": "X²=Y²=Z²=I; XY=iZ, YZ=iX, ZX=iY (cyclic)",
            "commutation": "[X,Y]=2iZ, [Y,Z]=2iX, [Z,X]=2iY  (non-Abelian)",
            "demos_reduce": {
                k: {"phase": complex(v[0]), "word": v[1]} for k, v in demos_reduce.items()
            },
            "demos_comm": {
                k: {"phase": complex(v[0]), "word": v[1]} for k, v in demos_comm.items()
            },
            "demos_acomm": {
                k: {"phase": complex(v[0]), "word": v[1]} for k, v in demos_acomm.items()
            },
        },
        "axiom": "AXIOM_NONLOCAL_CORE",
        "seal": "∀∞φ² · PAULI_COMM_8902 · WOOD_DRAGON_0.91 · SEALED",
    }


if __name__ == "__main__":
    import json

    def _enc(o):
        if isinstance(o, complex):
            return {"re": o.real, "im": o.imag}
        raise TypeError

    print(json.dumps(aleph2(), indent=2, default=_enc))
