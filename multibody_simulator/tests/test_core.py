"""
Tests for core module: RigidBody, MultibodySystem.
"""

import pytest
import jax.numpy as jnp
from multibody_simulator.core import RigidBody, MultibodySystem


def test_rigid_body_creation():
    """Test RigidBody dataclass instantiation."""
    body = RigidBody(mass=1.0, inertia=jnp.eye(3), shape="sphere", radius=0.2)
    assert body.mass == 1.0
    assert body.shape == "sphere"
    assert body.radius == 0.2


def test_multibody_system_creation():
    """Test MultibodySystem instantiation."""
    bodies = [
        RigidBody(mass=1.0, inertia=jnp.eye(3), radius=0.2),
        RigidBody(mass=1.0, inertia=jnp.eye(3), radius=0.2),
    ]
    joint_parents = [-1, -1]
    joint_types = ["free", "free"]
    joint_axes = [jnp.array([0.0, 0.0, 0.0]), jnp.array([0.0, 0.0, 0.0])]

    sys = MultibodySystem(bodies, joint_parents, joint_types, joint_axes)
    assert sys.n_bodies == 2
    assert sys.n_joints == 0
    assert sys.n_q == 6


def test_get_pose():
    """Test pose extraction from state vector."""
    bodies = [RigidBody(mass=1.0, inertia=jnp.eye(3))]
    sys = MultibodySystem(bodies, [-1], ["free"], [jnp.array([0.0, 0.0, 0.0])])

    q = jnp.array([0.0, 1.0, 2.0, 0.1, 0.2, 0.3])
    joint_q, base_pos, base_orient = sys.get_pose(q)

    assert joint_q.shape == (0,)
    assert base_pos.shape == (3,)
    assert base_orient.shape == (3,)
