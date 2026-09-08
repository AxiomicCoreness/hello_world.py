"""JAX two-ball TOI step. Same kinematics as pythonIDE/toi_step.py.

State s = [p1x, p1y, p2x, p2y, v1x, v1y, v2x, v2y]
Control u = [ux, uy] on ball 1. Masses = 1. Radius R = 0.2. Elastic equal-mass.
No uvicorn. No MCP fill.
"""
from __future__ import annotations

import jax.numpy as jnp
from jax import jit

R = 0.2
DIAM2 = (2.0 * R) ** 2
MASS = 1.0
EPS = 1e-12


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


def sphere_sphere_toi(p1, p2, v1, v2, dt):
    rel_p = p2 - p1
    rel_v = v2 - v1
    aa = jnp.dot(rel_v, rel_v)
    bb = 2.0 * jnp.dot(rel_p, rel_v)
    cc = jnp.dot(rel_p, rel_p) - DIAM2
    disc = bb * bb - 4.0 * aa * cc
    sqrt_disc = jnp.sqrt(jnp.maximum(disc, 0.0) + EPS)
    t_lin = jnp.where(jnp.abs(aa) > EPS, (-bb - sqrt_disc) / (2.0 * aa + EPS), dt + 1.0)
    approaching = jnp.dot(rel_p, rel_v) < -EPS
    hit = approaching & (disc > EPS) & (t_lin > EPS) & (t_lin <= dt)
    tau = jnp.where(hit, t_lin, dt)
    r_imp = rel_p + tau * rel_v
    n = r_imp / (jnp.linalg.norm(r_imp) + EPS)
    return tau, hit, n


def elastic_reset(v1, v2, n):
    j = jnp.dot(v1 - v2, n)
    return v1 - j * n, v2 + j * n


@jit
def step_with_toi(s, u, dt):
    p1, p2, v1, v2 = split(s)
    tau, hit, n = sphere_sphere_toi(p1, p2, v1, v2, dt)
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
