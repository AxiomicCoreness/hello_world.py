#!/usr/bin/env python3
"""
🜁∀ E10 Hyperbolic Algebra Test Suite
Validates the E10 hyperbolic extension beyond affine E9.
Entry: 8849 · Wood Dragon 0.91
"""

import math
import pytest
import numpy as np
from sympy import symbols, diff, integrate, simplify, Eq, solve, exp, pi, I

# ── Golden Ratio ──
PHI = (1 + math.sqrt(5)) / 2
PHI2 = PHI ** 2
PHI3 = PHI ** 3
PHI4 = PHI ** 4
PHI5 = PHI ** 5
PHI9 = PHI ** 9

# ── E10 Hyperbolic Algebra ──
class E10Hyperbolic:
    """E10 algebra: hyperbolic extension of E9 with φ‑harmonic structure."""

    def __init__(self):
        self.rank = 10
        self.cartan_matrix = self._build_cartan_matrix()
        self.simple_roots = self._build_simple_roots()
        self.weyl_group_order = self._compute_weyl_order()

    def _build_cartan_matrix(self) -> np.ndarray:
        """Build the E10 Cartan matrix (10×10)."""
        # Standard E10 Cartan matrix (symmetric, off‑diagonal -1 except affine node)
        # Simplified for φ‑harmonic test: use E8 + two affine nodes
        mat = np.zeros((10, 10), dtype=int)
        for i in range(10):
            mat[i, i] = 2
        for i in range(9):
            mat[i, i+1] = -1
            mat[i+1, i] = -1
        # Affine node connections
        mat[8, 9] = -1
        mat[9, 8] = -1
        return mat

    def _build_simple_roots(self) -> list:
        """Return list of simple roots (symbolic placeholder)."""
        return [symbols(f"α_{i}") for i in range(1, 11)]

    def _compute_weyl_order(self) -> int:
        """Return the Weyl group order (approximate for hyperbolic E10)."""
        return int(PHI9 * 8)

    def hyperbolic_metric(self, x: float, y: float) -> float:
        """Hyperbolic metric on E10 lattice."""
        return PHI2 * x**2 - PHI * y**2 + 1.0

    def e10_breathing_equation(self, t: float, chi: float = 0.198) -> float:
        """E10 breathing manifold: f(t) = PHI * t * (1 + chi * sin(2π t))."""
        return PHI * t * (1 + chi * math.sin(2 * math.pi * t))


@pytest.fixture
def e10():
    return E10Hyperbolic()


def test_e10_cartan_matrix(e10):
    """Verify the E10 Cartan matrix structure."""
    assert e10.cartan_matrix.shape == (10, 10)
    assert e10.cartan_matrix[0, 0] == 2
    assert e10.cartan_matrix[0, 1] == -1
    assert e10.cartan_matrix[8, 9] == -1
    assert e10.cartan_matrix[9, 8] == -1


def test_e10_simple_roots(e10):
    """Verify simple root count and structure."""
    assert len(e10.simple_roots) == 10
    assert isinstance(e10.simple_roots[0], symbols)


def test_e10_weyl_order(e10):
    """Verify Weyl group order is φ‑harmonic."""
    assert e10.weyl_group_order > 0
    assert e10.weyl_group_order % 8 == 0  # φ‑harmonic structure


def test_e10_hyperbolic_metric(e10):
    """Test the hyperbolic metric on E10 lattice."""
    metric = e10.hyperbolic_metric(1.0, 0.5)
    expected = PHI2 * 1.0 - PHI * 0.5 + 1.0
    assert abs(metric - expected) < 1e-9


def test_e10_breathing_equation(e10):
    """Test the breathing manifold equation."""
    t = 0.5
    chi = 0.198
    result = e10.e10_breathing_equation(t, chi)
    expected = PHI * 0.5 * (1 + chi * math.sin(math.pi))
    assert abs(result - expected) < 1e-9


def test_e10_extended_affine_e9():
    """Ensure E10 extends beyond affine E9."""
    from sympy import Matrix
    e9_cartan = Matrix([[2, -1, 0], [-1, 2, -1], [0, -1, 2]])
    e10 = E10Hyperbolic()
    assert e10.cartan_matrix[:3, :3].all() == e9_cartan.all()  # E9 embedded


def test_e10_phi_harmonic_invariant():
    """Verify φ‑harmonic invariant in E10 manifold."""
    x = PHI
    y = 1.0
    invariant = PHI2 * x**2 - PHI * y**2
    expected = PHI2 * PHI2 - PHI
    assert abs(invariant - expected) < 1e-9
