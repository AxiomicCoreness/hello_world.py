#!/usr/bin/env python3
"""One-pass 1D hopper TOI optimize (NumPy). No uvicorn. No MCP."""
from __future__ import annotations

import math

G = 9.81
E = 0.8
EPS = 1e-12


def step_hopper(h, v, u, dt, e=E, g=G):
    a = u - g
    aa, bb, cc = 0.5 * a, v, h
    disc = bb * bb - 4.0 * aa * cc
    t_hit = dt + 1.0
    hit = False
    if disc >= 0.0 and abs(aa) > EPS:
        sd = math.sqrt(disc)
        for t in ((-bb - sd) / (2.0 * aa), (-bb + sd) / (2.0 * aa)):
            if EPS < t <= dt:
                t_hit = t
                hit = True
                break
    tau = t_hit if hit else dt
    hm = h + v * tau + 0.5 * a * tau * tau
    vm = v + a * tau
    vp = -e * vm if hit else vm
    rem = max(dt - tau, 0.0)
    hn = hm + vp * rem + 0.5 * a * rem * rem
    vn = vp + a * rem
    return hn, vn, tau, hit


def rollout(u, dt, h0=1.0, v0=0.0):
    h, v = h0, v0
    hits = 0
    for ui in u:
        h, v, tau, hit = step_hopper(h, v, ui, dt)
        hits += int(hit)
    return h, v, hits


def loss(u, dt):
    h, v, hits = rollout(u, dt)
    return (h - 2.0) ** 2 + v ** 2 + 0.01 * sum(x * x for x in u) * dt, h, v, hits


def one_pass(n=80, dt=0.01, lr=0.02):
    u = [9.81] * n
    j0, h0, v0, hits0 = loss(u, dt)
    g = []
    eps = 1e-3
    for i in range(n):
        u[i] += eps
        jp, *_ = loss(u, dt)
        u[i] -= eps
        g.append((jp - j0) / eps)
    u1 = [ui - lr * gi for ui, gi in zip(u, g)]
    j1, h1, v1, hits1 = loss(u1, dt)
    return {
        "J0": j0,
        "J1": j1,
        "h0": h0,
        "h1": h1,
        "v0": v0,
        "v1": v1,
        "hits0": hits0,
        "hits1": hits1,
        "g_norm": math.sqrt(sum(x * x for x in g)),
    }


if __name__ == "__main__":
    out = one_pass()
    for k, v in out.items():
        print(f"{k}={v}")
