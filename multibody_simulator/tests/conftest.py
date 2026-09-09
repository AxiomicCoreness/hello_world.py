"""
Pytest configuration for multibody_simulator tests.
"""

import pytest
import jax.numpy as jnp
import numpy as np

# Sovereign constants
PHI = (1 + 5**0.5) / 2
G = 9.81
E = 0.8
EPS = 1e-12


@pytest.fixture
def phi():
    return PHI


@pytest.fixture
def g_const():
    return G


@pytest.fixture
def e_const():
    return E


@pytest.fixture
def eps_const():
    return EPS


@pytest.fixture
def sample_state_2d():
    """Sample state for two-ball simulation."""
    return jnp.array([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0])


@pytest.fixture
def sample_state_hopper():
    """Sample state for hopper simulation."""
    return jnp.array([1.0, 0.0])


@pytest.fixture
def sample_control_2d():
    """Sample control for two-ball simulation."""
    return jnp.array([0.0, 3.0])


@pytest.fixture
def sample_control_hopper():
    """Sample control for hopper simulation."""
    return jnp.array(4.0)


@pytest.fixture
def dt_small():
    return 0.02


@pytest.fixture
def dt_large():
    return 0.5
