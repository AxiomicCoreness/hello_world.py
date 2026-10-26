# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Head-on TOI + elastic swap."""
import jax.numpy as jnp
from multibody_simulator.two_ball_toi import step_with_toi, R


def test_head_on_swap():
    # ball1 at 0 moving +x, ball2 at 1 at rest; R=0.2 so gap 0.6
    s = jnp.array([0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0])
    u = jnp.array([0.0, 0.0])
    s1, tau, hit, _, s_plus = step_with_toi(s, u, 1.0)
    assert bool(hit)
    assert abs(float(tau) - 0.6) < 1e-6
    v1 = s_plus[4:6]
    v2 = s_plus[6:8]
    assert abs(float(v1[0])) < 1e-6
    assert abs(float(v2[0]) - 1.0) < 1e-6


def test_no_hit_short_dt():
    s = jnp.array([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0])
    u = jnp.array([0.0, 3.0])
    _, tau, hit, _, _ = step_with_toi(s, u, 0.05)
    assert not bool(hit)
    # No hit => tau is exactly dt, in tau's own dtype. JAX defaults to float32,
    # so float(tau) is float32(0.05) = 0.05000000074505806, never the Python
    # double 0.05. Compare exactly against dt cast to the same dtype.
    assert tau.dtype == jnp.asarray(0.05).dtype
    assert bool(tau == jnp.asarray(0.05, dtype=tau.dtype))


if __name__ == "__main__":
    test_head_on_swap()
    test_no_hit_short_dt()
    print("Test passed.")


def _brute_force_toi(s, u, dt, h=1e-5):
    """First contact time from fine-step integration (float64 numpy).

    Steps the same constant-acceleration kinematics as integrate_free in
    substeps of h and returns the first substep end with |p2 - p1| <= 2R,
    or None if the balls never touch within dt.
    """
    import numpy as np

    s = np.asarray(s, dtype=np.float64)
    a1 = np.asarray(u, dtype=np.float64)  # MASS = 1
    p1, p2, v1, v2 = s[0:2].copy(), s[2:4].copy(), s[4:6].copy(), s[6:8].copy()
    steps = int(round(dt / h))
    for k in range(1, steps + 1):
        p1 = p1 + v1 * h + 0.5 * a1 * h * h
        v1 = v1 + a1 * h
        p2 = p2 + v2 * h
        if np.linalg.norm(p2 - p1) <= 2.0 * R:
            return k * h
    return None


def test_toi_matches_brute_force():
    h = 1e-5
    cases = [
        # head-on, constant velocity (no acceleration)
        ([0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0], [0.0, 0.0], 1.0),
        # relative rest, contact only through acceleration
        ([0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0], [2.0, 0.0], 0.5),
        # oblique approach with acceleration (tangential motion)
        ([0.0, 0.0, 0.6, 0.25, 0.2, 0.0, 0.0, 0.0], [3.0, 1.0], 0.5),
        # test_toi_grad step 18: start-of-interval velocity alone predicts
        # contact at exactly dt; the accelerated trajectory touches earlier
        ([-1.0, -1.46, -1.0, -1.0, 0.0, 1.8, 0.0, 0.0], [0.0, 3.0], 0.8 / 24),
        # miss: passes by with clearance > 2R
        ([0.0, 0.0, 1.0, 0.5, 1.0, 0.0, 0.0, 0.0], [0.0, 0.0], 1.5),
    ]
    for s, u, dt in cases:
        _, tau, hit, _, _ = step_with_toi(jnp.array(s), jnp.array(u), dt)
        bf = _brute_force_toi(s, u, dt, h)
        if bf is None:
            assert not bool(hit), (s, u, dt)
            assert bool(tau == jnp.asarray(dt, dtype=tau.dtype))
        else:
            assert bool(hit), (s, u, dt, bf)
            assert bf - h - 1e-6 <= float(tau) <= bf + 1e-6, (s, u, dt, float(tau), bf)
