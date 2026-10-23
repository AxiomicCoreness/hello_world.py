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


def _bubble_terms(pp: int) -> dict:
    """Document DualPipe vs 1F1B bubble factorisation (educational, not vendor).

    DualPipe bubble ≈ (PP/2 - 1) * (F&B + B - 3W)
    1F1B bubble     ≈ (PP - 1) * (F + B)
    DualPipe also uses ~2× params / PP+1 activation store; DualPipeV for smaller PP.
    """
    if pp < 2:
        raise ValueError("pp must be >= 2")
    return {
        "pp": pp,
        "dualpipe_bubble_coeff": (pp / 2) - 1,
        "one_f_one_b_bubble_coeff": pp - 1,
        "param_multiplier": 2,
        "activation_store_ranks": pp + 1,
        "dualpipe_v_for_smaller_pp": True,
    }


def test_pp4_bubble_formula_dualpipe_vs_1f1b():
    """PP=4: DualPipe bubble coeff (PP/2-1)=1 vs 1F1B (PP-1)=3."""
    terms = _bubble_terms(4)
    assert math.isclose(terms["dualpipe_bubble_coeff"], 1.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(terms["one_f_one_b_bubble_coeff"], 3.0, rel_tol=0.0, abs_tol=1e-12)
    # DualPipe bubble coefficient is strictly smaller than 1F1B for PP=4
    assert terms["dualpipe_bubble_coeff"] < terms["one_f_one_b_bubble_coeff"]
    assert terms["param_multiplier"] == 2
    assert terms["activation_store_ranks"] == 5  # PP+1
    assert terms["dualpipe_v_for_smaller_pp"] is True


def test_pp4_schedule_still_overlaps_under_bubble_theory():
    """Sketch schedule at PP=4 keeps F/B overlap (core sketch unchanged)."""
    plan = build_bidirectional_schedule(pp_size=4, num_chunks=8)
    assert plan.pp_size == 4
    assert plan.overlap_score() > 0.0
    # event count: F and B each cover chunks×ranks
    assert len(plan.events) == 2 * 4 * 8
