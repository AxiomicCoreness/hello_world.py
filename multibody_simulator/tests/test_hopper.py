"""
Tests for hopper TOI-Velocity implementation.
"""

import pytest
import jax.numpy as jnp
from multibody_simulator.hopper_toi import (
    step_hopper, find_toi, G, E, EPS, PHI, loss_hopper
)


def test_constants():
    """Verify sovereign constants."""
    assert G == 9.81
    assert E == 0.8
    assert EPS == 1e-12
    assert abs(PHI - 1.618033988749895) < 1e-10


def test_find_toi_no_collision():
    """Test TOI when no collision occurs in step."""
    h, v, u, dt = 1.0, 0.0, 4.0, 0.02  # u < G, but dt too short
    tau, hit = find_toi(h, v, u, dt)
    assert not hit
    assert tau == dt


def test_find_toi_collision():
    """Test TOI when collision occurs."""
    h, v, u, dt = 1.0, 0.0, 4.0, 0.5  # dt long enough for impact
    tau, hit = find_toi(h, v, u, dt)
    assert hit
    assert 0.0 < tau < dt


def test_step_hopper_no_collision():
    """Test hopper step without collision."""
    s = jnp.array([1.0, 0.0])
    u = 4.0
    dt = 0.02

    s_next, tau, hit, info = step_hopper(s, u, dt)
    assert not hit
    assert tau == dt
    assert s_next[0] > 0.0


def test_step_hopper_collision():
    """Test hopper step with collision."""
    s = jnp.array([1.0, 0.0])
    u = 4.0
    dt = 0.5

    s_next, tau, hit, info = step_hopper(s, u, dt)
    assert hit
    assert 0.0 < tau < dt
    assert s_next[0] >= 0.0


def test_step_hopper_elastic_bounce():
    """Test elastic bounce with e=0.8."""
    # Just above ground, moving downward
    s = jnp.array([0.01, -1.0])
    u = 0.0
    dt = 0.1

    s_next, tau, hit, info = step_hopper(s, u, dt, e=0.8)
    assert hit
    # After bounce, velocity should be positive (upward)
    # v+ = -0.8 * v- = 0.8
    assert s_next[1] > 0.0


def test_loss_hopper():
    """Test loss function for hopper optimization."""
    n = 80
    dt = 0.02
    s0 = jnp.array([1.0, 0.0])
    u_seq = jnp.full((n,), 4.0)

    loss_val, hits = loss_hopper(u_seq, s0, dt, lam=0.01)
    assert loss_val > 0.0
    assert hits >= 0


def test_step_hopper_ground_never_negative():
    """Test that height never goes negative."""
    s = jnp.array([0.5, -2.0])  # Heading down fast
    u = 0.0
    dt = 0.5

    s_next, tau, hit, info = step_hopper(s, u, dt)
    assert s_next[0] >= 0.0
