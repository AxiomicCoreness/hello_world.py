"""Two-ball forward + gradient smoke for JAX TOI."""
from __future__ import annotations

import jax.numpy as jnp
from jax import grad

from multibody_simulator.two_ball_toi import step_with_toi


def rollout(s0, u_seq, dt):
    s = s0
    recs = []
    for u in u_seq:
        s, tau, hit, s_minus, s_plus = step_with_toi(s, u, dt)
        recs.append((tau, hit, s_minus, s_plus))
    return s, recs


def terminal_loss(s):
    p2 = s[2:4]
    return jnp.dot(p2, p2)


def main():
    s0 = jnp.array([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0])
    n, t = 40, 1.2
    dt = t / n
    u_seq = jnp.tile(jnp.array([0.0, 3.0]), (n, 1))
    s, recs = rollout(s0, u_seq, dt)
    hits = [i for i, r in enumerate(recs) if bool(r[1])]
    print("hits", hits)
    if hits:
        print("first gamma", float(recs[hits[0]][0]), "t", hits[0] * dt + float(recs[hits[0]][0]))
    print("p2", s[2:4])

    def J(u_y0):
        u = u_seq.at[0, 1].set(u_y0)
        sf, _ = rollout(s0, u, dt)
        return terminal_loss(sf)

    g = grad(J)(3.0)
    print("dJ/du_y[0]", float(g))


if __name__ == "__main__":
    main()
