#!/usr/bin/env python3
"""pythonIDE/optimize_toi.py — NumPy TOI-Velocity open-loop shooter.

Gravity assumption: a2 = 0 (paper / 9206). Hopper g is 9220 OPEN.
Triune placeholder is UNFILLED. MCP FILLED=False. No 0.0.0.0 bind.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from typing import List, Tuple

import numpy as np

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_SQ = PHI ** 2
THETA_SOVEREIGN = 2.5416018462

BALL_RADIUS = 0.2
BALL_MASS = 1.0
T_FINAL = 1.0
N_STEPS = int(os.environ.get("TOI_N", "480"))
DT = T_FINAL / N_STEPS
LAMBDA_REG = 0.01
S0 = np.array([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
MAX_ITER = int(os.environ.get("TOI_ITERS", "500"))
LR = float(os.environ.get("TOI_LR", "0.01"))
EPS_FD = math.sqrt(np.finfo(np.float64).eps)

# Gravity: two-ball paper has no free-fall on ball 2.
GRAVITY_ASSUMPTION = "a2=0"
A2_GRAVITY = np.zeros(2, dtype=np.float64)

# Hybrid triple placeholders. Only two-ball flow is implemented here.
TRIUNE = {
    "two_ball": {
        "filled": True,
        "flow": "ds = f(s, u)",
        "guard": "||p2-p1||^2 = (2R)^2",
        "reset": "elastic",
        "gravity": GRAVITY_ASSUMPTION,
    },
    "hopper": {
        "filled": False,
        "flow": "ds = f(s, u)",
        "guard": "h + v t + 0.5 a t^2 = 0",
        "reset": "velocity reversal",
        "gravity": "g stub — ledger 9220 OPEN",
    },
    "mcp_lattice": {
        "filled": False,
        "bind": "127.0.0.1:8024",
        "wildcard": False,
        "note": "FILLED=False stub only",
    },
}


def triune_status() -> dict:
    return {
        "filled": False,
        "gravity": GRAVITY_ASSUMPTION,
        "legs": {k: bool(v.get("filled")) for k, v in TRIUNE.items()},
    }


def step_with_toi(s: np.ndarray, u: np.ndarray, dt: float) -> Tuple[np.ndarray, float]:
    p1, p2 = s[0:2], s[2:4]
    v1, v2 = s[4:6], s[6:8]
    a1 = u / BALL_MASS
    a2 = A2_GRAVITY
    v1n = v1 + a1 * dt
    v2n = v2 + a2 * dt
    d = p2 - p1
    v_rel = v2n - v1n
    A = float(np.dot(v_rel, v_rel))
    B = float(2.0 * np.dot(d, v_rel))
    C = float(np.dot(d, d) - (2.0 * BALL_RADIUS) ** 2)
    gamma = dt
    if A > 1e-12:
        disc = B * B - 4.0 * A * C
        if disc >= 0.0:
            sqrt_disc = math.sqrt(disc)
            for t in ((-B - sqrt_disc) / (2.0 * A), (-B + sqrt_disc) / (2.0 * A)):
                if 0.0 < t <= dt:
                    gamma = t
                    break
    if gamma < dt:
        p1_hit = p1 + v1n * gamma
        p2_hit = p2 + v2n * gamma
        n = p2_hit - p1_hit
        n = n / (np.linalg.norm(n) + 1e-12)
        v1_n = np.dot(v1n, n) * n
        v2_n = np.dot(v2n, n) * n
        v1_post = (v1n - v1_n) + v2_n
        v2_post = (v2n - v2_n) + v1_n
        rem = dt - gamma
        p1_new = p1_hit + v1_post * rem
        p2_new = p2_hit + v2_post * rem
        return np.concatenate([p1_new, p2_new, v1_post, v2_post]), gamma
    p1_new = p1 + v1n * dt
    p2_new = p2 + v2n * dt
    return np.concatenate([p1_new, p2_new, v1n, v2n]), gamma


def forward_trajectory(u_seq: np.ndarray) -> Tuple[np.ndarray, List[float], float]:
    s = S0.copy()
    collisions: List[float] = []
    total = 0.0
    for i in range(N_STEPS):
        s, gamma = step_with_toi(s, u_seq[i], DT)
        if gamma < DT:
            collisions.append(i * DT + gamma)
        total += LAMBDA_REG * float(u_seq[i, 0] ** 2 + u_seq[i, 1] ** 2) * DT
    p2 = s[2:4]
    total += float(np.dot(p2, p2))
    return s, collisions, total


def numerical_gradient(u_seq: np.ndarray, eps: float = EPS_FD) -> np.ndarray:
    grad = np.zeros_like(u_seq)
    for i in range(N_STEPS):
        for j in range(2):
            up, um = u_seq.copy(), u_seq.copy()
            up[i, j] += eps
            um[i, j] -= eps
            _, _, lp = forward_trajectory(up)
            _, _, lm = forward_trajectory(um)
            grad[i, j] = (lp - lm) / (2.0 * eps)
    return grad


def adam_step(u, grad, m, v, t, lr=LR):
    b1, b2, eps = 0.9, 0.999, 1e-8
    m = b1 * m + (1.0 - b1) * grad
    v = b2 * v + (1.0 - b2) * (grad ** 2)
    mh = m / (1.0 - b1 ** t)
    vh = v / (1.0 - b2 ** t)
    return u - lr * mh / (np.sqrt(vh) + eps), m, v


def compute_event_hash(index: int, event: str) -> str:
    payload = f"{index}|{event}|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462"
    return hashlib.sha3_256(b"GARDEN.EVENT.v1\x00" + payload.encode("ascii")).hexdigest()


def run_optimization():
    u = np.zeros((N_STEPS, 2), dtype=np.float64)
    u[:, 1] = 3.0
    s, cols, loss0 = forward_trajectory(u)
    print(f"init J={loss0:.12f} hits={len(cols)} p2={s[2:4]} gravity={GRAVITY_ASSUMPTION}")
    print("triune", json.dumps(triune_status()))
    m = np.zeros_like(u)
    v = np.zeros_like(u)
    history = []
    for it in range(MAX_ITER):
        s, cols, loss = forward_trajectory(u)
        history.append(float(loss))
        grad = numerical_gradient(u)
        u, m, v = adam_step(u, grad, m, v, it + 1)
        if it % max(1, MAX_ITER // 10) == 0 or it == MAX_ITER - 1:
            g = cols[0] if cols else -1.0
            print(f"iter {it:4d} J={loss:.12f} hits={len(cols)} gamma={g:.8f}")
    s, cols, loss_f = forward_trajectory(u)
    h9207 = compute_event_hash(9207, "/toi_optimal_control_shooter")
    result = {
        "loss": float(loss_f),
        "hits": len(cols),
        "p2_final": s[2:4].tolist(),
        "gamma": float(cols[0]) if cols else None,
        "n": N_STEPS,
        "iters": MAX_ITER,
        "hash_9207": h9207,
        "gravity": GRAVITY_ASSUMPTION,
        "triune": triune_status(),
        "u_y_first5": [float(x) for x in u[:5, 1]],
        "u_y_last5": [float(x) for x in u[-5:, 1]],
        "loss_history": history,
    }
    os.makedirs("ledger", exist_ok=True)
    with open("ledger/optimize_toi_results.json", "w") as f:
        json.dump(result, f, indent=2)
    print("FINAL", json.dumps({
        "loss": result["loss"],
        "hits": result["hits"],
        "gravity": GRAVITY_ASSUMPTION,
        "triune_filled": False,
        "hash_9207": h9207,
    }))
    return result


def main():
    print("optimize_toi NumPy TOI_N=", N_STEPS, "TOI_ITERS=", MAX_ITER)
    print("gravity", GRAVITY_ASSUMPTION, "triune_filled", False)
    print("H_9207", compute_event_hash(9207, "/toi_optimal_control_shooter"))
    return run_optimization()


if __name__ == "__main__":
    main()
