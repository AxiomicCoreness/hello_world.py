"""Entry 8336 — ConvergenceWindow integrity (not liveness-only φ check)."""
from __future__ import annotations

import math

from math_origin import PHI, convergence_window, verify_canonical_19


def test_phi_polynomial_liveness():
    assert abs(PHI**2 - (PHI + 1)) < 1e-15


def test_canonical_19():
    ok, cw = verify_canonical_19()
    assert ok
    assert cw.n == 19
    assert cw.L_n == 9349
    assert cw.F_n == 4181
    assert cw.k == 4


def test_phase_is_residue_not_modulus():
    cw = convergence_window(19)
    # Window bound π/φ ≈ 111.246° — NOT the phase u
    assert abs(cw.modulus_deg - 111.246) < 0.01
    assert abs(cw.u_deg - 78.87) < 0.05
    assert cw.u_deg < 90.0  # must not be reported as 111.246


def test_multiplier_is_n_not_26():
    cw = convergence_window(19)
    assert abs(cw.raw - 19 * math.log(PHI)) < 1e-12
    assert abs(cw.raw - 26 * math.log(PHI)) > 1.0  # not 26·ln φ


def test_payload_segment_grammar():
    seg = convergence_window(19).payload_segment()
    assert seg.startswith("math_origin=Convergence_window(")
    assert "n=19" in seg
    assert "L=9349" in seg
    assert "F=4181" in seg
    assert "k=4" in seg
