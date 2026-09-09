"""
Tests for hopper TOI-Velocity implementation.
"""

import jax.numpy as jnp
from multibody_simulator.hopper_toi import step_hopper, find_toi, G


def test_find_toi():
    """Test TOI detection for vertical hopper."""
    # Falling from 1m with v=0, a=-G
    h, v, a, dt = 1.0, 0.0, -G, 0.1
    gamma, hit = find_toi(h, v, a, dt)

    # Expected: t = sqrt(2h/G) = sqrt(2/9.81) ≈ 0.4515s
    # Since dt=0.1, no impact in this step
    assert not hit
    assert gamma == dt

    # Longer dt to capture impact
    dt_long = 0.5
    gamma, hit = find_toi(h, v, a, dt_long)
    assert hit
    assert 0.45 < gamma < 0.46


def test_step_hopper():
    """Test single hopper step with TOI."""
    s = jnp.array([1.0, 0.0])
    u = 4.0  # below G, so falls
    dt = 0.1

    s_next, gamma, hit, _ = step_hopper(s, u, dt)
    assert not hit
    assert gamma == dt

    # Test collision
    dt_long = 0.5
    s_next, gamma, hit, _ = step_hopper(s, u, dt_long)
    assert hit
    assert gamma > 0.0
    assert s_next[0] >= 0.0


def test_elastic_collision():
    """Test elastic collision at ground."""
    # Just above ground, moving down
    s = jnp.array([0.01, -1.0])
    u = 0.0
    dt = 0.1

    s_next, gamma, hit, _ = step_hopper(s, u, dt)
    assert hit
    # After elastic collision, velocity should be positive (bounce)
    assert s_next[1] > 0.0
