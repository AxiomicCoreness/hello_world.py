"""ADE surface singularities and the static quadratic-program split.

Research extract. Not a measurement, not a seal, not a vendored OSQP build.
OsqpEigen Solver.cpp remains Giulio Romualdi, BSD 3-Clause, 2018, and is not copied.

The quadratic program is

    min_x  1/2 x^T P x + q^T x
    subject to  l <= A x <= u

P and A are static. A real initSolver() factorizes them once through osqp_setup.
updateGradient, updateLowerBound, updateUpperBound, and updateBounds change
only q, l, and u. If P or A change, the workspace is stale: clearSolver(),
then initSolver().

solve() returns false unless status_val is exactly Solved. Solved-inaccurate
is a failure in that wrapper even if a point was returned.
clearSolverVariables() zeros primal and dual iterates only on the pre-v1 path.
Under OSQP_EIGEN_OSQP_IS_V1 that function returns true and clears nothing.

This module does not call OSQP.
"""

from __future__ import annotations


def ade_polynomials() -> dict[str, str]:
    """Du Val / rational double points in C^3. Standard forms, not fitted."""
    return {
        "A_n": "z^2 + x^2 + y^{n+1}",
        "D_n (n>=4)": "z^2 + y(x^2 + y^{n-2})",
        "E6": "z^2 + x^3 + y^4",
        "E7": "z^2 + x(x^2 + y^3)",
        "E8": "z^2 + x^3 + y^5",
    }


def arithmetic_example() -> dict[str, str]:
    return {
        "congruence": "y^2 + x^3 - x^2 ≡ 0 (mod p)",
        "figure": "y^2 + x^3 - x^2 ≡ 0 (mod 5)",
    }


def regularity() -> dict[str, str]:
    return {
        "local": (
            "A Noetherian local ring S with maximal ideal n is regular if a "
            "regular sequence y_1..y_m generates n."
        ),
        "ring": (
            "A Noetherian ring R is regular if R_m is regular for every "
            "maximal ideal m."
        ),
        "smooth_iff": (
            "A hypersurface f=0 in C^n is smooth iff C[x_1..x_n]/(f) is regular."
        ),
    }


def static_qp() -> dict[str, str]:
    return {
        "program": "min 1/2 x^T P x + q^T x s.t. l <= A x <= u",
        "static": "P, A factorized once",
        "warm_start": "q, l, u only",
        "stale_when": "P or A change",
        "solve_accepts": "status Solved only",
        "osqp_called": "false",
    }


def suite() -> dict[str, object]:
    return {
        "ade": ade_polynomials(),
        "arithmetic": arithmetic_example(),
        "regularity": regularity(),
        "qp": static_qp(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(suite(), indent=2))
