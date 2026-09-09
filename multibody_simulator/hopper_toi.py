"""1D hopper: height + velocity. Ground TOI is a quadratic root.

s = [h, v], u = upward thrust (scalar). a = u - g.
Guard h=0, reset v+ = -e v-.
"""
from __future__ import annotations

import jax.numpy as jnp
from jax import jit

G = 9.81
E = 0.8
EPS = 1e-12


@jit
def step_hopper(s, u, dt, e=E, g=G):
    h, v = s[0], s[1]
    a = u - g
    # h + v t + 0.5 a t^2 = 0
    aa = 0.5 * a
    bb = v
    cc = h
    disc = bb * bb - 4.0 * aa * cc
    sqrt_d = jnp.sqrt(jnp.maximum(disc, 0.0))
    t1 = jnp.where(jnp.abs(aa) > EPS, (-bb - sqrt_d) / (2.0 * aa + EPS), dt + 1.0)
    t2 = jnp.where(jnp.abs(aa) > EPS, (-bb + sqrt_d) / (2.0 * aa + EPS), dt + 1.0)
    t_pos = jnp.where((t1 > EPS) & (t1 <= dt), t1, jnp.where((t2 > EPS) & (t2 <= dt), t2, dt + 1.0))
    approaching = (h + EPS) > 0.0
    hit = approaching & (t_pos <= dt) & (disc >= -EPS)
    tau = jnp.where(hit, t_pos, dt)
    h_m = h + v * tau + 0.5 * a * tau * tau
    v_m = v + a * tau
    v_p = jnp.where(hit, -e * v_m, v_m)
    rem = jnp.maximum(dt - tau, 0.0)
    h_n = h_m + v_p * rem + 0.5 * a * rem * rem
    v_n = v_p + a * rem
    s_next = jnp.array([h_n, v_n])
    return s_next, tau, hit, jnp.array([h_m, v_m])
