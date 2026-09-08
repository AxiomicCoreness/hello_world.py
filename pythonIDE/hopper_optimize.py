#!/usr/bin/env python3
"""JAX 1D hopper optimizer using hopper_toi.step_hopper. No uvicorn."""
from __future__ import annotations

import json
import os
from pathlib import Path

import jax
import jax.numpy as jnp

from multibody_simulator.hopper_toi import step_hopper

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
    out_dir = Path(os.environ.get("HOPPER_OUT", "/app/ledger"))
    if not out_dir.exists():
        out_dir = Path("ledger")
    out_dir.mkdir(parents=True, exist_ok=True)
    u = jnp.full((N,), 4.0)
    vg = jax.jit(jax.value_and_grad(lambda uu: objective(uu)[0]))
    hist = []
    hits_hist = []
    lr = 0.02
    for i in range(80):
        loss, g = vg(u)
        u = u - lr * g
        hist.append(float(loss))
        if i % 10 == 0:
            _, (_, _, hits) = objective(u)
            hc = int(hits.sum())
            hits_hist.append(hc)
            print(f"Iter {i}: loss={float(loss):.6f} hits={hc}")
    s, rec = rollout(u)
    results = {
        "final_loss": hist[-1],
        "loss_first": hist[0],
        "final_hit_count": int(rec[2].sum()),
        "h_last": float(rec[0][-1]),
        "v_last": float(rec[1][-1]),
        "u_mean": float(jnp.mean(u)),
        "note": "9220 is code. This JSON is only written when the process actually runs.",
    }
    path = out_dir / "hopper_run.json"
    path.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print("wrote", path)


if __name__ == "__main__":
    main()
