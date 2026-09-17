"""Rigid body and multibody system definitions."""

import jax.numpy as jnp
from jax import jit
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class RigidBody:
    mass: float
    inertia: jnp.ndarray  # 3x3 inertia tensor (world-aligned for simplicity)
    shape: str = "sphere"  # "sphere", "box", etc.
    radius: float = 0.2  # for spheres
    half_extents: Tuple[float, float, float] = (0.1, 0.1, 0.1)  # for boxes


class MultibodySystem:
    """Tree of rigid bodies connected by joints (floating base + joints)."""

    def __init__(self, bodies: List[RigidBody], joint_parents: List[int],
                 joint_types: List[str], joint_axes: List[jnp.ndarray]):
        """
        Args:
            bodies: list of RigidBody objects.
            joint_parents: parent body index for each joint; -1 for base.
            joint_types: 'free' (for base) or 'revolute' / 'prismatic'.
            joint_axes: joint axis (for revolute/prismatic).
        """
        self.bodies = bodies
        self.n_bodies = len(bodies)
        self.joint_parents = joint_parents
        self.joint_types = joint_types
        self.joint_axes = joint_axes
        self.n_joints = sum(1 for t in joint_types if t != 'free')
        self.n_q = self.n_joints + 6  # floating base

    def get_pose(self, q: jnp.ndarray) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """Extract base position and orientation from q."""
        # q = [joint_angles (N), base_position (3), base_orientation (3)]
        # orientation as Euler angles for simplicity (or quaternion)
        n_j = self.n_joints
        joint_q = q[:n_j]
        base_pos = q[n_j:n_j+3]
        base_orient = q[n_j+3:n_j+6]  # Euler ZYX
        return joint_q, base_pos, base_orient
