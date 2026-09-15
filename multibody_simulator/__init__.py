"""
Differentiable multibody simulator with TOI‑Velocity.
Sovereign Lattice Integration — Hopper & Two-Ball Support.
"""

from .core import RigidBody, MultibodySystem
from .dynamics import mass_matrix, bias_forces, contact_jacobians
from .collision import detect_collisions, resolve_impulse
from .integrator import step
from .toi_velocity import toi_velocity_correction

# Hopper TOI-Velocity (1D vertical hopper)
from .hopper_toi import step_hopper, find_toi, G, g_const, loss_hopper

# JAX Hopper Optimizer
from .jax_hopper_optimizer import main as optimize_hopper

__all__ = [
    # Core simulator
    "RigidBody",
    "MultibodySystem",
    "mass_matrix",
    "bias_forces",
    "contact_jacobians",
    "detect_collisions",
    "resolve_impulse",
    "step",
    "toi_velocity_correction",
    
    # Hopper TOI (1D)
    "step_hopper",
    "find_toi",
    "G",
    "g_const",
    "loss_hopper",
    
    # JAX Hopper Optimizer
    "optimize_hopper",
]
