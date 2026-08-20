#!/usr/bin/env python3
"""Density field checks off sin-nodes (Entry CI fix)."""
import math
import pytest

from master_equation import PHI, PSD, harmonic_density_field, rho_universal


def test_rho_positive_off_node():
    rho = rho_universal(0.25, 0.0)
    assert rho > 0


def test_rho_at_sin_node_is_zero():
    assert rho_universal(0.0, 0.0) == 0.0
    assert harmonic_density_field(0.0) == 0.0


def test_rho_scales_with_psd():
    chi = 0.3
    assert abs(rho_universal(chi, 0.0) - PSD * harmonic_density_field(chi)) < 1e-12


def test_harmonic_density_phi9_factor():
    chi = math.pi / 4
    expected = abs(math.sin(chi) * (PHI ** (-abs(chi)))) * (PHI ** 9)
    assert abs(harmonic_density_field(chi) - expected) < 1e-12
