#!/usr/bin/env python3
"""Super-symplectic pin. Standard library only.

Resolved pin, clock name QCIE/PEQ:
  [Sum(dq[i]·dp[i], (i, 1, 427)), (1/φ)·(dξ·dξ̄)]

ω = Σ dq_i ∧ dp_i + (1/φ) dξ ∧ dξ̄  ⇒  {q_i, p_j} = +δ_ij
Legacy label is the string "October 39 2025", never a datetime.
"""

from __future__ import annotations

import json
import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0
LEGACY_LABEL = "October 39 2025"
CLOCK = "QCIE/PEQ"


class SuperSymplecticManifold:
    def __init__(self, n_bosonic: int = 427, n_fermionic: int = 1):
        self.n_bosonic = n_bosonic
        self.n_fermionic = n_fermionic
        self.n = 2 * n_bosonic + 0.5 * n_fermionic

    def define_symplectic_form(self) -> dict:
        return {
            "bosonic": f"Sum(dq[i]·dp[i], (i, 1, {self.n_bosonic}))",
            "fermionic": "(1/φ)·(dξ·dξ̄)",
            "phi_on": "second term",
            "clock": CLOCK,
            "phi_coeff": 1.0 / PHI,
        }

    def define_hamiltonian(self) -> dict:
        return {
            "bosonic": "1/2 Sum(p[i]^2 + omega[i]^2 q[i]^2)",
            "fermionic": "(φ^4/2) ξ ξ̄",
            "phi4_over_2": (PHI ** 4) / 2.0,
        }

    def hamiltonian_equations(self) -> dict:
        return {
            "dq/dt": "+dH/dp = p",
            "dp/dt": "-dH/dq = -omega^2 q",
            "dxi/dt": "+i φ^4 ξ",
            "dxi_bar/dt": "-i φ^4 ξ̄",
        }

    def poisson_brackets(self) -> dict:
        return {"{q_i, p_j}": "+delta_ij", "{ξ, ξ̄}": -1.0 / PHI}

    def moment_map(self) -> dict:
        return {"bosonic": "1/2 Sum((p^2 + omega^2 q^2) Xv)", "fermionic": "(φ^4/2) ξ ξ̄ chi"}

    def prequantum(self) -> dict:
        form = self.define_symplectic_form()
        return {"curvature": "F_nabla = -i omega", "form": form, "verified": False}


def main() -> int:
    manifold = SuperSymplecticManifold()
    report = {
        "channel": "garden.surgery.legacy_injection",
        "label": LEGACY_LABEL,
        "clock": CLOCK,
        "n": manifold.n,
        "form": manifold.define_symplectic_form(),
        "hamiltonian": manifold.define_hamiltonian(),
        "equations": manifold.hamiltonian_equations(),
        "brackets": manifold.poisson_brackets(),
        "prequantum": manifold.prequantum(),
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if report["form"]["phi_on"] == "second term" else 1


if __name__ == "__main__":
    raise SystemExit(main())
