# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""JAX two-ball TOI step. Same kinematics as pythonIDE/toi_step.py.

State s = [p1x, p1y, p2x, p2y, v1x, v1y, v2x, v2y]
Control u = [ux, uy] on ball 1. Masses = 1. Radius R = 0.2. Elastic equal-mass.
No uvicorn. No MCP fill.

Time of impact (TOI) includes acceleration
------------------------------------------
Over one interval the integrator moves the balls as
    p1(t) = p1 + v1 t + 1/2 a1 t^2,  a1 = u / MASS
    p2(t) = p2 + v2 t               (a2 = 0: no gravity, no control on ball 2)
so the relative position is r(t) = rel_p + rel_v t + 1/2 rel_a t^2 with
rel_a = a2 - a1. Contact is |r(t)| = 2R.

Earlier versions solved the TOI from start-of-interval velocity only (rel_a
ignored). That TOI disagreed with the positions integrate_free actually
produces: a contact inside the step could be predicted after dt, the next
step started already overlapping, and the contact was never registered
(tunnelling). The hit / no-hit switch then sat on a discontinuity, and
autodiff vs finite difference disagreed (test_toi_grad, u_y0 = 3.0).

The TOI is now:
  1. Initial guess: the gap along the start-of-interval line of centres,
     d(t) = d0 + v_n t + 1/2 a_n t^2, smallest root in (0, dt], solved with the
     numerically stable quadratic form (q = -1/2 (b + sign(b) sqrt(disc));
     roots q/a, c/q); a_n ~ 0 falls back to the linear root; disc < 0 means no
     root.
  2. Refinement on the exact contact function f(t) = |r(t)|^2 - (2R)^2 with a
     bracketed (Newton + bisection) iteration, so tau matches the integrated
     trajectory, including tangential motion.
  3. One final Newton step taken from the stop-gradient root with the live
     inputs. Its value equals the root; its derivative is the implicit-function
     derivative d tau = -f_theta / f_t.
