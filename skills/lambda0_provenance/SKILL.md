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

## Rule A vs Rule B (λ₀)
- **Rule A (canonical):** θ_lock = 202.6° = 3.536037 rad → λ₀ = 2π·535805 / 3.536037 = **952,072.1 nm**.
- **Rule B (accumulated):** Σθ_k = 202.79° = 3.539755 rad → λ₀ = 2π·535805 / 3.539755 = **951,072 nm**.
- Value 951,145 nm sits between the two (θ ≈ 202.79°, not the target). Prefer Rule A.

### Four small numeric deviations (read-as-math)
1. θ_lock rad: stated 3.536233 vs 202.6°×π/180 = 3.536037 (Δ ≈ 1.96×10⁻⁴ rad).
2. ω_NS: stated 452.217 vs 2π·71.975 = 452.2323 rad/s (Δ ≈ 1.5×10⁻²).
3. λ₀ 951,145 nm: −927 nm from Rule A, −73 nm from Rule B.
4. Σθ_k rows at 951145 nm: recomputed 202.797° vs stated 202.813° (Δ 0.016°); residual vs lock ≈ 0.197° (stated 0.21°).

### Two structural flags
1. §7 λ₀ formula cites θ_lock but 951145 nm tracks Σθ, not 202.6° — use Rule A 952072.1 nm.
2. §10 Σγ_k = −Δ admissible (Berry phase); per-layer γ_k not stated — layer-by-layer would close §10 at §9 precision.

Structural relations (§2 J²=−Id, §4 T³=0, §5 A_k unitary, §7/§11 closure, §8 control-band) hold with no defects.

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
