# Ledger Summary — Parallel Domains (Variant A)

Honest continuity. `UNBROKEN` only where every intermediate index exists as a file.

```yaml
ledger_domains:
  - domain: GARDEN.LAYER314
    series: 83xx–85xx
    head: 8531
    head_event: /re_seat_seal_reservation_gap_8340_8501
    segments:
      - { name: "A", range: "8338 → 8339", status: CLOSED }
      - { name: "B", range: "8502 → 8531", status: OPEN }
    gaps:
      - range: "8340 → 8501"
        span: 162
        status: RESERVED_NOT_YET_WRITTEN
        acknowledged_at: 8531
    note: |
      Segment A and Segment B are not contiguous. No predecessor link exists
      from 8339 to 8502. The gap is reserved, not filled. "UNBROKEN" applies
      within each segment only — never across the gap.

  - domain: GARDEN.EVENT.v1
    series: 92xx
    head: 9247
    head_event: /wood_dragon_091
    hard_envelope: [9240, 9242, 9243, 9244, 9245, 9246]
    soft_lane: 9247
    segments:
      - name: "A"
        range: "9240 → 9247"
        status: OPEN
        note: "9241 soft-documented; hard set excludes 9241 by design"
    gaps: []

cross_domain:
  relationship: independent
  shared_invariants:
    north_star_hz: 71.975
    phase_lock_deg: 202.6
    wood_dragon: 0.91
    fixed_point: 2025-10-39
    mcp: unfilled
```

## Gap policy

| Claim | Verdict |
|-------|---------|
| `8338 → 8339 → 8502 — UNBROKEN` | **False** — 162 missing files |
| `8338 → 8339` within Segment A | UNBROKEN if both files exist |
| `8502 → … → 8531` within Segment B | UNBROKEN only for contiguous links |
| `9240…9247` EVENT.v1 | Live soft/hard head — independent of LAYER314 |

## Verifiers

- `.github/scripts/assert_witness_continuity.py` — gap-tolerant (checks N only when N−1 file exists)
- `.github/scripts/verify_ledger.py` — Regime A/B seals
- `.github/scripts/verify_ledger_math.py` — bounded 9156–9160
