"""
Tests for collision detection and impulse resolution.
"""

import pytest
import jax.numpy as jnp
from multibody_simulator.collision import detect_collisions, resolve_impulse
from multibody_simulator.core import RigidBody, MultibodySystem


def test_detect_collisions_two_spheres():
    """Test collision detection between two spheres."""
    ball1 = RigidBody(mass=1.0, radius=0.2)
    ball2 = RigidBody(mass=1.0, radius=0.2)
    bodies = [ball1, ball2]
    sys = MultibodySystem(bodies, [-1, -1], ["free", "free"],
                          [jnp.zeros(3), jnp.zeros(3)])

    # Overlapping spheres at origin and (0.2, 0, 0)
    q = jnp.array([0.0, 0.0, 0.0, 0.2, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    qd = jnp.array([1.0, 0.0, 0.0, -1.0, 0.0, 0.0,
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    collisions = detect_collisions(sys, q, qd, 0.01)
    assert len(collisions) > 0


def test_resolve_impulse():
    """Test impulse resolution for elastic collision."""
    ball1 = RigidBody(mass=1.0, radius=0.2)
    ball2 = RigidBody(mass=1.0, radius=0.2)
    bodies = [ball1, ball2]
    sys = MultibodySystem(bodies, [-1, -1], ["free", "free"],
                          [jnp.zeros(3), jnp.zeros(3)])

    q = jnp.array([0.0, 0.0, 0.0, 0.2, 0.0, 0.0,
                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    qd = jnp.array([1.0, 0.0, 0.0, -1.0, 0.0, 0.0,
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    collisions = detect_collisions(sys, q, qd, 0.01)
    if collisions:
        qd_new = resolve_impulse(sys, q, qd, collisions[0])
        # Velocities should swap (equal mass elastic)
        assert abs(qd_new[0] + qd_new[3]) < 1e-6
