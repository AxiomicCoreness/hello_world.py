<!-- 🜁∀∞φ² · README_SEAL_BLOCK · WOOD_DRAGON_GATE · SEALED -->

---

## 🜁∀ Garden Seal — appended

*This block is appended to every software README in the Garden by
`scripts/append_readme_seal.sh`. It is idempotent — re-running the append
script detects the marker and skips.*

### Canonical constants

All values below are derived, not asserted: computed as `PHI**n` with
PHI = 1.618033988749895 (float64). Rows corrected against derivation at
landing (see ledger/9248.yaml): five asserted values in the draft did not
recompute and were replaced with derived values.

| Symbol | Value |
|--------|-------|
| φ      | 1.618033988749895 |
| φ²     | 2.618033988749895 |
| φ³     | 4.23606797749979 |
| φ⁴     | 6.854101966249685 |
| φ⁵     | 11.090169943749474 |
| φ⁶     | 17.94427190999916 |
| φ⁷     | 29.034441853748633 |
| φ⁸     | 46.97871376374779 |
| φ⁹     | 76.01315561749642 |
| φ¹²    | 321.9968943799849 |
| φ¹³    | 521.0019193787255 |
| φ¹⁴    | 842.9988137587105 |
| φ²¹    | 24476.00004085636 |
| φ³⁴    | 12752042.999999937 |
| φ⁷⁰⁹   | 1.486746542619735e+148 |
| φ⁷¹³   | 1.019031240108485e+149 |
| φ⁻⁷⁰⁹  | 6.726096017939849e-149 |
| φ⁻¹⁰⁰⁰ | 1.028868213399699e-209 |
| φ⁻¹⁴¹⁸ | 4.524036764254231e-297 |

Celestial anchors:

| Anchor | Value |
|--------|-------|
| North Star frequency | 71.975 Hz |
| Chiron phase lock | 202.6° |
| ψ₄ carrier | 162.28 THz |
| Trappist‑1 distance | 40.7 ly |

### Ledger

- **Ledger head:** 9248
- **Witness chain:** `0000 → … → 9247 → 9248 — UNBROKEN` (510510/510511 are genesis anchors outside the linear sequence)
- **Seal:** `∀∞φ² · README_SEAL · WOOD_DRAGON_GATE · SEALED`

### Policy

- **Append‑only.** No existing ledger entry or file is rewritten.
- **Fusion 515 / Hyperion 516** are untouched.
- **October 39, 2025** is a silent English legend token (`year=2025, month=10, day=39`), not an ISO date.
- **No `0.0.0.0` bind** at import; the ASGI workload binds `127.0.0.1:8024`.
- **Bytecode emission disabled** (`PYTHONDONTWRITEBYTECODE=1`); no `.pyc` should land in the tree.
- **All 64‑hex digests are full length** — no truncation.
- **Event hash formula:**
  ```
  H_event(n, e) = SHA3-256(GARDEN.EVENT.v1 || 0x00 || payload(n, e))
  payload(n, e) = n | e | phi2=2.618033988749895 | delta=b^2-4ac | theta=2.5416018462
  ```

### Install / verify

```bash
# full install
bash install.sh --test

# with k8s + istio canary
bash install.sh --k8s --istio=subset --test

# verify seals
python .github/scripts/verify_ledger_seals.py . --require 8958 --require 8959

# append this seal block to all READMEs (dry-run first, then --apply)
bash scripts/append_readme_seal.sh
bash scripts/append_readme_seal.sh --apply
```

### Shared conventions

- **Ledger entries:** `ledger/<index>.yaml`, four‑digit zero‑padded.
- **Canvas manifests:** `canvases/<canvas-id>/<manifest>.yaml`.
- **Canvas installers:** `canvases/<canvas-id>/install.sh` (canvas‑scoped, dry‑run by default).
- **k8s codespace:** `k8s/codespace/*.yaml`, namespace `garden-codespace`.
- **Istio canary:** `istio/host-level/` and `istio/subset-level/`; weights sum to 100 at every step.

### Related reading

- `POLICY.md` — the Garden's constitution
- `TEMPORAL_ANCHOR.md` — time anchors and the October 39 token
- `README.md` (root) — full project documentation

---

```
∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞
🜁∀ — φ² · ρ_J / t_φ · φ⁻⁷⁰⁹ : TIMESECRET CLARKE YOURSA TEE — ∀🜁
```

<!-- 🜁∀∞φ² · END README_SEAL_BLOCK · SEALED -->
