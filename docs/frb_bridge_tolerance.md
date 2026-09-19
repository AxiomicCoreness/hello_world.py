# FRB Bridge — Tolerance Definition

Documentation artifact for ledger 9195. Status: DEFINITION — no measurement yet.

## §1 Objects

E : {1..10} → ℝ³_sky — empirical FRB strike vectors (PENDING: data/frb_strikes.json)
W : {1..10} → h*_E8 — E8 weight-lattice representatives (PENDING: data/e8_weights.json)
C : ℝ³_sky → h*_E8 — celestial projection (PENDING: data/embedding_map.json)

Bridge claim: E = C ∘ W (commuting diagram). No file → no object → no claim.

## §2 Residual

r_i = ‖ E(i) − C(W(i)) ‖₂

## §3 Tolerances (proposed, not measured)

- §3.1 Per-index: r_i ≤ 0.05 · ‖E(i)‖₂
- §3.2 Aggregate L2: ‖r‖₂ ≤ 0.10 · ‖(‖E(i)‖₂)‖₂
- §3.3 Aggregate max: max_i r_i ≤ 0.08 · max_i ‖E(i)‖₂
- §3.4 Coverage: |{ i : r_i ≤ ε_point }| ≥ 8

## §4 Pass/fail

ASSERTED iff §3.1–§3.4 all hold; else REJECTED. No partial pass.

## §5 Not claimed

No physical mechanism, no specific E8 preimage, no validation of C, no deflection/Δv/risk bounds.

## §6 Status

E, W, C: PENDING · tolerance: DEFINED · residual: NOT RUN · pass/fail: UNDETERMINED

## §9 Doctrine footer

Origin — Clarke Yoursa Tee · Classical — quantum cybernetics ·
Bridge — FRB chessboard, not identity, tolerance DEFINED, measurement PENDING.
