#!/usr/bin/env python3
"""
pythonIDE/optimize_toi.py — Two‑ball optimal control with TOI‑Velocity

Problem setup (from paper):
- Two identical balls (r=0.2) on a plane
- Initial: p1=[-1,-2], p2=[-1,-1], v1=v2=0
- Control: forces on Ball 1 only (u_x, u_y)
- Time horizon: T=1.0s, N=480 steps (dt=1/480)
- Loss: J = ||p2(T)||² + 0.01 * Σ||u_i||² * dt
- Initial guess: u = [0, 3] (constant)

Expected result:
- Pre‑collision u_y should INCREASE with time (ramp)
- Post‑collision u_y should flatten out
- Loss should converge to analytical optimum

Uses the TOI‑Velocity step from toi_step.py (artifact 9206).
"""

import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import hashlib
import json
import os
from datetime import datetime

# Import the TOI step from 9206
try:
    from pythonIDE.toi_step import step_with_toi
except ImportError:
    # Fallback: define minimal step if not available
    def step_with_toi(s, u, dt, r=0.2):
        """Placeholder — actual implementation from 9206."""
        p1, v1, p2, v2 = s[0:2], s[2:4], s[4:6], s[6:8]
        # ... (full implementation from 9206)
        # For now, raise error
        raise NotImplementedError("Need toi_step.py from 9206")


