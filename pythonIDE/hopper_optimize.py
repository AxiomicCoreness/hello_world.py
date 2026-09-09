#!/usr/bin/env python3
"""JAX 1D hopper optimizer + writer. Uses hopper_toi. No uvicorn."""
from __future__ import annotations

import json

import jax
import jax.numpy as jnp

from multibody_simulator.hopper_toi import step_hopper
from pythonIDE.hopper_writer import write_hopper_run

DT = 0.01
T = 2.0
N = int(T / DT)


def rollout(u_seq, h0=1.0, v0=0.0):
    def body(carry, u):
        s_next, tau, hit, _ = step_hopper(carry, u, DT)
        return s_next, (s_next[0], s_next[1], hit, tau)

    s0 = jnp.array([h0, v0])
    s_final, rec = jax.lax.scan(body, s0, u_seq)
    return s_final, rec


def objective(u_seq):
    s_final, rec = rollout(u_seq)
    h_traj, v_traj, hits, taus = rec
    term = h_traj[-1] ** 2 + 0.01 * v_traj[-1] ** 2
    run = 0.001 * jnp.sum(u_seq * u_seq)
    return term + run, (h_traj, v_traj, hits)


def main():
    u = jnp.full((N,), 4.0)
    vg = jax.jit(jax.value_and_grad(lambda uu: objective(uu)[0]))
    hist = []
    lr = 0.02
    for i in range(80):
        loss, g = vg(u)
        u = u - lr * g
        hist.append(float(loss))
        if i % 10 == 0:
            _, (_, _, hits) = objective(u)
            print(f"Iter {i}: loss={float(loss):.6f} hits={int(hits.sum())}")
    s, rec = rollout(u)
    results = {
        "final_loss": hist[-1],
        "loss_first": hist[0],
        "final_hit_count": int(rec[2].sum()),
        "h_last": float(rec[0][-1]),
        "v_last": float(rec[1][-1]),
        "u_mean": float(jnp.mean(u)),
        "note": "writer only records a run when this process executes under JAX",
    }
    path = write_hopper_run(results)
    print(json.dumps(results, indent=2))
    print("wrote", path)
    return results


if __name__ == "__main__":
    main()
