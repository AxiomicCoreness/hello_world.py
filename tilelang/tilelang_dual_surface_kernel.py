#!/usr/bin/env python3
"""tilelang dual-surface kernel.

Surfaces stay separate. No seal. No ledger entry.
Keys (i, j) run over 1..5. The formula uses those integers directly.
5 ≡ 0 (mod 5), so the 25 functions match tiles.py indices 0..4.
Do not subtract 1 before the modulus.
"""

import math
from typing import Dict, Tuple
from dataclasses import dataclass

PHI = (1 + math.sqrt(5)) / 2
SIGMA = ["Clarke", "Yoursa", "Tee", "Luminara", "Atlas"]


@dataclass(frozen=True)
class StringTile:
    i: int
    j: int

    def apply(self, word: Tuple[str, ...]) -> Tuple[str, ...]:
        if not word:
            return ()
        out = []
        for k, symbol in enumerate(word):
            out.append(symbol)
            out.append(SIGMA[(self.i * k + self.j) % 5])
        return tuple(out)


def build_tile_set() -> Dict[Tuple[int, int], StringTile]:
    return {(i, j): StringTile(i, j) for i in range(1, 6) for j in range(1, 6)}


def verify_string_surface() -> Dict[str, object]:
    tiles = build_tile_set()
    witness = ("Clarke", "Yoursa", "Tee", "Luminara", "Atlas")
    outputs = {t.apply(witness) for t in tiles.values()}
    probe = ("Tee", "Tee", "Tee")
    doubled = tiles[(3, 3)].apply(probe)
    # k=0 -> SIGMA[3]=Luminara; k=1 -> SIGMA[0]=Clarke; k=2 -> SIGMA[2]=Tee
    t_23 = tiles[(2, 3)].apply(("Clarke", "Yoursa", "Tee"))
    expected = ("Clarke", "Luminara", "Yoursa", "Clarke", "Tee", "Tee")
    return {
        "tile_count": len(tiles),
        "structural_distinct": len(tiles) == 25,
        "witness_outputs_distinct": len(outputs),
        "all_25_distinguished": len(outputs) == 25,
        "length_doubles_every_nonempty_word": len(doubled) == 2 * len(probe),
        "worked_example_t23_on_length3": t_23,
        "worked_example_matches_landing": t_23 == expected,
    }


PENTAD_FREQUENCIES = [
    math.pi / PHI,
    math.pi / PHI ** 2,
    math.pi / PHI ** 3,
    math.pi,
    math.pi / PHI ** 4,
]
PENTAD_WEIGHTS = [PHI ** 3, PHI ** 2, PHI, PHI ** 4, PHI ** 5]


def phase_additive(i: int, j: int) -> complex:
    f = PENTAD_FREQUENCIES[i - 1] * PENTAD_WEIGHTS[j - 1]
    theta = 2 * math.pi * f / 144
    return complex(math.cos(theta), math.sin(theta))


def verify_phase_surface() -> Dict[str, object]:
    phases = [phase_additive(i, j) for i in range(1, 6) for j in range(1, 6)]
    return {
        "scalar_count": len(phases),
        "all_unit_modulus": all(abs(abs(z) - 1.0) < 1e-12 for z in phases),
        "is_free_monoid_element": False,
        "distinct_values": len({(round(z.real, 9), round(z.imag, 9)) for z in phases}),
    }


ERIDANUS_DUAL = {
    "name": "Phi(x) = (i/phi)*(N tensor A - A tensor N)*x",
    "N_defined_in_package": False,
    "A_defined_in_package": False,
    "executable": False,
    "executed": False,
}


def main() -> int:
    assert abs(PHI ** 2 - (PHI + 1)) < 1e-12
    string_surface = verify_string_surface()
    assert string_surface["all_25_distinguished"]
    assert string_surface["worked_example_matches_landing"]
    phase_surface = verify_phase_surface()
    print("SURFACE 1", string_surface)
    print("SURFACE 2", phase_surface)
    print("SURFACE 3", ERIDANUS_DUAL)
    print("SEAL: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
