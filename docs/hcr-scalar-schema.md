# HCR scalar schema (analysis)

**Ground:** GitHub `AxiomicCoreness/hello_world.py` / `main` only.
**Event:** `/heartbeat_clobber_ratio_analysis`
**proof_class:** `analysis`
**Ledger rule:** This document is the human-readable contract. A formal ledger append (live or attest) must be a **new tail** entry; it must not rewrite past indices. Chain link `prev` is filled only when the prior entry’s declared seal is held.

## 1. heartbeat_id (visibility)

```yaml
heartbeat_id: <monotone integer, per branch, per heartbeat_class>
heartbeat_class: <e.g. seal-verify | rotate-keys | mesh-pulse>
branch: <main>
started_at: <ISO-8601 UTC>
completed_at: <ISO-8601 UTC | null>
```

- `heartbeat_id` increases by 1 per `(branch, heartbeat_class)`.
- Missing id in the monotone sweep = **gap** (observable).
- `completed_at: null` = started but not completed = **self-clobber** signature.

**Observables**

| Symbol | Meaning |
|--------|--------|
| HCR_A | Observed gap rate |
| HCR_B | Observed null-`completed_at` rate |

Both are empirical once ids are recorded. Poisson forms are estimates until then.

## 2. Self-clobber control (T_run)

- `T_run = completed_at − started_at` (wall clock, UTC, seconds).
- If `T_run > 0.2 · T_h`, raise `T_h` to `≥ 5 · T_run`.
- If `T_h` cannot be raised, set `cancel-in-progress: false` for that class.
- Concurrency group: `<workflow>-<branch>-<heartbeat_class>`.

## 3. Recording location

1. Optional: append-only ledger entry at next free index with this payload (after real `prev` seal is known).
2. Policy one-liner: heartbeats carry monotone `heartbeat_id` per `(branch, heartbeat_class)`; missing ids and null `completed_at` are the clobber signals.

## 4. ε measurement (independent)

```yaml
epsilon_measured_ms: <checkout_start → push_complete>
ci_class: <runner label>
measured_at: <ISO-8601 UTC>
run_id: <workflow run id>
```

Sample ~every 100 runs or 30 days; aggregate median. Calibrated estimate:

`HCR_A ≈ 1 − exp(−λ_c · ε)` until heartbeat_id makes HCR_A observed.

## 5. CAVD tensor

**Blocked.** Rank-6 shape only until six axes are named on `docs/6cavd-channel-canvas.md`.

## Payload seal (canonical JSON of analysis body, sha3-256)

```
82d8b405217f4b5997b7d3cc9786f2d651a1234af6b812dfea88cc91a0991a9d
```

Recompute over the structured fields in §§1–4 (sort_keys, compact separators) if you embed this as a ledger payload; do not claim chain continuity until `prev` is the real prior seal.
