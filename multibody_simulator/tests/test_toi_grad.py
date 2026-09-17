"""Finite-difference check on dJ/du_y[0] through one TOI-capable rollout."""
import jax
import jax.numpy as jnp
from jax import grad
from multibody_simulator.two_ball_toi import step_with_toi


def rollout(s0, u_seq, dt):
    s = s0
    for u in u_seq:
        s, *_ = step_with_toi(s, u, dt)
    return s


def test_grad_finite_diff():
    s0 = jnp.array([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0])
    n, t = 24, 0.8
    dt = t / n
    u_seq = jnp.tile(jnp.array([0.0, 3.0]), (n, 1))

    def J(uy0):
        u = u_seq.at[0, 1].set(uy0)
        sf = rollout(s0, u, dt)
        p2 = sf[2:4]
        return jnp.dot(p2, p2)

    g = float(grad(J)(3.0))
    eps = 1e-3
    fd = float((J(3.0 + eps) - J(3.0 - eps)) / (2 * eps))
    assert abs(g - fd) < 5e-2 * (1.0 + abs(fd))
