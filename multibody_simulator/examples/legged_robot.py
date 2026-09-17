"""Simple 3D hopper model (one leg) for flight‑phase testing."""

import jax.numpy as jnp
from multibody_simulator import MultibodySystem, RigidBody


def create_hopper():
    # Base (body)
    body = RigidBody(mass=2.0, inertia=jnp.eye(3)*0.1, shape="box", half_extents=(0.2, 0.1, 0.1))
    # Leg (link)
    leg = RigidBody(mass=0.5, inertia=jnp.eye(3)*0.01, shape="box", half_extents=(0.02, 0.3, 0.02))
    bodies = [body, leg]
    # Joint: body is free, leg is revolute around z-axis at base attachment point
    joint_parents = [-1, 0]  # leg attached to body
    joint_types = ["free", "revolute"]
    joint_axes = [jnp.array([0., 0., 0.]), jnp.array([0., 0., 1.])]
    sys = MultibodySystem(bodies, joint_parents, joint_types, joint_axes)
    return sys