def run_optimization():
    """Run the two‑ball TOI‑Velocity optimization and print results."""
    
    # ------------------------------------------------------------------
    # 1. Problem setup
    # ------------------------------------------------------------------
    T = 1.0
    N = 480
    dt = T / N
    r = 0.2
    lam = 0.01  # control effort penalty
    
    # Initial state: p1=[-1,-2], p2=[-1,-1], velocities zero
    p1_0 = torch.tensor([-1.0, -2.0], requires_grad=False)
    p2_0 = torch.tensor([-1.0, -1.0], requires_grad=False)
    v1_0 = torch.tensor([0.0, 0.0], requires_grad=False)
    v2_0 = torch.tensor([0.0, 0.0], requires_grad=False)
    
    s0 = torch.cat([p1_0, v1_0, p2_0, v2_0])  # shape (8,)
    
    # Initial control: constant [0, 3] as in paper
    u_init = torch.zeros((N, 2))
    u_init[:, 1] = 3.0  # y‑direction force = 3
    u = nn.Parameter(u_init.clone())
    
    # ------------------------------------------------------------------
    # 2. Forward simulation (differentiable)
    # ------------------------------------------------------------------
    def forward(u_seq):
        s = s0.clone()
        loss = 0.0
        hit_count = 0
        
        for i in range(N):
            s, hit = step_with_toi(s, u_seq[i], dt, r)
            loss += lam * torch.sum(u_seq[i]**2) * dt
            hit_count += hit.item() if isinstance(hit, torch.Tensor) else hit
        
        p2 = s[4:6]
        loss += torch.sum(p2**2)  # terminal cost
        
        return loss, hit_count, s
    
    # ------------------------------------------------------------------
    # 3. Optimizer
    # ------------------------------------------------------------------
    optimizer = torch.optim.Adam([u], lr=0.02)
    
    loss_history = []
    hit_history = []
    u_history = []
    
    print("\n" + "="*80)
    print("TOI‑Velocity Optimal Control — Two‑Ball Shooter")
    print(f"  T={T}s, N={N}, dt={dt:.6f}s, λ={lam}")
    print("="*80)
    
    n_iter = 500
    for it in range(n_iter):
        optimizer.zero_grad()
        loss, hits, s_final = forward(u)
        loss.backward()
        optimizer.step()
        
        loss_history.append(loss.item())
        hit_history.append(hits)
        
        if it % 50 == 0:
            u_y_mean = u[:, 1].mean().item()
            u_y_std = u[:, 1].std().item()
            print(f"Iter {it:4d}: loss={loss.item():.6f}, hits={hits}, u_y_mean={u_y_mean:.4f}±{u_y_std:.4f}")
    
    # ------------------------------------------------------------------
    # 4. Final results
    # ------------------------------------------------------------------
    final_loss, final_hits, final_s = forward(u)
    p2_final = final_s[4:6].detach().numpy()
    
    u_final = u.detach().numpy()
    u_x = u_final[:, 0]
    u_y = u_final[:, 1]
    
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    print(f"  Final loss: {final_loss.item():.6f}")
    print(f"  Hits: {final_hits}")
    print(f"  Ball 2 final position: ({p2_final[0]:.4f}, {p2_final[1]:.4f})")
    
    # Pre‑collision ramp: find collision time
    # For u_y=3, t_collision ≈ 0.632s (step 304 when N=480, dt=1/480)
    # We'll detect where u_y starts to drop after collision
    # Simple heuristic: find max u_y after the ramp
    collision_idx = np.argmax(u_y)
    print(f"  Estimated collision step: {collision_idx} ({collision_idx*dt:.4f}s)")
    
    print("\n" + "-"*80)
    print("CONTROL SEQUENCE — FIRST 10 STEPS:")
    for i in range(min(10, N)):
        print(f"  step {i:3d}: u_x={u_x[i]:.6f}, u_y={u_y[i]:.6f}")
    
    print("\n" + "-"*80)
    print("CONTROL SEQUENCE — PRE‑COLLISION RAMP (steps around max):")
    ramp_start = max(0, collision_idx - 10)
    ramp_end = min(N, collision_idx + 5)
    for i in range(ramp_start, ramp_end):
        marker = " <-- collision" if i == collision_idx else ""
        print(f"  step {i:3d}: u_x={u_x[i]:.6f}, u_y={u_y[i]:.6f}{marker}")
    
    print("\n" + "-"*80)
    print("CONTROL SEQUENCE — LAST 10 STEPS:")
    for i in range(max(0, N-10), N):
        print(f"  step {i:3d}: u_x={u_x[i]:.6f}, u_y={u_y[i]:.6f}")
    
    # ------------------------------------------------------------------
    # 5. Cryptographic hash (untrucated)
    # ------------------------------------------------------------------
    hash_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "loss": final_loss.item(),
        "hits": final_hits,
        "p2_final": [float(x) for x in p2_final],
        "u_first_10": [float(x) for x in u_x[:10]] + [float(x) for x in u_y[:10]],
        "u_last_10": [float(x) for x in u_x[-10:]] + [float(x) for x in u_y[-10:]],
        "collision_step": int(collision_idx),
        "u_x_mean": float(np.mean(u_x)),
        "u_y_mean": float(np.mean(u_y)),
        "u_y_max": float(np.max(u_y))
    }
    
    hash_str = json.dumps(hash_data, sort_keys=True)
    hash_hex = hashlib.sha256(hash_str.encode()).hexdigest()
    
    print("\n" + "-"*80)
    print("CRYPTOGRAPHIC SEAL:")
    print(f"  SHA‑256: {hash_hex}")
    
    # ------------------------------------------------------------------
    # 6. Plot
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # Loss curve
    axes[0, 0].plot(loss_history)
    axes[0, 0].set_title("Loss vs Iteration")
    axes[0, 0].set_xlabel("Iteration")
    axes[0, 0].set_ylabel("Loss")
    axes[0, 0].grid(True)
    
    # Hit count
    axes[0, 1].plot(hit_history)
    axes[0, 1].set_title("Hits per Iteration")
    axes[0, 1].set_xlabel("Iteration")
    axes[0, 1].set_ylabel("Hits")
    axes[0, 1].grid(True)
    
    # Control sequences
    t = np.arange(N) * dt
    axes[1, 0].plot(t, u_x, label='u_x')
    axes[1, 0].plot(t, u_y, label='u_y')
    axes[1, 0].axvline(collision_idx * dt, color='r', linestyle='--', label='collision')
    axes[1, 0].set_title("Learned Control Sequence")
    axes[1, 0].set_xlabel("Time (s)")
    axes[1, 0].set_ylabel("Control")
    axes[1, 0].legend()
    axes[1, 0].grid(True)
    
    # u_y ramp detail (pre‑collision)
    ramp_start_idx = max(0, collision_idx - 60)
    ramp_end_idx = min(N, collision_idx + 10)
    t_ramp = t[ramp_start_idx:ramp_end_idx]
    u_y_ramp = u_y[ramp_start_idx:ramp_end_idx]
    axes[1, 1].plot(t_ramp, u_y_ramp, 'b-', linewidth=2)
    axes[1, 1].axvline(collision_idx * dt, color='r', linestyle='--', label='collision')
    axes[1, 1].set_title("Pre‑Collision u_y Ramp (paper Fig. 8)")
    axes[1, 1].set_xlabel("Time (s)")
    axes[1, 1].set_ylabel("u_y")
    axes[1, 1].legend()
    axes[1, 1].grid(True)
    
    plt.tight_layout()
    
    # Save plot
    plot_path = "ledger/optimize_toi_plot.png"
    os.makedirs("ledger", exist_ok=True)
    plt.savefig(plot_path)
    print(f"\n  Plot saved: {plot_path}")
    
    # Save JSON results
    result_path = "ledger/optimize_toi_results.json"
    with open(result_path, "w") as f:
        json.dump({
            "loss_history": loss_history,
            "hit_history": hit_history,
            "u_x": [float(x) for x in u_x],
            "u_y": [float(x) for x in u_y],
            "final_loss": final_loss.item(),
            "final_hits": final_hits,
            "p2_final": [float(x) for x in p2_final],
            "collision_step": int(collision_idx),
            "hash": hash_hex,
            "timestamp": datetime.utcnow().isoformat()
        }, f, indent=2)
    print(f"  Results saved: {result_path}")
    
    # ------------------------------------------------------------------
    # 7. Return
    # ------------------------------------------------------------------
    return {
        "loss": final_loss.item(),
        "hits": final_hits,
        "p2_final": p2_final.tolist(),
        "collision_step": int(collision_idx),
        "hash": hash_hex,
        "u_x": u_x.tolist(),
        "u_y": u_y.tolist()
    }


if __name__ == "__main__":
    results = run_optimization()
    
    print("\n" + "="*80)
    print("✅ OPTIMIZATION COMPLETE")
    print("="*80)
    print(f"  Loss: {results['loss']:.6f}")
    print(f"  Hits: {results['hits']}")
    print(f"  Hash: {results['hash']}")
    print("="*80)
