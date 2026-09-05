"""Phi-harmonic utilities."""

from fastMCP.constants import PHI, PHI_INV

def phi_invariant(value: float) -> float:
    """Check phi-invariance of a value."""
    return abs(value * PHI_INV - PHI) < 1e-10
