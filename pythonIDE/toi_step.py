#!/usr/bin/env python3
"""2-ball TOI step fixture. Local numeric utility only.

No uvicorn, no 8024 bind, no MCP fill, no sovereign_lattice.
"""
from __future__ import annotations

from typing import Any

import torch

R = 0.2
DIAM2 = (2.0 * R) ** 2
MASS = 1.0
EPS = 1e-12


def split_state(s: torch.Tensor):
    p1 = s[..., 0:2]
    p2 = s[..., 2:4]
    v1 = s[..., 4:6]
    v2 = s[..., 6:8]
    return p1, p2, v1, v2


def pack_state(p1, p2, v1, v2) -> torch.Tensor:
    return torch.cat([p1, p2, v1, v2], dim=-1)


def integrate_free(p1, p2, v1, v2, u, t):
    a1 = u / MASS
    a2 = torch.zeros_like(v2)
    p1n = p1 + v1 * t + 0.5 * a1 * t * t
    p2n = p2 + v2 * t
    v1n = v1 + a1 * t
    v2n = v2 + a2 * t
    return p1n, p2n, v1n, v2n


def toi_quadratic(p1, p2, v1, v2, u, dt):
    """Smallest t in (0, dt] with |p2-p1|=2R.

    Closed-form quadratic on current relative kinematics (autograd-safe).
    Acceleration during the interval is applied in integrate_free; TOI
    uses v at the start of the interval so gamma stays in the graph.
    """
    del u
    rel_p = p2 - p1
    rel_v = v2 - v1
    aa = (rel_v * rel_v).sum(-1)
    bb = (2.0 * rel_p * rel_v).sum(-1)
    cc = (rel_p * rel_p).sum(-1) - DIAM2
    disc = bb * bb - 4.0 * aa * cc
    sqrt_disc = torch.sqrt(torch.clamp(disc, min=0.0) + EPS)
    t_lin = torch.where(
        aa.abs() > EPS,
        (-bb - sqrt_disc) / (2.0 * aa + EPS),
        torch.full_like(aa, dt),
    )
    t = torch.clamp(t_lin, min=0.0)
    approaching = (rel_p * rel_v).sum(-1) < -EPS
    hit = approaching & (disc > EPS) & (t > EPS) & (t <= dt)
    t = torch.where(hit, t, torch.ones_like(t) * dt)
    return t, hit


def elastic_equal_mass(p1, p2, v1, v2):
    n = p2 - p1
    nrm = torch.linalg.vector_norm(n, dim=-1, keepdim=True).clamp_min(EPS)
    nhat = n / nrm
    rel = v1 - v2
    j = (rel * nhat).sum(-1, keepdim=True)
    v1p = v1 - j * nhat
    v2p = v2 + j * nhat
    return v1p, v2p


def step_with_toi(s: torch.Tensor, u: torch.Tensor, dt: float):
    """Advance one interval. Returns (s_next, event_record)."""
    if not torch.is_tensor(s):
        s = torch.as_tensor(s, dtype=torch.float64)
    if not torch.is_tensor(u):
        u = torch.as_tensor(u, dtype=torch.float64)
    s = s.to(dtype=torch.float64)
    u = u.to(dtype=torch.float64)
    dt_t = torch.as_tensor(dt, dtype=s.dtype, device=s.device)

    p1, p2, v1, v2 = split_state(s)
    gamma, hit = toi_quadratic(p1, p2, v1, v2, u, dt_t)

    p1m, p2m, v1m, v2m = integrate_free(p1, p2, v1, v2, u, gamma)
    s_minus = pack_state(p1m, p2m, v1m, v2m)
    v1p, v2p = elastic_equal_mass(p1m, p2m, v1m, v2m)
    s_plus = pack_state(p1m, p2m, v1p, v2p)

    rem = (dt_t - gamma).clamp_min(0.0)
    p1f, p2f, v1f, v2f = integrate_free(p1m, p2m, v1p, v2p, u, rem)
    s_hit = pack_state(p1f, p2f, v1f, v2f)

    p1n, p2n, v1n, v2n = integrate_free(p1, p2, v1, v2, u, dt_t)
    s_free = pack_state(p1n, p2n, v1n, v2n)

    mask = hit.to(dtype=s.dtype).unsqueeze(-1)
    s_next = mask * s_hit + (1.0 - mask) * s_free

    event: dict[str, Any] = {
        "gamma": gamma,
        "hit": hit,
        "s_minus": s_minus,
        "s_plus": s_plus,
        "dt": dt_t,
    }
    return s_next, event


def rollout(s0, u_seq, dt):
    s = s0
    recs = []
    for u in u_seq:
        s, ev = step_with_toi(s, u, dt)
        recs.append(ev)
    return s, recs


def terminal_loss(s):
    p2 = s[..., 2:4]
    return (p2 * p2).sum(-1)


if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    s0 = torch.tensor([-1.0, -2.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0])
    N, T = 40, 1.2
    dt = T / N
    u_seq = torch.tensor([[0.0, 3.0]] * N, requires_grad=True)
    s, recs = rollout(s0, u_seq, dt)
    hits = [i for i, e in enumerate(recs) if bool(e["hit"].detach())]
    print("hits at steps", hits)
    if hits:
        g = recs[hits[0]]["gamma"].detach()
        print("first gamma", float(g), "t", hits[0] * dt + float(g))
    J = terminal_loss(s)
    J.backward()
    print("p2", s[2:4].detach())
    print("dJ/du_y first 8", u_seq.grad[:8, 1].detach())
    print("dJ/du_y last 8", u_seq.grad[-8:, 1].detach())
