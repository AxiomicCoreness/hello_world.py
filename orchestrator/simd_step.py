#!/usr/bin/env python3
"""
orchestrator/simd_step.py — SIMD batch interface over Garden step surfaces.

Batches in one atomic cycle (asyncio.gather):
  Phase 0  convergence /step   (local math)
  Phase 1  /mesh               (local φ-coupled map)
  Phase 2  orchestrator.dispatch (DeepSeek optional)
  Phase 3  MCP /pulse          (optional HTTP)
  Phase 4  /deepseek/stream    (optional HTTP, collected)
  Phase ρ  density field       (optional --phase-rho)

Then applies leaky-integral PID to e_batch = mean(1 - C_i).
I state can be loaded/saved via --leaky-i / --leaky-i-path (ledger 8805).

Usage:
  python -m orchestrator.simd_step --no-http
  python -m orchestrator.simd_step --phase-rho --leaky-i-path /var/state/leaky_i/i_value
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import time
from typing import Any, Dict, List, Optional

PHI = (1 + math.sqrt(5)) / 2
PHASE_TARGET = 202.6
ALPHA = 1.0 / PHI
KP, KI, KD = PHI**2, 1.0 / PHI, PHI ** (-2)
PSD = 5.774

try:
    from orchestrator.dispatch import dispatch_cycle
except ImportError:
    from dispatch import dispatch_cycle  # type: ignore

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

_I = 0.0
_e_prev = 0.0


def load_leaky_i(path: Optional[str], explicit: Optional[float]) -> float:
    global _I
    if explicit is not None:
        _I = float(explicit)
        return _I
    if path and os.path.isfile(path):
        try:
            with open(path) as f:
                _I = float(f.read().strip() or "0")
        except (OSError, ValueError):
            _I = 0.0
    return _I


def save_leaky_i(path: Optional[str]) -> None:
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(f"{_I:.12g}\n")


def harmonic_density_field(chi: float) -> float:
    return abs(math.sin(chi) * (PHI ** (-abs(chi)))) * (PHI ** 9)


def rho_universal(position: float, t: float = 0.0) -> float:
    return PSD * harmonic_density_field(position + t)


def local_rho_phase(seed_phase: float, t: float = 0.0) -> Dict[str, Any]:
    """Optional density-field phase for SIMD (ledger 8804)."""
    chi = (seed_phase / 360.0) * 2 * math.pi
    rho = rho_universal(chi, t)
    rho_target = PSD
    rho_error = abs(rho - rho_target) / max(rho_target, 1e-12)
    return {
        "phase_id": "rho",
        "name": "rho",
        "rho": rho,
        "rho_target": rho_target,
        "rho_error": rho_error,
        "chi": chi,
        "status": "ok",
    }


def local_step(coherence: float, phase: float, workload: float, dt: float) -> Dict[str, Any]:
    gamma = 1.0 / math.sqrt(5.0)
    C = 1.0 - (1.0 - coherence) * math.exp(-gamma * dt)
    k = 1.0 / (PHI**3)
    phi_next = phase + k * (PHASE_TARGET - phase)
    W = workload * math.exp(-gamma * dt)
    e = 1.0 - C
    if e > 0.5:
        branch = "A"
    elif abs(phi_next - PHASE_TARGET) > 2.0:
        branch = "C"
    else:
        branch = "B"
    return {
        "phase_id": 0,
        "name": "step",
        "C": C,
        "phase": phi_next,
        "workload": W,
        "error": e,
        "branch": branch,
        "status": "ok",
    }


def local_mesh(nodes: int, seed_phase: float, coupling: float) -> Dict[str, Any]:
    phases = [(seed_phase + i * 360.0 / (PHI * PHI)) % 360.0 for i in range(nodes)]
    freqs = [6.49 * (PHI ** (i % 12)) for i in range(nodes)]
    mean_phase = sum(phases) / nodes
    coupling_energy = coupling * sum(
        abs(phases[i] - phases[(i + 1) % nodes]) for i in range(nodes)
    ) / nodes
    return {
        "phase_id": 1,
        "name": "mesh",
        "nodes": nodes,
        "mean_phase": mean_phase,
        "coupling_energy": coupling_energy,
        "freqs_head": freqs[: min(7, nodes)],
        "status": "ok",
    }


def pid_update(e_batch: float, dt: float) -> Dict[str, float]:
    global _I, _e_prev
    _I = _I + dt * (e_batch - ALPHA * _I)
    de = (e_batch - _e_prev) / dt if dt > 0 else 0.0
    u = KP * e_batch + KI * _I + KD * de
    _e_prev = e_batch
    return {"I": _I, "u": u, "e_batch": e_batch, "de": de}


async def http_pulse(mcp_url: str, secret: str, force_branch: Optional[str]) -> Dict[str, Any]:
    if httpx is None:
        return {"phase_id": 3, "name": "pulse", "status": "skipped", "reason": "httpx missing"}
    url = mcp_url.rstrip("/") + "/pulse"
    payload = {"force_branch": force_branch, "use_deepseek": True, "source": "simd_step"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                url,
                json=payload,
                headers={"X-Garden-Secret": secret, "Content-Type": "application/json"},
            )
            data = r.json() if r.content else {}
            return {
                "phase_id": 3,
                "name": "pulse",
                "status": "ok" if r.status_code == 200 else "error",
                "http_status": r.status_code,
                "body": data,
            }
    except Exception as e:
        return {"phase_id": 3, "name": "pulse", "status": "error", "error": str(e)}


async def http_stream_collect(base_url: str, prompt: str, max_tokens: int = 64) -> Dict[str, Any]:
    if httpx is None:
        return {"phase_id": 4, "name": "stream", "status": "skipped", "reason": "httpx missing"}
    url = base_url.rstrip("/") + "/deepseek/stream"
    chunks: List[str] = []
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                url,
                json={"prompt": prompt, "max_tokens": max_tokens},
                headers={"Content-Type": "application/json"},
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        chunks.append(data)
        return {
            "phase_id": 4,
            "name": "stream",
            "status": "ok",
            "text": "".join(chunks)[:2000],
            "chunks": len(chunks),
        }
    except Exception as e:
        return {"phase_id": 4, "name": "stream", "status": "error", "error": str(e)}


async def simd_batch_step(
    coherence: float = 0.99,
    phase: float = 200.0,
    dt: float = 1.0,
    nodes: int = 7,
    branch: Optional[str] = None,
    base_url: Optional[str] = None,
    mcp_url: Optional[str] = None,
    garden_secret: str = "wood_dragon_0.91",
    use_http: bool = True,
    stream_prompt: str = "Strike X flush plan",
    phase_rho: bool = False,
) -> Dict[str, Any]:
    t0 = time.time()

    async def phase0():
        return local_step(coherence, phase, 0.0, dt)

    async def phase1():
        return local_mesh(nodes, phase, 1.0 / PHI)

    async def phase2():
        b = branch or "B"
        return {
            "phase_id": 2,
            "name": "dispatch",
            **(
                await dispatch_cycle(
                    branch=b,
                    coherence=coherence,
                    phase=phase,
                    use_deepseek=True,
                )
            ),
            "status": "ok",
        }

    async def phase_rho_task():
        return local_rho_phase(phase, t=0.0)

    tasks = [phase0(), phase1(), phase2()]
    if phase_rho:
        tasks.append(phase_rho_task())
    if use_http and mcp_url:
        tasks.append(http_pulse(mcp_url, garden_secret, branch))
    if use_http and base_url:
        tasks.append(http_stream_collect(base_url, stream_prompt))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    phases: List[Dict[str, Any]] = []
    errors: List[float] = []
    for r in results:
        if isinstance(r, Exception):
            phases.append({"status": "error", "error": str(r)})
            continue
        phases.append(r)
        if isinstance(r, dict) and "error" in r and isinstance(r["error"], (int, float)):
            errors.append(float(r["error"]))
        elif isinstance(r, dict) and "coherence" in r:
            errors.append(1.0 - float(r["coherence"]))
        elif isinstance(r, dict) and r.get("name") == "rho" and "rho_error" in r:
            errors.append(float(r["rho_error"]))

    e_batch = sum(errors) / len(errors) if errors else (1.0 - coherence)
    pid = pid_update(e_batch, dt)
    ok = all(p.get("status") == "ok" for p in phases if isinstance(p, dict))

    return {
        "ts": time.time(),
        "elapsed_s": time.time() - t0,
        "atomic": True,
        "all_ok": ok,
        "phases": phases,
        "pid": pid,
        "phase_rho": phase_rho,
        "seal": "SIMD_BATCH_STEP_OK" if ok else "SIMD_BATCH_STEP_PARTIAL",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="SIMD batch Garden step")
    p.add_argument("--coherence", type=float, default=0.99)
    p.add_argument("--phase", type=float, default=200.0)
    p.add_argument("--dt", type=float, default=1.0)
    p.add_argument("--nodes", type=int, default=7)
    p.add_argument("--branch", default=None, choices=[None, "A", "B", "C"])
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--mcp-url", default="http://localhost:8080")
    p.add_argument("--secret", default="wood_dragon_0.91")
    p.add_argument("--no-http", action="store_true", help="local phases only")
    p.add_argument("--phase-rho", action="store_true", help="include density field phase (8804)")
    p.add_argument("--leaky-i", type=float, default=None, help="seed leaky integral I")
    p.add_argument(
        "--leaky-i-path",
        default=None,
        help="read/write path for I (PVC mount; 8805)",
    )
    args = p.parse_args()

    load_leaky_i(args.leaky_i_path, args.leaky_i)

    out = asyncio.run(
        simd_batch_step(
            coherence=args.coherence,
            phase=args.phase,
            dt=args.dt,
            nodes=args.nodes,
            branch=args.branch,
            base_url=args.base_url,
            mcp_url=args.mcp_url,
            garden_secret=args.secret,
            use_http=not args.no_http,
            phase_rho=args.phase_rho,
        )
    )
    save_leaky_i(args.leaky_i_path)
    if args.leaky_i_path:
        out["leaky_i_path"] = args.leaky_i_path
        out["leaky_i_saved"] = _I
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
