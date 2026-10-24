"""Float-safety tests for quadratic_daemon discriminant check."""
from celestial.quadratic_daemon import solve_quadratic, RootKind


def test_near_zero_discriminant_returns_repeated_root():
    """a=1, b=2, c=1.0000000000000002 produces D ≈ -1e-15 (near zero).
    With == 0.0 this would fall through to the complex branch; with
    math.isclose it correctly returns REAL_REPEATED."""
    result = solve_quadratic(1.0, 2.0, 1.0000000000000002)
    assert result.kind == RootKind.REAL_REPEATED


def test_exact_zero_discriminant_still_repeated():
    """a=1, b=2, c=1 produces D = 0 exactly."""
    result = solve_quadratic(1.0, 2.0, 1.0)
    assert result.kind == RootKind.REAL_REPEATED


def test_positive_discriminant_still_distinct():
    """a=1, b=-3, c=2 produces D = 1 > 0."""
    result = solve_quadratic(1.0, -3.0, 2.0)
    assert result.kind == RootKind.REAL_DISTINCT


def test_negative_discriminant_still_complex():
    """a=1, b=0, c=1 produces D = -4 < 0."""
    result = solve_quadratic(1.0, 0.0, 1.0)
    assert result.kind == RootKind.COMPLEX_PAIR
