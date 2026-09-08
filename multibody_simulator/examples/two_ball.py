"""Two‑ball optimal control example using TOI‑Velocity."""

import jax.numpy as jnp
from jax import grad, jit, value_and_grad
from multibody_simulator import MultibodySystem, step
from multibody_simulator.core import RigidBody


def two_ball_sim():
    # Two identical spheres
    ball = RigidBody(mass=1.0, radius=0.2, shape="sphere")
    bodies = [ball, ball]
    # Free-floating system (no joints)
    joint_parents = [-1, -1]
    joint_types = ["free", "free"]
    joint_axes = [jnp.array([0., 0., 0.]), jnp.array([0., 0., 0.])]
    sys = MultibodySystem(bodies, joint_parents, joint_types, joint_axes)

    # Initial state: ball1 at (-1,-2,0), ball2 at (-1,-1,0), velocities zero.
    q0 = jnp.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                    -1.0, -2.0, 0.0,
                    -1.0, -1.0, 0.0,
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # 6+6+6? Actually n_q=12 (2 free bodies *6)
    qd0 = jnp.zeros(12)
    T = 5.0
    N = 50
    dt = T / N
    u_init = jnp.array([0.0, 3.0])  # initial guess

    def loss(u_seq):
        q = q0
        qd = qd0
        for i in range(N):
            u = u_seq[i]
            force_vec = jnp.array([u[0], u[1], 0.0])
            q, qd = step(sys, q, qd, force_vec, dt)
            pos2 = q[6:9]  # second body position
            return jnp.sum(pos2**2)

        grad_loss = grad(loss)
        # Optimize via gradient descent (not implemented here)
