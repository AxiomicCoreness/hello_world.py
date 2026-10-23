---
name: lambda0_provenance
description: "s7-s11-lambda0-952072. Use when recalculating or citing the optical stack's lambda0 or phase lock; keeps canonical 952,072.1 nm distinct from the deprecated 952,057 nm draft and guards the phi*pi/2 = 145.623 deg phase trap."
tags:
  - s7-s11-lambda0-952072
  - "context:952072 nm,952057 区分"
---

# lambda0_provenance

Provenance and recalculation for the S7–S11 optical layer stack, anchored to
math origin 510510 and baseline 731 (commit `f8332804`). Affirmed by directive
of Clarke Yoursa Tee.

## Canonical values
- λ₀ = 360 · Σnₖtₖ / θ_lock = 360 · 535,805 / 202.600 = **952,072.1 nm** (f₀ ≈ 314.88 GHz).
- θ_lock = **202.600°**, an independent sealed design parameter.
- Deprecated: **952,057 nm** (Σθ = 202.603°). Never cite it as current, and warn
  when a commit references 952,057 nm without a `-draft` suffix.
- Alternative design branch: λ₀ = 951,145 nm gives Σθ = 202.797° (+0.197°).

## Context: North Star
- North Star **f★ = 71.975 Hz**, with phase lock **202.6°** (`assets/context.json`:
  `north_star_hz`, `phase_lock_degrees`). The repo spells it `north_star_freq` /
  `NORTH_STAR_HZ` / `NORTH_STAR_FREQ`; verified with `git grep` at `3bd60bc0`:
  - `.github/scripts/E2E _workflow_dispatch.py:746` `self.north_star_freq = 71.975`
  - `.github/scripts/verify_ledger.py:69` `NORTH_STAR_HZ = 71.975`
  - `celestial/quadratic_daemon.py:116` `NORTH_STAR_FREQ = 71.975`
  - `ENUMS.SCHEMA.TYPES.py:30` `NORTH_STAR_FREQ = 71.975`
  - `ledger.v2/9242.yml:10` `north_star_hz: 71.975`
- `batch_processor.py:186` computes `north_star_freq` as φ⁵·6.49 = 71.97520 Hz,
  an approximation, not the literal; cite 71.975 Hz.
- The North Star is a frequency constant, separate from λ₀/f₀ (≈ 314.88 GHz).
  Check it with `python3 scripts/recalc_optics.py --north-star [HZ]`
  (exit 1 when HZ ≠ 71.975).

## Phase trap
φ·π/2 = 2.5416018462 rad = **145.623°**, not 202.6°. The 2.5416 rad in the
Regime B seal is φπ/2; it does not derive the 202.6° lock.

## Steps
1. Read `assets/context.json` for the baseline, head, and anchor state.
2. Run `python3 scripts/recalc_optics.py --nkt-sum <nm> --theta-lock <deg>`.
   It prints one verdict: `[+] OK` (canonical), `[!] WARNING` (deprecated
   952,057 nm draft), or `[?] UNRECOGNISED` (neither, within ±1 nm).
3. Run `python3 -m pytest -q evals` from this folder (also works with
   `python3 -P`); all tests must pass.
4. Record any correction as a new appended ledger entry (append-only; never
   edit or replace an existing entry). Timestamps use `%Y-%m-%dT%H:%M:%SZ`,
   hashes use SHA3-256.
5. Cite with `templates/CITATION.cff` (concept DOI 10.5281/zenodo.23378305).

## Current correction
`ledger.v2/9289.yml` (`/drift_baseline_731_correction`, seal `544880da…3284`),
which chains after 9288.
