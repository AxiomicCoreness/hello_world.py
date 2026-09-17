"""Collision detection, TOI, and impulse resolution."""

import jax.numpy as jnp
from jax import jit, lax
from .core import MultibodySystem


def detect_collisions(sys: MultibodySystem, q: jnp.ndarray, qd: jnp.ndarray, dt: float):
    """
    Detect collisions and compute Time‑of‑Impact (TOI) for each.
    Returns list of (body_i, body_j, toi, contact_normal, contact_point).
    """
    # For two spheres: distance = norm(pos_i - pos_j) - (r_i + r_j)
    # TOI is when distance crosses zero.
    collisions = []
    for i in range(sys.n_bodies):
        for j in range(i+1, sys.n_bodies):
            # Get positions from q (simplified)
            # In real impl, use forward kinematics.
            pos_i = jnp.array([q[0], q[1], q[2]])  # placeholder
            pos_j = jnp.array([q[3], q[4], q[5]])
            rad_sum = sys.bodies[i].radius + sys.bodies[j].radius
            rel_pos = pos_i - pos_j
            dist = jnp.linalg.norm(rel_pos)
            if dist < rad_sum:
                # Collision detected. Compute TOI assuming linear motion.
                # Simplified: assume constant velocity over dt.
                vel_i = jnp.array([qd[0], qd[1], qd[2]])  # placeholder
                vel_j = jnp.array([qd[3], qd[4], qd[5]])
                rel_vel = vel_i - vel_j
                # Solve: |pos_i0 - pos_j0 + rel_vel * t| = rad_sum
                a = jnp.dot(rel_vel, rel_vel)
                b = 2 * jnp.dot(rel_pos, rel_vel)
                c = jnp.dot(rel_pos, rel_pos) - rad_sum**2
                disc = b**2 - 4*a*c
                toi = 0.0
                if disc >= 0:
                    t1 = (-b - jnp.sqrt(disc)) / (2*a)
                    t2 = (-b + jnp.sqrt(disc)) / (2*a)
                    # choose smallest positive within [0, dt]
                    t = jnp.where((t1 > 0) & (t1 < dt), t1, t2)
                    toi = jnp.where((t > 0) & (t < dt), t, dt)
                else:
                    toi = dt
                normal = rel_pos / (dist + 1e-10)
                collisions.append((i, j, toi, normal, pos_i + vel_i * toi))
    return collisions


def resolve_impulse(sys: MultibodySystem, q: jnp.ndarray, qd: jnp.ndarray,
                    collision: tuple) -> jnp.ndarray:
    """
    Apply impulse for a single collision using LCP-like resolution.
    Returns updated qd.
    """
    i, j, toi, normal, contact_point = collision
    # Simplified: perfectly elastic collision between two spheres.
    m_i = sys.bodies[i].mass
    m_j = sys.bodies[j].mass
    v_i = jnp.array([qd[0], qd[1], qd[2]])  # placeholder
    v_j = jnp.array([qd[3], qd[4], qd[5]])
    rel_v = v_i - v_j
    vn = jnp.dot(rel_v, normal)
    if vn > 0:  # moving apart, no impulse
        return qd
    impulse_mag = -(1 + 1.0) * vn / (1/m_i + 1/m_j)  # e=1
    impulse = impulse_mag * normal
    v_i_new = v_i + impulse / m_i
    v_j_new = v_j - impulse / m_j
    qd_new = qd.at[0:3].set(v_i_new)
    qd_new = qd_new.at[3:6].set(v_j_new)
    return qd_new
