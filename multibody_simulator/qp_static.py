"""Static quadratic-program split for the existing multibody step.

Does not replace dynamics.py, integrator.py, or toi_velocity.py.
Does not vendor OsqpEigen. The wrapper remains Giulio Romualdi, BSD 3-Clause.

The program is

    min_x  1/2 x^T P x + q^T x
    subject to  l <= A x <= u

P and A are the static part. A real initSolver() would factorize them once.
updateGradient / updateLowerBound / updateUpperBound / updateBounds then
change only q, l, and u. If P or A change, the factorization is stale.

In this package that split is not implemented:

- mass_matrix returns eye(n_q). That is a placeholder, not CRBA.
- contact_jacobians returns a constant row. That is not a kinematic Jacobian.
- toi_velocity_correction returns qd unchanged.
- step() solves M qdd = tau - bias with that identity M. It does not call OSQP.
- solve() in the OsqpEigen wrapper accepts only status Solved. This file does
  not call that wrapper.

Ledger index 9212 in the package README is a label. This module computes no seal.
"""

from __future__ import annotations


def static_split() -> dict[str, str]:
    return {
        "program": "min 1/2 x^T P x + q^T x s.t. l <= A x <= u",
        "static": "P, A factorized once",
        "warm_start": "q, l, u updated",
        "stale_when": "P or A change",
        "this_package": "identity mass matrix; TOI correction is the identity",
        "osqp": "not called",
        "ledger_9212": "label in README, not a computed digest",
    }
