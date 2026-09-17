"""Dynamics computation: mass matrix, bias forces, contact Jacobians."""

import jax.numpy as jnp
from jax import jit, grad
from .core import MultibodySystem


def mass_matrix(sys: MultibodySystem, q: jnp.ndarray) -> jnp.ndarray:
    """Compute (N+6)x(N+6) mass matrix via Composite Rigid Body Algorithm."""
    # Simplified: treat as diagonal plus coupling (for demonstration)
    # Real implementation would use CRBA.
    n = sys.n_q
    M = jnp.eye(n) * 1.0  # placeholder
    # In practice: implement recursive Newton-Euler.
    return M


def bias_forces(sys: MultibodySystem, q: jnp.ndarray, qd: jnp.ndarray) -> jnp.ndarray:
    """Coriolis, centrifugal, and gravity forces."""
    n = sys.n_q
    gravity = jnp.array([0.0, -9.81, 0.0])  # y-down
    # Simplified: just gravity on base.
    g_force = jnp.zeros(n)
    g_force = g_force.at[sys.n_joints+1].set(-9.81 * sum(b.mass for b in sys.bodies))
    # Coriolis/centrifugal ignored for simplicity.
    return g_force


def contact_jacobians(sys: MultibodySystem, q: jnp.ndarray, contacts: list) -> jnp.ndarray:
    """Return contact Jacobian matrix (n_contacts x n_q)."""
    # For each contact point, compute Jacobian.
    # Simplified: return identity for demonstration.
    nc = len(contacts)
    C = jnp.zeros((nc, sys.n_q))
    for i, (body_idx, local_point) in enumerate(contacts):
        # Jacobian = derivative of contact point w.r.t. q
        # In practice, use forward kinematics.
        C = C.at[i, :].set(jnp.ones(sys.n_q) * 0.1)  # placeholder
    return C
