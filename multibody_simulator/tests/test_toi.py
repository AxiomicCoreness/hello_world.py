"""Test TOI detection and impulse resolution."""

import jax.numpy as jnp
from multibody_simulator import detect_collisions, resolve_impulse
from multibody_simulator.core import RigidBody, MultibodySystem


def test_two_spheres():
    ball1 = RigidBody(mass=1.0, radius=0.2)
    ball2 = RigidBody(mass=1.0, radius=0.2)
    bodies = [ball1, ball2]
    sys = MultibodySystem(bodies, [-1, -1], ["free", "free"], [jnp.zeros(3), jnp.zeros(3)])
    # Set positions: overlapping
    q = jnp.array([0.0, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # dummy
    qd = jnp.array([1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # velocities
    collisions = detect_collisions(sys, q, qd, 0.01)
    assert len(collisions) > 0
    # Resolve impulse
    qd_new = resolve_impulse(sys, q, qd, collisions[0])
    # Velocities should have swapped: elastic collision equal masses
    # Simplified: check that signs reversed
    assert qd_new[0] == -1.0
    assert qd_new[3] == 1.0
    print("Test passed.")
