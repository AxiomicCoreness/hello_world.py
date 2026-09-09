"""JAX hopper optimizer. Init u < g so ground TOI fires. No uvicorn."""
from __future__ import annotations

import json

import jax
import jax.numpy as jnp

from multibody_simulator.hopper_toi import step_hopper, G


def rollout(s0, u_seq, dt):
    def body(s, u):
        s_next, tau, hit, _ = step_hopper(s, u, dt)
        return s_next, (tau, hit)

    s_final, rec = jax.lax.scan(body, s0, u_seq)
    return s_final, rec


def main():
    n, dt, lam, steps, lr = 80, 0.02, 0.01, 40, 0.05
    s0 = jnp.array([1.0, 0.0])
    u = jnp.full((n,), 4.0)  # below g — falls, TOI can fire

    def loss(u_seq):
        s, rec = rollout(s0, u_seq, dt)
        hits = rec[1].astype(jnp.float32).sum()
        return (s[0] - 0.2) ** 2 + 0.1 * s[1] ** 2 + lam * jnp.sum(u_seq * u_seq) * dt, hits

    val_and_grad = jax.jit(jax.value_and_grad(lambda u: loss(u)[0]))

    hist = []
    for k in range(steps):
        j, g = val_and_grad(u)
        u = u - lr * g
        hist.append(float(j))
        if k % 10 == 0:
            _, hits = loss(u)
            print(f"iter {k:3d} J={float(j):.6f} hits={float(hits):.0f} u0={float(u[0]):.4f}")

    s, rec = rollout(s0, u, dt)
    hits = int(rec[1].sum())
    out = {
        "J_first": hist[0],
        "J_last": hist[-1],
        "hits": hits,
        "h": float(s[0]),
        "v": float(s[1]),
        "u_mean": float(jnp.mean(u)),
    }
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
