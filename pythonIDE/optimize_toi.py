#!/usr/bin/env python3
"""Optimize a two-ball control sequence using the local TOI step."""
from __future__ import annotations

import json
from pathlib import Path

import torch

try:
    from .toi_step import step_with_toi
except ImportError:
    import sys

    sys.path.insert(0, str(__file__.rsplit("/", 1)[0]))
    from toi_step import step_with_toi


def run_optimization(iterations: int = 100, steps: int = 120) -> dict:
    duration = 1.0 / steps
    effort_weight = 0.01
    initial_state = torch.tensor([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0])
    control = torch.nn.Parameter(torch.zeros(steps, 2, dtype=torch.float64))
    control.data[:, 1] = 3.0
    optimizer = torch.optim.Adam([control], lr=0.02)
    losses = []

    for _ in range(iterations):
        state = initial_state.clone()
        hits = 0
        effort = torch.zeros((), dtype=control.dtype)
        for control_step in control:
            state, event = step_with_toi(state, control_step, duration)
            effort = effort + effort_weight * (control_step * control_step).sum() * duration
            hits += int(event["hit"].detach().item())
        loss = (state[2:4] * state[2:4]).sum() + effort
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))

    result = {"final_loss": losses[-1], "hits": hits, "iterations": iterations, "steps": steps}
    ledger = Path("ledger")
    ledger.mkdir(exist_ok=True)
    (ledger / "optimize_toi_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run_optimization()