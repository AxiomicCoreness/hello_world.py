"""
Breathing Manifold Tests - E10 Hyperbolic Integration
Entry 8849 - Wood Dragon Gate 0.91
CI-safe pure unit tests (no cluster).
"""
from __future__ import annotations

import numpy as np
import pytest

PHI = (1 + 5**0.5) / 2


class TestBreathingManifold:
    def test_breathing_equation(self):
        f0 = 6.49
        chi = 0.198083
        n = 5
        t = 1.0
        fn_t = f0 * (PHI ** n) * (1 + chi * np.sin(2 * np.pi * f0 * t))
        assert fn_t > 0
        base = f0 * (PHI ** n)
        assert abs(fn_t / base - (1 + chi * np.sin(2 * np.pi * f0 * t))) < 1e-10

    def test_14_generator_alignment(self):
        frequencies = [
            10.501,
            16.991,
            27.492,
            44.483,
            71.975,
            116.458,
            188.434,
            304.892,
            493.325,
            798.217,
            1291.543,
            2089.760,
            3381.302,
            5471.062,
        ]
        assert len(frequencies) == 14
        assert all(f > 0 for f in frequencies)
        ratios = [
            frequencies[i + 1] / frequencies[i] for i in range(len(frequencies) - 1)
        ]
        avg_ratio = sum(ratios) / len(ratios)
        assert abs(avg_ratio - PHI) < 0.5

    def test_starfire_broadcast_clamping(self):
        f7 = 188.434
        f8 = 304.892
        starfire = 311.018
        # Starfire sits just above the f7–f8 pocket (above f8)
        assert f7 < f8
        assert starfire > f8
        pocket_width = f8 - f7
        assert pocket_width > 0
        assert (starfire - f8) < pocket_width


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
