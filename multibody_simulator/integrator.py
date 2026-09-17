"""Integrator with TOI‑Velocity step."""

import jax.numpy as jnp
from jax import jit, grad
from .dynamics import mass_matrix, bias_forces
from .collision import detect_collisions, resolve_impulse
from .toi_velocity import toi_velocity_correction


def step(sys, q, qd, u, dt):
    """
    Single integration step with collision handling and TOI‑Velocity correction.
    Returns new state (q_next, qd_next).
    """
    # 1. Compute dynamics without contact
    M = mass_matrix(sys, q)
    bias = bias_forces(sys, q, qd)
    # Generalized forces: joint torques + base zero
    tau = jnp.zeros(sys.n_q)
    tau = tau.at[:sys.n_joints].set(u)  # only joints actuated
    qdd = jnp.linalg.solve(M, tau - bias)

    # 2. Semi‑implicit Euler (predict)
    qd_pred = qd + qdd * dt
    q_pred = q + qd_pred * dt

    # 3. Detect collisions along predicted path
    collisions = detect_collisions(sys, q_pred, qd_pred, dt)

    # 4. Apply impulses for each collision (in order of TOI)
    qd_current = qd_pred
    q_current = q_pred
    for col in collisions:
        toi = col[2]
        q_at_toi = q + qd_current * toi  # simplified
        qd_current = resolve_impulse(sys, q_at_toi, qd_current, col)

    # 5. TOI‑Velocity correction (gradient correction)
    qd_corrected = toi_velocity_correction(qd_current, collisions, dt)

    # 6. Final position update
    q_next = q_current + qd_corrected * (dt - collisions[-1][2] if collisions else dt)

    return q_next, qd_corrected
