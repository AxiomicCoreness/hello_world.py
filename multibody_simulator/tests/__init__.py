"""
Test suite for Multibody Simulator with TOI-Velocity.
Sovereign test manifest included in test_suite.bon.

Test Coverage:
    - Core: RigidBody, MultibodySystem
    - Dynamics: mass_matrix, bias_forces, contact_jacobians
    - Collision: detect_collisions, resolve_impulse
    - Integrator: step with TOI
    - TOI-Velocity: gradient correction
    - Hopper: 1D TOI with constants G, E, EPS
    - JAX Optimizer: hopper optimization
"""

from pathlib import Path

TEST_ROOT = Path(__file__).parent
BON_FILE = TEST_ROOT / "test_suite.bon"

__all__ = ["TEST_ROOT", "BON_FILE"]
