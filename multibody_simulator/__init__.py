"""Differentiable multibody simulator with TOI‑Velocity."""

from .core import RigidBody, MultibodySystem
from .dynamics import mass_matrix, bias_forces, contact_jacobians
from .collision import detect_collisions, resolve_impulse
from .integrator import step
from .toi_velocity import toi_velocity_correction

__all__ = [
    "RigidBody",
    "MultibodySystem",
    "mass_matrix",
    "bias_forces",
    "contact_jacobians",
    "detect_collisions",
    "resolve_impulse",
    "step",
    "toi_velocity_correction",
]
