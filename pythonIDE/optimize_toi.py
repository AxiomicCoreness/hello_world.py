#!/usr/bin/env python3
"""Open-loop TOI shooter. No MCP, no uvicorn, no sovereign_lattice."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from toi_step import rollout, terminal_loss  # noqa: E402

LAMBDA = 0.01
T = 1.0


def running_cost(u_seq: torch.Tensor, dt: float) -> torch.Tensor:
    return LAMBDA * (u_seq * u_seq).sum() * dt


def optimize(n: int, iters: int, lr: float = 0.01) -> dict:
    dt = T / n
    s0 = torch.tensor([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0], dtype=torch.float64)
    u = torch.zeros((n, 2), dtype=torch.float64)
    u[:, 1] = 3.0
    u.requires_grad_(True)
    opt = torch.optim.Adam([u], lr=lr)
    hist = []
    for k in range(iters):
        opt.zero_grad(set_to_none=True)
        s, recs = rollout(s0, u, dt)
        J = terminal_loss(s) + running_cost(u, dt)
        J.backward()
        torch.nn.utils.clip_grad_norm_([u], max_norm=1.0)
        opt.step()
        hist.append(float(J.detach()))
        if k % max(1, iters // 10) == 0 or k == iters - 1:
            hits = sum(int(bool(e["hit"].detach())) for e in recs)
            uy0 = float(u.detach()[0, 1])
            uym = float(u.detach()[n // 2, 1])
            uye = float(u.detach()[-1, 1])
            print(f"iter {k:4d}  J={hist[-1]:.6f}  hits={hits}  uy0={uy0:.4f}  uy_mid={uym:.4f}  uy_end={uye:.4f}")
    s, recs = rollout(s0, u.detach(), dt)
    hit_idx = [i for i, e in enumerate(recs) if bool(e["hit"])]
    return {
        "J": hist[-1],
        "hist": hist,
        "u": u.detach(),
        "p2": s[2:4].detach(),
        "hit_idx": hit_idx,
        "dt": dt,
    }


def main() -> int:
    torch.set_default_dtype(torch.float64)
    n = int(os.environ.get("TOI_N", "480"))
    iters = int(os.environ.get("TOI_ITERS", "500"))
    print(f"N={n} T={T} iters={iters} lambda={LAMBDA}")
    out = optimize(n, iters)
    u = out["u"]
    print("final J", out["J"])
    print("p2(T)", out["p2"])
    print("hit steps", out["hit_idx"][:5], "...")
    print("u first 5\n", u[:5])
    print("u last 5\n", u[-5:])
    if out["hit_idx"]:
        i = out["hit_idx"][0]
        pre = u[:i, 1]
        print("pre-impact uy first,last", float(pre[0]), float(pre[-1]), "delta", float(pre[-1] - pre[0]))
    if os.environ.get("TOI_PLOT", "0") == "1":
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib missing — skip plot")
            return 0
        fig, ax = plt.subplots(2, 1, figsize=(8, 6))
        ax[0].plot(out["hist"])
        ax[0].set_ylabel("J")
        t = [i * out["dt"] for i in range(len(u))]
        ax[1].plot(t, u[:, 1].numpy(), label="uy")
        ax[1].set_xlabel("t")
        ax[1].set_ylabel("uy")
        fig.tight_layout()
        png = HERE / "optimize_toi_controls.png"
        fig.savefig(png, dpi=120)
        print("wrote", png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
