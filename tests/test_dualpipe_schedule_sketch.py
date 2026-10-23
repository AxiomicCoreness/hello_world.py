"""CPU-only DualPipe schedule sketch — no DualPipe submodule."""

from __future__ import annotations

import math

from eval.dualpipe_schedule_sketch import (
    PHI,
    build_bidirectional_schedule,
    cpu_ref_chunked_mse,
    verify_sketch,
)


def test_sketch_overlap_and_cpu_ref():
    out = verify_sketch(pp_size=4, num_chunks=8)
    assert out["deferred_vendor"] is True
    assert out["submodule"] is None
    assert out["ok"] is True
    assert out["overlap_positive"] is True
    assert math.isclose(out["phi"], PHI, rel_tol=0.0, abs_tol=1e-15)


def test_build_schedule_event_counts():
    plan = build_bidirectional_schedule(2, 3)
    assert len(plan.events) == 12
    assert plan.overlap_score() > 0.0


def test_cpu_ref_chunked_mse_perfect_model():
    xs = [1.0, 2.0, 3.0, 4.0]
    targets = [PHI * x for x in xs]
    loss, preds = cpu_ref_chunked_mse(xs, targets, chunks=2)
    assert math.isclose(loss, 0.0, rel_tol=0.0, abs_tol=1e-12)
    for p, t in zip(preds, targets):
        assert math.isclose(p, t, rel_tol=0.0, abs_tol=1e-12)