A hit requires the balls to be separated at the start of the step and either
f(dt) <= 0 (the trajectory ends overlapping, so a root must exist), or a
converged root with f'(tau) < 0 (an entering contact that exits again within
the step). A grazing contact (f'(tau) ~ 0) is not a hit; its impulse would
be ~0 anyway. Every division goes through a jnp.where-safe denominator, so the
gradients are NaN-free.
"""
from __future__ import annotations

import jax
import jax.numpy as jnp
from jax import jit, lax

R = 0.2
DIAM2 = (2.0 * R) ** 2
MASS = 1.0
EPS = 1e-12
NEWTON_ITERS = 32           # bracketed refinement iterations (value only)
RESIDUAL_TOL = 1e-4 * DIAM2  # |f(tau)| tolerance for a converged root
GRAZE_EPS = 1e-9            # |f'(tau)| below this counts as grazing


def split(s):
    return s[0:2], s[2:4], s[4:6], s[6:8]


def pack(p1, p2, v1, v2):
    return jnp.concatenate([p1, p2, v1, v2])


def integrate_free(p1, p2, v1, v2, u, t):
    a1 = u / MASS
    p1n = p1 + v1 * t + 0.5 * a1 * t * t
    p2n = p2 + v2 * t
    v1n = v1 + a1 * t
    return p1n, p2n, v1n, v2


def _safe_den(x):
    """Denominator that is never ~0 (sign kept); pair with a jnp.where mask."""
    return jnp.where(jnp.abs(x) > EPS, x, jnp.where(x < 0, -1.0, 1.0))


def _contact_fn(t, rel_p, rel_v, rel_a):
    """f(t) = |r(t)|^2 - (2R)^2 and f'(t), with r(t) from the integrator."""
    r = rel_p + rel_v * t + 0.5 * rel_a * t * t
    rd = rel_v + rel_a * t
    return jnp.dot(r, r) - DIAM2, 2.0 * jnp.dot(r, rd)


def _smallest_root_in(a, b, c, dt):
    """Smallest root of a t^2 + b t + c in (0, dt], else dt (stable form)."""
    big = dt + 1.0
    # linear fallback (a ~ 0)
    lin_ok = jnp.abs(b) > EPS
    t_lin = jnp.where(lin_ok, -c / _safe_den(b), big)
    t_lin = jnp.where(t_lin > 0.0, t_lin, big)
    # quadratic, numerically stable
    disc = b * b - 4.0 * a * c
    disc_ok = disc >= 0.0
    sq = jnp.where(disc_ok, jnp.sqrt(jnp.where(disc_ok, disc, 0.0)), 0.0)
    sgn = jnp.where(b >= 0.0, 1.0, -1.0)
    q = -0.5 * (b + sgn * sq)
    r1 = jnp.where(jnp.abs(a) > EPS, q / _safe_den(a), big)
    r2 = jnp.where(jnp.abs(q) > EPS, c / _safe_den(q), big)
    r1 = jnp.where(r1 > 0.0, r1, big)
    r2 = jnp.where(r2 > 0.0, r2, big)
    t_quad = jnp.where(disc_ok, jnp.minimum(r1, r2), big)
    t = jnp.where(jnp.abs(a) > EPS, t_quad, t_lin)
    return jnp.where(t <= dt, t, dt)


def _solve_toi_value(rel_p, rel_v, rel_a, dt):
    """Value-only TOI search (no gradient flows through this)."""
    d0 = jnp.sqrt(jnp.dot(rel_p, rel_p))
    n0 = rel_p / _safe_den(d0)
    guess = _smallest_root_in(
        0.5 * jnp.dot(n0, rel_a), jnp.dot(n0, rel_v), d0 - 2.0 * R, dt
    )
    f0, _ = _contact_fn(0.0 * dt, rel_p, rel_v, rel_a)
    fdt, _ = _contact_fn(dt, rel_p, rel_v, rel_a)
    bracket = (f0 > 0.0) & (fdt <= 0.0)

    def body(_, carry):
        t, lo, hi = carry
        fv, fp = _contact_fn(t, rel_p, rel_v, rel_a)
        lo = jnp.where(bracket & (fv > 0.0), t, lo)
        hi = jnp.where(bracket & (fv <= 0.0), t, hi)
        t_n = t - fv / _safe_den(fp)
        inside = (t_n > lo) & (t_n < hi) & (jnp.abs(fp) > EPS)
        t_b = jnp.where(inside, t_n, 0.5 * (lo + hi))
        t_free = jnp.clip(jnp.where(jnp.abs(fp) > EPS, t_n, t), 0.0, dt)
        return jnp.where(bracket, t_b, t_free), lo, hi

    zero = 0.0 * dt
    t, _, _ = lax.fori_loop(0, NEWTON_ITERS, body, (guess, zero, zero + dt))
    fv, fp = _contact_fn(t, rel_p, rel_v, rel_a)
    entering = (jnp.abs(fv) <= RESIDUAL_TOL) & (fp < -GRAZE_EPS)
    hit = (f0 > 0.0) & (t > 0.0) & (t <= dt) & (bracket | entering)
    return t, hit


def sphere_sphere_toi(p1, p2, v1, v2, dt, u=None):
    """Smallest t in (0, dt] with |p2(t) - p1(t)| = 2R under the integrator.

    u is the control on ball 1 (acceleration u / MASS); u=None means no
    acceleration (the previous behaviour for unforced balls).
    Returns (tau, hit, n): tau = dt when there is no hit; n is the unit
    normal from ball 1 to ball 2 at the contact positions.
    """
    rel_p = p2 - p1
    rel_v = v2 - v1
    a1 = jnp.zeros_like(v1) if u is None else u / MASS
    rel_a = jnp.zeros_like(v2) - a1          # a2 = 0
    sg = jax.lax.stop_gradient
    t_sg, hit = _solve_toi_value(sg(rel_p), sg(rel_v), sg(rel_a), sg(dt))
    # implicit-function step: value == root, derivative == -f_theta / f_t
    fv, fp = _contact_fn(t_sg, rel_p, rel_v, rel_a)
    fp_ok = jnp.abs(fp) > EPS
    t_hit = jnp.where(fp_ok, t_sg - fv / _safe_den(fp), t_sg)
    tau = jnp.where(hit, jnp.clip(t_hit, 0.0, dt), dt)
    r_imp = rel_p + tau * rel_v + 0.5 * rel_a * tau * tau
    n = r_imp / (jnp.linalg.norm(r_imp) + EPS)
    return tau, hit, n


def elastic_reset(v1, v2, n):
    j = jnp.dot(v1 - v2, n)
    return v1 - j * n, v2 + j * n


@jit
def step_with_toi(s, u, dt):
    p1, p2, v1, v2 = split(s)
    tau, hit, n = sphere_sphere_toi(p1, p2, v1, v2, dt, u)
    p1m, p2m, v1m, v2m = integrate_free(p1, p2, v1, v2, u, tau)
    v1p, v2p = elastic_reset(v1m, v2m, n)
    rem = jnp.maximum(dt - tau, 0.0)
    p1h, p2h, v1h, v2h = integrate_free(p1m, p2m, v1p, v2p, u, rem)
    s_hit = pack(p1h, p2h, v1h, v2h)
    p1f, p2f, v1f, v2f = integrate_free(p1, p2, v1, v2, u, dt)
    s_free = pack(p1f, p2f, v1f, v2f)
    s_next = jnp.where(hit, s_hit, s_free)
    s_minus = pack(p1m, p2m, v1m, v2m)
    s_plus = pack(p1m, p2m, v1p, v2p)
    return s_next, tau, hit, s_minus, s_plus
