"""TOI‑Velocity gradient correction for exact collision differentiation."""

import jax.numpy as jnp
from jax import jit, grad, vjp


def toi_velocity_correction(qd, collisions, dt):
    """
    Compute corrected velocity after collisions, ensuring gradients through TOI.
    This is a placeholder that simply returns qd; the real implementation
    would compute gradients of TOI w.r.t. state.
    """
    # In practice, we would compute the Jacobian of the collision time
    # and apply the correction as in the TOI‑Velocity paper.
    # For now, return unchanged.
    return qd
