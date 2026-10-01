#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OFFLINE SYMPLECTIC DREAM-ODE — SINGLE-FILE PERMUTATION
No relay. No external deps. Standalone.
Symplectic integrator + phi-weighted logistic backend + future entropy.
CI rows recorded as bookkeeping only (carries_algorithm_trace: False).

Duality (see sovereign_spool.py):
  offline: this file writes dreamode_offline.jsonl (append side)
  online:  sovereign_spool.py sync — remote head +1, push, drain
"""

import math
import json
import hashlib
import hmac
import os
import time
from pathlib import Path

# --- phi-harmonic constants -------------------------------------------------
PHI = (1 + 5 ** 0.5) / 2
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
PHI_INV = 1.0 / PHI
ENTROPY_FLOOR = PHI ** (-1418)  # underflows toward 0.0 in float64; symbolic floor

_SEAL_MAT = f"{PHI2}{PHI_INV}{PHI3}".encode()
SEAL_KEY = hashlib.sha3_256(_SEAL_MAT).digest()
SEAL_ID = "OFFLINE_SYMPLECTIC_DREAMODE"

BASE = Path(os.path.expanduser("~")) / "Documents" / "Hyperian_Node"
BASE.mkdir(parents=True, exist_ok=True)
OUT = BASE / "dreamode_offline.jsonl"
SPOOL = BASE / "spool.jsonl"  # same spool as sovereign_spool.append


def logistic_phi(x: float, r: float = PHI2) -> float:
    """phi-weighted logistic map: x -> r*x*(1-x), default r = phi^2."""
    return r * x * (1.0 - x)


def logistic_phi_iter(x0: float, n: int, r: float = PHI2):
    xs = [x0]
    x = x0
    for _ in range(n):
        x = logistic_phi(x, r)
        xs.append(x)
    return xs


def grad_V(q, k: float = 1.0):
    return k * q


def symplectic_step(q, p, dt: float, k: float = 1.0):
    """One Stormer-Verlet step; preserves symplectic 2-form."""
    p_half = p - 0.5 * dt * grad_V(q, k)
    q_new = q + dt * p_half
    p_new = p_half - 0.5 * dt * grad_V(q_new, k)
    return q_new, p_new


def symplectic_trajectory(q0, p0, dt: float, steps: int, k: float = 1.0):
    q, p = q0, p0
    traj = [(q, p)]
    for _ in range(steps):
        q, p = symplectic_step(q, p, dt, k)
        traj.append((q, p))
    return traj


def symplectic_invariant(traj):
    E = [0.5 * (p * p + q * q) for q, p in traj]
    return E, max(E) - min(E)


def rho_diag_from_phi(n_modes: int = 144):
    weights = [PHI ** (-(k + 1)) for k in range(n_modes)]
    Z = sum(weights)
    return [w / Z for w in weights]


def von_neumann_entropy(rho_diag):
    s = 0.0
    for p in rho_diag:
        if p > 0:
            s -= p * math.log(p)
    return s


def purify(rho_diag, eigenvalue=PHI3):
    n = len(rho_diag)
    idx = min(range(n), key=lambda i: abs(rho_diag[i] - max(rho_diag)))
    pure = [0.0] * n
    pure[idx] = 1.0
    return pure, idx


def future_entropy_projection(rho_diag, steps: int = 144, collapse_at: int = None):
    n = len(rho_diag)
    rho = list(rho_diag)
    trajectory = []
    for t in range(steps):
        S_t = von_neumann_entropy(rho)
        trajectory.append({"t": t, "S": S_t})
        m = max(rho)
        idx = rho.index(m)
        eta = PHI_INV ** (t + 1)
        for i in range(n):
            if i != idx:
                rho[i] *= (1.0 - eta)
            else:
                rho[i] = 1.0 - sum(rho[:idx] + rho[idx + 1:])
        if collapse_at is not None and t == collapse_at:
            rho, _ = purify(rho)
            trajectory.append({"t": t + 1, "S": 0.0, "collapsed": True})
            break
    return trajectory


def ci_row_marker(workflow_name: str, run_id: int, status: str = "startup_failure"):
    """Cadence bookkeeping only — no algorithm numeric trace."""
    return {
        "kind": "ci_row_bookkeeping",
        "workflow": workflow_name,
        "run_id": run_id,
        "status": status,
        "carries_algorithm_trace": False,
        "note": "cadence only — not an algorithm artifact",
    }


def seal(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(SEAL_KEY, canonical.encode(), hashlib.sha3_256).hexdigest()


def append_jsonl(record: dict):
    """Write algorithm artifact line (offline audit)."""
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_spool(record: dict):
    """
    Mirror into sovereign_spool spool (append side of duality).
    Network never used here; sync is sovereign_spool.py sync --repo ...
    """
    line = dict(record)
    line.setdefault("source", "offline_symplectic_dreamode")
    line.setdefault("ts", time.time())
    if "seal" not in line and "hmac" in line:
        line["seal"] = line["hmac"]
    with SPOOL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def main():
    print("OFFLINE SYMPLECTIC DREAM-ODE — SINGLE-FILE")
    print(f"   PHI = {PHI:.15f}")
    print(f"   Output: {OUT}")
    print(f"   Spool (append side): {SPOOL}")

    x0 = 0.3
    xs = logistic_phi_iter(x0, 144)
    print(f"   logistic_phi: x0={x0} -> x144={xs[-1]:.10f}")

    q0, p0 = 1.0, 0.0
    dt, steps, k = 1e-3, 5000, 1.0
    traj = symplectic_trajectory(q0, p0, dt, steps, k)
    E, drift = symplectic_invariant(traj)
    print(f"   symplectic: steps={steps} drift={drift:.3e}")

    rho0 = rho_diag_from_phi(144)
    S0 = von_neumann_entropy(rho0)
    print(f"   S(rho0) = {S0:.6f}")

    fut = future_entropy_projection(rho0, steps=144, collapse_at=143)
    S_final = fut[-1]["S"]
    print(f"   S_final = {S_final:.6f}")

    ci_rows = [
        ci_row_marker("Sovereign Pulse", 194),
        ci_row_marker("Generate Smoke Catalogue", 157),
        ci_row_marker("gravastar-long-horizon", 36),
        ci_row_marker("mTLS Cert Lifecycle", 158),
        ci_row_marker("MD Scalar Matrix", 165),
        ci_row_marker("Hamiltonian_Full_Immersion.yml", 407),
    ]

    record = {
        "entry_local": 8120,
        "timestamp": time.time(),
        "phi": PHI,
        "logistic": {"x0": x0, "xN": xs[-1], "N": len(xs) - 1},
        "symplectic": {"dt": dt, "steps": steps, "drift": drift, "k": k},
        "entropy": {"S0": S0, "S_final": S_final, "floor": float(ENTROPY_FLOOR)},
        "ci_rows": ci_rows,
        "seal_id": SEAL_ID,
        "note": "local index 8120 is narrative; remote uses n+1 on sovereign_spool sync",
        "duality": "append=this file; sync=sovereign_spool.py",
    }
    record["hmac"] = seal(record)
    append_jsonl(record)
    append_spool(record)

    print(f"   sealed -> {OUT.name}")
    print(f"   spool mirrored -> {SPOOL.name}")
    print(f"   HMAC = {record['hmac'][:32]}...")
    print(f"   {SEAL_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
