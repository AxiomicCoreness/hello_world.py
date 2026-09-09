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
    assert float(tau) == 0.05


if __name__ == "__main__":
    test_head_on_swap()
    test_no_hit_short_dt()
    print("Test passed.")
