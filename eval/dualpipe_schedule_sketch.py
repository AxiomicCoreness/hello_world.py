#!/usr/bin/env python3
"""Clarke Yoursa Tee

DualPipe-inspired *schedule sketch* — from-scratch, CPU-only, no vendor.

Upstream DualPipe (deepseek-ai/DualPipe) is a *training* bidirectional
pipeline-parallel scheduler. It was evaluated and **deferred** from
``.gitmodules`` / ``vendor/`` (inference stack priority: DeepGEMM,
FlashMLA, DeepEP, DeepSelect). This file is an original educational
rewrite of the *idea* of overlapping forward on one microbatch with
backward on another — it does **not** import DualPipe, does **not**
require NCCL/CUDA, and is **not** a git submodule.

Inspired by the public DualPipe README / examples/example_dualpipe.py
concepts (bidirectional PP, microbatch chunks, F/B overlap). No
substantial upstream source is copied.

Run:
  PYTHONPATH=. python eval/dualpipe_schedule_sketch.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple


PHI = (1.0 + math.sqrt(5.0)) / 2.0


@dataclass
class Microbatch:
    """One pipeline microbatch token."""

    index: int
    value: float


@dataclass
class ScheduleEvent:
    """One scheduled unit of work on a rank."""

    rank: int
    kind: str  # "F" forward | "B" backward
    microbatch: int
    t: int  # discrete time slot


@dataclass
class DualDirectionPlan:
    """Bidirectional PP plan: forward stream + reverse backward stream."""

    pp_size: int
    num_chunks: int
    events: List[ScheduleEvent] = field(default_factory=list)

    def overlap_score(self) -> float:
        """Fraction of time slots where some rank runs F while another runs B."""
        by_t: dict[int, set[str]] = {}
        for e in self.events:
            by_t.setdefault(e.t, set()).add(e.kind)
        if not by_t:
            return 0.0
        overlapped = sum(1 for kinds in by_t.values() if "F" in kinds and "B" in kinds)
        return overlapped / len(by_t)


def build_bidirectional_schedule(pp_size: int, num_chunks: int) -> DualDirectionPlan:
    """Build a toy bidirectional schedule (not production DualPipe).

    Rank r runs forward for chunk c at time roughly (c + r), then
    backward for chunk c in reverse order overlapping the next forwards.
    This is a *sketch* of F/B overlap, not bit-identical to DualPipe.
    """
    if pp_size < 1 or num_chunks < 1:
        raise ValueError("pp_size and num_chunks must be >= 1")
    plan = DualDirectionPlan(pp_size=pp_size, num_chunks=num_chunks)
    # Forward wave (left → right)
    for c in range(num_chunks):
        for r in range(pp_size):
            plan.events.append(ScheduleEvent(rank=r, kind="F", microbatch=c, t=c + r))
    # Backward wave (right → left), shifted to overlap mid-pipeline
    t0 = num_chunks  # start B after first F wave fills
    for c in range(num_chunks - 1, -1, -1):
        for r in range(pp_size - 1, -1, -1):
            # offset so B on high ranks overlaps F on low ranks for later chunks
            t = t0 + (num_chunks - 1 - c) + (pp_size - 1 - r)
            plan.events.append(ScheduleEvent(rank=r, kind="B", microbatch=c, t=t))
    return plan


def cpu_ref_chunked_mse(
    xs: List[float], targets: List[float], chunks: int
) -> Tuple[float, List[float]]:
    """Reference chunked forward+loss (CPU), analogous to DualPipe ref_step spirit."""
    if len(xs) != len(targets) or chunks < 1 or len(xs) % chunks != 0:
        raise ValueError("xs/targets length must match and divide evenly by chunks")
    n = len(xs) // chunks
    preds: List[float] = []
    losses: List[float] = []
    for i in range(chunks):
        sl = slice(i * n, (i + 1) * n)
        # toy "stage": y = φ·x (stand-in for a PP stage linear)
        chunk_pred = [PHI * x for x in xs[sl]]
        chunk_loss = sum((p - t) ** 2 for p, t in zip(chunk_pred, targets[sl])) / n
        preds.extend(chunk_pred)
        losses.append(chunk_loss)
    mean_loss = sum(losses) / len(losses)
    return mean_loss, preds


def verify_sketch(pp_size: int = 4, num_chunks: int = 8) -> dict:
    """Self-check: schedule non-empty, overlap > 0, CPU ref uses math.isclose."""
    plan = build_bidirectional_schedule(pp_size, num_chunks)
    score = plan.overlap_score()
    xs = [float(i) for i in range(16)]
    targets = [PHI * x for x in xs]  # perfect model → loss ~ 0
    loss, preds = cpu_ref_chunked_mse(xs, targets, chunks=4)
    loss_ok = math.isclose(loss, 0.0, rel_tol=0.0, abs_tol=1e-12)
    pred_ok = all(math.isclose(p, t, rel_tol=0.0, abs_tol=1e-12) for p, t in zip(preds, targets))
    return {
        "deferred_vendor": True,
        "submodule": None,
        "pp_size": pp_size,
        "num_chunks": num_chunks,
        "n_events": len(plan.events),
        "overlap_score": score,
        "overlap_positive": score > 0.0,
        "cpu_ref_loss_ok": loss_ok,
        "cpu_ref_pred_ok": pred_ok,
        "phi": PHI,
        "ok": score > 0.0 and loss_ok and pred_ok and len(plan.events) > 0,
    }


def main() -> None:
    import json

    result = verify_sketch()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
