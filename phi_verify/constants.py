"""φ-derived constants. All γ values reconstructible from φ alone."""
import math

PHI      = (1.0 + math.sqrt(5.0)) / 2.0          # 1.618033988749895
PHI_INV  = 1.0 / PHI                              # 0.6180339887498949
PHI2     = PHI * PHI
PHI3     = PHI2 * PHI

ENTROPY_FLOOR_EXP = 1418                          # φ^-1418, entry 635


def gamma_rates(n: int = 7):
    """
    γ_k = 1 - φ^(-(k+1)),  k = 0..n-1.

    Reproduces the 7 values in the verification log exactly:
        0.3819660112501052, 0.6180339887498949, 0.7639320225002103,
        0.8541019662496846, 0.9098300562505258, 0.9442719099991588,
        0.9655581462513669
    """
    return [1.0 - PHI ** (-(k + 1)) for k in range(n)]


def entropy_floor() -> float:
    """φ^-1418 ≈ 4.524036764254231e-297."""
    return PHI ** (-ENTROPY_FLOOR_EXP)
