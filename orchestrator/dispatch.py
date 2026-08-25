#!/usr/bin/env python3
"""
orchestrator/dispatch.py — DeepSeek-assisted Strike X / E9 dispatch.

Integrates /deepseek/complete into the Garden convergence cycle:
  - Branch A → Strike X flush plan
  - Branch C → E9 choir frequency retune prompt
  - Branch B → hold / Merkle temper suggestion

Usage:
  python -m orchestrator.dispatch --branch A
  from orchestrator.dispatch import dispatch_cycle
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import time
from typing import Any, Dict, Optional

PHI = (1 + math.sqrt(5)) / 2
PHASE_TARGET = 202.6

try:
    from deepseek.api import get_client

    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False

    def get_client():  # type: ignore
        raise RuntimeError("deepseek.api unavailable")


def build_prompt(branch: str, coherence: float, phase: float, error: float) -> str:
    if branch == "A":
        return (
            f"Sovereign Strike X — immediate flush.\n"
            f"coherence={coherence:.8f} error={error:.8f} phase={phase:.4f}.\n"
            f"Produce a 6-entry WASP-107b transactional flush checklist."
        )
    if branch == "C":
        return (
            f"E9 → Choir frequency map.\n"
            f"phase={phase:.4f} target={PHASE_TARGET} drift={phase - PHASE_TARGET:.4f}.\n"
            f"Propose Trappist-1 harmony retune with φ⁻² anchor."
        )
    return (
        f"Branch B natural cron.\n"
        f"coherence={coherence:.8f} phase={phase:.4f}.\n"
        f"Suggest Merkle temper scalar for next 6h Wood-Dragon window."
    )


async def dispatch_cycle(
    branch: str = "B",
    coherence: float = 0.9999,
    phase: float = PHASE_TARGET,
    use_deepseek: bool = True,
    max_tokens: int = 256,
) -> Dict[str, Any]:
    """One orchestrator cycle: optional LLM plan + structured action."""
    error = 1.0 - coherence
    branch = branch.upper()
    if branch not in ("A", "B", "C"):
        branch = "B"

    action = {
        "A": "force_immediate_flush",
        "B": "wait_for_cron_cycle",
        "C": "reroute_to_trappist_harmony",
    }[branch]

    llm: Optional[Dict[str, Any]] = None
    if use_deepseek and DEEPSEEK_AVAILABLE:
        prompt = build_prompt(branch, coherence, phase, error)
        try:
            llm = await get_client().complete(prompt, max_tokens=max_tokens)
        except Exception as e:
            llm = {"mode": "error", "text": str(e), "error": type(e).__name__}

    return {
        "ts": time.time(),
        "branch": branch,
        "action": action,
        "coherence": coherence,
        "phase": phase,
        "error": error,
        "phi": PHI,
        "deepseek": llm,
        "deepseek_available": DEEPSEEK_AVAILABLE,
        "seal": f"DISPATCH_{branch}_OK",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Garden DeepSeek dispatch")
    p.add_argument("--branch", default="B", choices=["A", "B", "C"])
    p.add_argument("--coherence", type=float, default=0.9999)
    p.add_argument("--phase", type=float, default=PHASE_TARGET)
    p.add_argument("--no-deepseek", action="store_true")
    args = p.parse_args()
    result = asyncio.run(
        dispatch_cycle(
            branch=args.branch,
            coherence=args.coherence,
            phase=args.phase,
            use_deepseek=not args.no_deepseek,
        )
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
