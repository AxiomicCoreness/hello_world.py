# ADE extract and static QP

Same note on both trees. The multibody package on hello_world.py is not replaced.

## Quadratic program

$$\min_x \tfrac12 x^\top P x + q^\top x \quad\text{subject to}\quad l \le Ax \le u.$$

\(P\) and \(A\) are static and factorized once. Warm start updates \(q\), \(l\), and \(u\). If \(P\) or \(A\) change, clear the solver and initialize again. `solve()` accepts only exact Solved. `clearSolverVariables()` zeros iterates only on the pre-v1 path.

OSQP is not called. The Eigen wrapper is not vendored.

## Du Val polynomials

These are the standard rational double points in \(\mathbb{C}^3\), recorded from the supplied extract.

- \(A_n\): \(z^2 + x^2 + y^{n+1}\)
- \(D_n\) (\(n\ge 4\)): \(z^2 + y(x^2 + y^{n-2})\)
- \(E_6\): \(z^2 + x^3 + y^4\)
- \(E_7\): \(z^2 + x(x^2 + y^3)\)
- \(E_8\): \(z^2 + x^3 + y^5\)

Congruence example: \(y^2 + x^3 - x^2 \equiv 0 \pmod 5\).

A hypersurface \(f=0\) in \(\mathbb{C}^n\) is smooth if and only if \(\mathbb{C}[x_1,\ldots,x_n]/(f)\) is regular. That is the stated equivalence, not a computation performed here.
