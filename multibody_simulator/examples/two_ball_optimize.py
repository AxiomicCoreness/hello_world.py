#!/usr/bin/env python3
"""Optimal control for the two-ball collision problem using differentiable TOI.

Solves:
    min_u  ||p2(T)||^2 + λ ∑ ||u_i||^2 Δt
    s.t.   s_{i+1} = step_with_toi(s_i, u_i, Δt)

Expected: pre-collision u_y increases with time (ramp).
No uvicorn. No MCP fill.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import jax
import jax.numpy as jnp

try:
    from multibody_simulator.two_ball_toi import step_with_toi
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from two_ball_toi import step_with_toi


def main():
    T = 1.0
    N = 480
    dt = T / N
    lam = 0.01

    s0 = jnp.array([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0])
    u_init = jnp.tile(jnp.array([0.0, 3.0]), (N, 1))

    def forward(s0_, u_seq):
        def step_fn(s, u):
            s_next, tau, hit, s_minus, s_plus = step_with_toi(s, u, dt)
            return s_next, (s_next, tau, hit)

        s_final, traj = jax.lax.scan(step_fn, s0_, u_seq)
        return s_final, traj

    def loss(u_seq):
        s_final, _ = forward(s0, u_seq)
        p2_final = s_final[2:4]
        terminal = jnp.dot(p2_final, p2_final)
        reg = lam * jnp.sum(u_seq * u_seq) * dt
        return terminal + reg

    grad_loss = jax.grad(loss)

    def optimise(u_init_, lr=0.05, momentum=0.9, steps=500):
        u = u_init_
        v = jnp.zeros_like(u)
        loss_history = []

        @jax.jit
        def update(u_, v_):
            g = grad_loss(u_)
            v_ = momentum * v_ + (1.0 - momentum) * g
            u_ = u_ - lr * v_
            return u_, v_

        print("Running optimisation...")
        for i in range(steps):
            u, v = update(u, v)
            if i % 50 == 0:
                l = float(loss(u))
                loss_history.append(l)
                print(f"  Step {i:4d}: loss = {l:.6f}")
        return u, loss_history

    print("Optimising two-ball control with differentiable TOI...")
    t0 = time.perf_counter()
    u_opt, loss_hist = optimise(u_init, lr=0.05, steps=500)
    t1 = time.perf_counter()
    print(f"Done in {t1 - t0:.1f} s.")
    final_loss = float(loss(u_opt))
    print(f"Final loss: {final_loss:.6f}")
    print("First 30 u_y values:")
    print(u_opt[:30, 1])
    print("Last 30 u_y values:")
    print(u_opt[-30:, 1])
    jnp.save("u_opt_two_ball.npy", u_opt)
    print("Control sequence saved to u_opt_two_ball.npy")
    try:
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        ax1.plot(u_opt[:, 0], label="ux")
        ax1.set_ylabel("ux")
        ax2.plot(u_opt[:, 1], label="uy", color="orange")
        ax2.set_ylabel("uy")
        ax2.set_xlabel("Time step")
        plt.suptitle(f"Learned optimal controls (final loss = {final_loss:.4f})")
        plt.tight_layout()
        plt.savefig("two_ball_learned_controls.png", dpi=150)
        print("Plot saved as two_ball_learned_controls.png")
    except ImportError:
        print("Matplotlib not available; skipping plot.")


if __name__ == "__main__":
    main()
