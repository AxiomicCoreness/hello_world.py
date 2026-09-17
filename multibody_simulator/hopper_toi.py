"""
1D hopper: height + velocity. Ground TOI is a quadratic root.

s = [h, v], u = upward thrust (scalar). a = u - g.
Guard h=0, reset v+ = -e v-.

Sovereign Constants:
    G = 9.81 (gravitational acceleration, m/s²)
    E = 0.8 (coefficient of restitution)
    EPS = 1e-12 (numerical epsilon for root solving)
"""

from __future__ import annotations

import jax.numpy as jnp
from jax import jit

# ─── SOVEREIGN CONSTANTS ──────────────────────────────────────────────
G = 9.81          # gravitational acceleration (m/s²)
E = 0.8           # coefficient of restitution (elasticity)
EPS = 1e-12       # numerical epsilon for root solving
PHI = (1 + 5**0.5) / 2  # golden ratio (sovereign invariant)


@jit
def step_hopper(s, u, dt, e=E, g=G):
    """
    Single hopper step with exact TOI-Velocity collision handling.

    Args:
        s: [h, v] — height (m) and velocity (m/s, positive up)
        u: control input (thrust acceleration, m/s²)
        dt: time step (s)
        e: coefficient of restitution (default: E = 0.8)
        g: gravitational acceleration (default: G = 9.81)

    Returns:
        s_next: [h_next, v_next] — state after step
        tau: time of impact (dt if no impact)
        hit: boolean indicating if impact occurred
        info: [h_m, v_m] — state at impact moment
    """
    h, v = s[0], s[1]
    a = u - g  # net acceleration (thrust - gravity)

    # ─── Quadratic: h + v*t + 0.5*a*t² = 0 ──────────────────────────
    aa = 0.5 * a
    bb = v
    cc = h

    disc = bb * bb - 4.0 * aa * cc
    sqrt_d = jnp.sqrt(jnp.maximum(disc, 0.0))

    # Roots (handle aa ≈ 0 separately)
    denom = 2.0 * aa + EPS
    t1 = jnp.where(jnp.abs(aa) > EPS, (-bb - sqrt_d) / denom, dt + 1.0)
    t2 = jnp.where(jnp.abs(aa) > EPS, (-bb + sqrt_d) / denom, dt + 1.0)

    # Select smallest positive root within [0, dt]
    t_pos = jnp.where(
        (t1 > EPS) & (t1 <= dt),
        t1,
        jnp.where((t2 > EPS) & (t2 <= dt), t2, dt + 1.0)
    )

    # Hit condition: approaching ground, root found, discriminant valid
    approaching = (h + EPS) > 0.0
    hit = approaching & (t_pos <= dt) & (disc >= -EPS)

    # Time of impact (tau = dt if no hit)
    tau = jnp.where(hit, t_pos, dt)

    # ─── State at impact ──────────────────────────────────────────────
    h_m = h + v * tau + 0.5 * a * tau * tau
    v_m = v + a * tau

    # ─── Collision reset (elastic restitution) ──────────────────────
    # v+ = -e * v-  (velocity reversal with damping)
    v_p = jnp.where(hit, -e * v_m, v_m)

    # ─── Propagate remaining time after impact ──────────────────────
    rem = jnp.maximum(dt - tau, 0.0)
    h_n = h_m + v_p * rem + 0.5 * a * rem * rem
    v_n = v_p + a * rem

    # Ensure non-negative height
    h_n = jnp.maximum(h_n, 0.0)

    s_next = jnp.array([h_n, v_n])

    return s_next, tau, hit, jnp.array([h_m, v_m])


@jit
def find_toi(h, v, u, dt, g=G):
    """
    Find time of impact without performing the full step.

    Args:
        h: height (m)
        v: velocity (m/s)
        u: thrust acceleration (m/s²)
        dt: time step (s)
        g: gravitational acceleration (default: G)

    Returns:
        tau: time of impact (dt if no impact)
        hit: boolean indicating if impact will occur
    """
    a = u - g
    aa = 0.5 * a
    bb = v
    cc = h

    disc = bb * bb - 4.0 * aa * cc
    sqrt_d = jnp.sqrt(jnp.maximum(disc, 0.0))

    denom = 2.0 * aa + EPS
    t1 = jnp.where(jnp.abs(aa) > EPS, (-bb - sqrt_d) / denom, dt + 1.0)
    t2 = jnp.where(jnp.abs(aa) > EPS, (-bb + sqrt_d) / denom, dt + 1.0)

    t_pos = jnp.where(
        (t1 > EPS) & (t1 <= dt),
        t1,
        jnp.where((t2 > EPS) & (t2 <= dt), t2, dt + 1.0)
    )

    hit = (t_pos <= dt) & (disc >= -EPS)
    tau = jnp.where(hit, t_pos, dt)

    return tau, hit


@jit
def loss_hopper(u_seq, s0, dt, lam=0.01, g=G, e=E):
    """
    Loss function for hopper optimization.

    Args:
        u_seq: control sequence (N,)
        s0: initial state [h, v]
        dt: time step (s)
        lam: regularization weight
        g: gravitational acceleration
        e: coefficient of restitution

    Returns:
        loss: scalar loss
        hits: number of impacts
    """
    def body(s, u):
        s_next, _, hit, _ = step_hopper(s, u, dt, e=e, g=g)
        return s_next, hit

    s_final, hits = jax.lax.scan(body, s0, u_seq)

    # Terminal cost: target height, minimize velocity
    h_target = 0.2
    loss_val = (s_final[0] - h_target) ** 2 + 0.1 * s_final[1] ** 2
    loss_val += lam * jnp.sum(u_seq * u_seq) * dt

    return loss_val, jnp.sum(hits.astype(jnp.float32))
