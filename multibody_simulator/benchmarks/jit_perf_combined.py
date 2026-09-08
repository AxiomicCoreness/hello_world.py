#!/usr/bin/env python3
"""Combined two-ball + hopper JIT bench. Does not start uvicorn."""
from __future__ import annotations

import time

import jax
import jax.numpy as jnp

from multibody_simulator.two_ball_toi import step_with_toi
from multibody_simulator.hopper_toi import step_hopper

DT = 0.0021
LAMBDA = 0.01
N_BALL = 120
N_HOP = 80

s0_ball = jnp.array([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0])
u_ball = jnp.tile(jnp.array([0.0, 3.0]), (N_BALL, 1))
s0_hop = jnp.array([1.0, 0.0])
u_hop = jnp.full((N_HOP,), 9.81)


def forward_ball(s0, u_seq):
    def step_fn(s, u):
        s_next, tau, hit, *_ = step_with_toi(s, u, DT)
        return s_next, tau
    s_final, _ = jax.lax.scan(step_fn, s0, u_seq)
    return s_final


def loss_ball(u_seq):
    s = forward_ball(s0_ball, u_seq)
    return jnp.dot(s[2:4], s[2:4]) + LAMBDA * jnp.sum(u_seq * u_seq) * DT


def forward_hop(s0, u_seq):
    def step_fn(s, u):
        s_next, tau, hit, _ = step_hopper(s, u, DT)
        return s_next, tau
    s_final, _ = jax.lax.scan(step_fn, s0, u_seq)
    return s_final


def loss_hop(u_seq):
    s = forward_hop(s0_hop, u_seq)
    return (s[0] - 2.0) ** 2 + s[1] ** 2 + LAMBDA * jnp.sum(u_seq * u_seq) * DT


def time_fn(fn, *args, repeat=8):
    _ = fn(*args)
    jax.block_until_ready(_)
    acc = 0.0
    for _i in range(repeat):
        t0 = time.perf_counter()
        jax.block_until_ready(fn(*args))
        acc += (time.perf_counter() - t0) * 1000.0
    return acc / repeat


def report(name, loss, u):
    gfun = jax.grad(loss)
    gjit = jax.jit(gfun)
    ljit = jax.jit(loss)
    tp = time_fn(loss, u)
    tj = time_fn(ljit, u)
    gp = time_fn(gfun, u)
    gg = time_fn(gjit, u)
    print(f"{name} loss plain {tp:.3f} ms jit {tj:.3f} ms")
    print(f"{name} grad plain {gp:.3f} ms jit {gg:.3f} ms norm {float(jnp.linalg.norm(gfun(u))):.6f}")


def main():
    print("Combined TOI bench (no fastMCP spawn)")
    report("two-ball", loss_ball, u_ball)
    report("hopper", loss_hop, u_hop)


if __name__ == "__main__":
    main()
