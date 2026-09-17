#!/usr/bin/env python3
"""JAX JIT benchmark for two-ball TOI scan + grad.

Uses step_with_toi(s, u, dt) from 9213 (no R argument).
Printed millisecond tables in chat drafts are not measurements.
"""
from __future__ import annotations

import time

import jax
import jax.numpy as jnp

from multibody_simulator.two_ball_toi import step_with_toi

T = 1.0
N = 480
DT = T / N
LAMBDA = 0.01

s0 = jnp.array([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0])
u_seq = jnp.tile(jnp.array([0.0, 3.0]), (N, 1))


def forward_plain(s0_, u_seq_):
    def step_fn(s, u):
        s_next, tau, hit, s_minus, s_plus = step_with_toi(s, u, DT)
        return s_next, (s_next, tau, hit)

    s_final, _ = jax.lax.scan(step_fn, s0_, u_seq_)
    return s_final


def loss_plain(u_seq_):
    s_final = forward_plain(s0, u_seq_)
    p2 = s_final[2:4]
    return jnp.dot(p2, p2) + LAMBDA * jnp.sum(u_seq_ * u_seq_) * DT


grad_plain = jax.grad(loss_plain)
forward_jit = jax.jit(forward_plain)
loss_jit = jax.jit(loss_plain)
grad_jit = jax.jit(grad_plain)


def time_fn(fn, *args, repeat=10):
    _ = fn(*args)
    jax.block_until_ready(_)
    times = []
    for _i in range(repeat):
        start = time.perf_counter()
        result = fn(*args)
        jax.block_until_ready(result)
        times.append((time.perf_counter() - start) * 1000.0)
    return sum(times) / len(times), times


def main():
    print("JAX JIT Performance Benchmark (two-ball TOI)")
    print(f"Steps: {N}, dt: {DT:.4f}s")
    t_plain_fwd, _ = time_fn(forward_plain, s0, u_seq)
    t_jit_fwd, _ = time_fn(forward_jit, s0, u_seq)
    print("\nForward pass:")
    print(f"  Plain: {t_plain_fwd:.3f} ms")
    print(f"  JIT:   {t_jit_fwd:.3f} ms")
    print(f"  Speed-up: {t_plain_fwd / max(t_jit_fwd, 1e-9):.2f}x")
    t_plain_loss, _ = time_fn(loss_plain, u_seq)
    t_jit_loss, _ = time_fn(loss_jit, u_seq)
    print("\nLoss computation:")
    print(f"  Plain: {t_plain_loss:.3f} ms")
    print(f"  JIT:   {t_jit_loss:.3f} ms")
    print(f"  Speed-up: {t_plain_loss / max(t_jit_loss, 1e-9):.2f}x")
    t_plain_grad, _ = time_fn(grad_plain, u_seq)
    t_jit_grad, _ = time_fn(grad_jit, u_seq)
    print("\nGradient computation:")
    print(f"  Plain: {t_plain_grad:.3f} ms")
    print(f"  JIT:   {t_jit_grad:.3f} ms")
    print(f"  Speed-up: {t_plain_grad / max(t_jit_grad, 1e-9):.2f}x")
    g = grad_plain(u_seq)
    print(f"\nGradient norm (plain): {float(jnp.linalg.norm(g)):.6f}")
    print("JIT compile time is excluded after warmup. Draft ms tables are not this run.")


if __name__ == "__main__":
    main()
