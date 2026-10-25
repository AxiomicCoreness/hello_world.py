#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
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


NEWTON_ITERS = 32            # bracketed refinement iterations (value only)
RESIDUAL_TOL = 1e-4 * DIAM2  # |f(tau)| tolerance for a converged root
GRAZE_EPS = 1e-9             # |f'(tau)| below this counts as grazing


def _safe_den(x: torch.Tensor) -> torch.Tensor:
    """Denominator that is never ~0 (sign kept); pair with a torch.where mask."""
    one = torch.ones_like(x)
    return torch.where(x.abs() > EPS, x, torch.where(x < 0, -one, one))


def _contact_fn(t, rel_p, rel_v, rel_a):
    """f(t) = |r(t)|^2 - (2R)^2 and f'(t), with r(t) from integrate_free."""
    tt = t.unsqueeze(-1)
    r = rel_p + rel_v * tt + 0.5 * rel_a * tt * tt
    rd = rel_v + rel_a * tt
    return (r * r).sum(-1) - DIAM2, 2.0 * (r * rd).sum(-1)


def _smallest_root_in(a, b, c, dt):
    """Smallest root of a t^2 + b t + c in (0, dt], else dt (stable form)."""
    big = torch.ones_like(c) * (dt + 1.0)
    t_lin = torch.where(b.abs() > EPS, -c / _safe_den(b), big)
    t_lin = torch.where(t_lin > 0.0, t_lin, big)
    disc = b * b - 4.0 * a * c
    disc_ok = disc >= 0.0
    sq = torch.where(disc_ok, torch.sqrt(torch.where(disc_ok, disc, torch.zeros_like(disc))),
                     torch.zeros_like(disc))
    sgn = torch.where(b >= 0.0, torch.ones_like(b), -torch.ones_like(b))
    q = -0.5 * (b + sgn * sq)
    r1 = torch.where(a.abs() > EPS, q / _safe_den(a), big)
    r2 = torch.where(q.abs() > EPS, c / _safe_den(q), big)
    r1 = torch.where(r1 > 0.0, r1, big)
    r2 = torch.where(r2 > 0.0, r2, big)
    t_quad = torch.where(disc_ok, torch.minimum(r1, r2), big)
    t = torch.where(a.abs() > EPS, t_quad, t_lin)
    return torch.where(t <= dt, t, torch.ones_like(t) * dt)


def toi_quadratic(p1, p2, v1, v2, u, dt):
    """Smallest t in (0, dt] with |p2(t)-p1(t)| = 2R under integrate_free.

    Same algorithm as multibody_simulator/two_ball_toi.py (keep in sync).

    Earlier versions deliberately solved the closed-form quadratic on
    start-of-interval velocity only (acceleration ignored, u unused) so that
    gamma stayed in the autograd graph. That TOI disagreed with the positions
    integrate_free produces when u != 0: contacts inside a step could be
    predicted after dt and then missed (tunnelling), which made the loss
    discontinuous in u. Acceleration is now included, and gamma still stays
    in the graph:
      1. guess: gap along the start line of centres,
         d(t) = d0 + v_n t + 1/2 a_n t^2, stable quadratic form, linear
         fallback for a_n ~ 0, no root if disc < 0;
      2. value-only bracketed Newton/bisection on the exact
         f(t) = |r(t)|^2 - (2R)^2, r(t) = rel_p + rel_v t + 1/2 rel_a t^2;
      3. one Newton step from the detached root with live inputs, so
         dgamma = -f_theta / f_t (implicit-function gradient).
    A hit needs separation at t=0 and either f(dt) <= 0 or a converged
    entering root (f' < 0). Grazing (f' ~ 0) is not a hit.
    """
    rel_p = p2 - p1
    rel_v = v2 - v1
    rel_a = torch.zeros_like(v2) - u / MASS  # a2 = 0, a1 = u / MASS
    with torch.no_grad():
        rp, rv, ra = rel_p.detach(), rel_v.detach(), rel_a.detach()
        d0 = torch.sqrt((rp * rp).sum(-1))
        n0 = rp / _safe_den(d0).unsqueeze(-1)
        t = _smallest_root_in(0.5 * (n0 * ra).sum(-1), (n0 * rv).sum(-1), d0 - 2.0 * R, dt)
        f0, _ = _contact_fn(torch.zeros_like(t), rp, rv, ra)
        fdt, _ = _contact_fn(torch.ones_like(t) * dt, rp, rv, ra)
        bracket = (f0 > 0.0) & (fdt <= 0.0)
        lo = torch.zeros_like(t)
        hi = torch.ones_like(t) * dt
        for _ in range(NEWTON_ITERS):
            fv, fp = _contact_fn(t, rp, rv, ra)
            lo = torch.where(bracket & (fv > 0.0), t, lo)
            hi = torch.where(bracket & (fv <= 0.0), t, hi)
            t_n = t - fv / _safe_den(fp)
            inside = (t_n > lo) & (t_n < hi) & (fp.abs() > EPS)
            t_b = torch.where(inside, t_n, 0.5 * (lo + hi))
            t_free = torch.where(fp.abs() > EPS, t_n, t).clamp(min=0.0, max=float(dt))
            t = torch.where(bracket, t_b, t_free)
        fv, fp = _contact_fn(t, rp, rv, ra)
        entering = (fv.abs() <= RESIDUAL_TOL) & (fp < -GRAZE_EPS)
        hit = (f0 > 0.0) & (t > 0.0) & (t <= dt) & (bracket | entering)
    fv, fp = _contact_fn(t, rel_p, rel_v, rel_a)
    t_hit = torch.where(fp.abs() > EPS, t - fv / _safe_den(fp), t)
    gamma = torch.where(hit, t_hit.clamp(min=0.0, max=float(dt)), torch.ones_like(t) * dt)
    return gamma, hit


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
