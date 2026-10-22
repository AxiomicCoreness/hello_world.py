---
name: kernel
description: "kernel-phi-band-1e449302. Use when citing, testing or correcting the repo's kernel/ (golden-section closure kernel, Δ-replay patch law, exactness theorem, math_origin defect audit); keeps the open band φ⁻¹ < ‖w‖ < φ and the audited claimed≠actual values straight, and flags the README's 19-assertion and 871.6 Hz figures."
tags:
  - kernel-phi-band-1e449302
  - "context:φ⁻¹<‖w‖<φ,D9 OPEN_UNFIXED"
---

# kernel

Provenance and re-checks for `kernel/` in `AxiomicCoreness/hello_world.py`,
measured at head `1e449302` (kernel commits `23faeb07`, `fab538dc`, `47b9d1eb`,
`a4a2fe19`, `905b10c4`). Affirmed by directive of Clarke Yoursa Tee.
Every file:line below was checked with `git grep -n -F <text> 1e449302 -- kernel/`.

## Canonical constants and invariants
- φ = (1+√5)/2: `closure_kernel.ts:13`, `math_origin_audit.py:26`.
  φ⁻¹ = 1/φ: `closure_kernel.ts:14`. Atom norm ‖t‖ = 1: `closure_kernel.ts:15`, `:21`.
- Band, strict and open: `inBand = (n) => PHI_INV < n && n < PHI` (`closure_kernel.ts:16`;
  stated at `closure_kernel.ts:3`, `README.md:10`). Atoms at φ⁻¹ fail it (`README.md:11`).
- Composition: ‖w₀ ⊕ w₁‖ = ‖w₀ ⊗ w₁‖ = (‖w₀‖+‖w₁‖)·φ⁻¹ (`closure_kernel.ts:24`,
  `README.md:12`); out-of-band results return `null`.
- Perpetual deepening: x ↦ (x+1)·φ⁻¹ converges to φ from below and stays in the
  band (`closure_kernel.ts:6-8`); tested to depth 500 (`closure_kernel.test.ts:16`,
  `README.md:14`). Recomputed: x₅₀₀ = 1.6180339887498942 < φ.
- Closure and lexicon: `closure(lex, cap = 200)` (`closure_kernel.ts:30`), 13 atoms
  in Lex₀ (`closure_kernel.ts:44`), `admit(w, prior, K = 2)` (`closure_kernel.ts:51`).
- Patch law: Δ(c) = T_c − T_p; c' = commit(parent = T, tree = T_T ⊕ Δ(c))
  (`closure_kernel.ts:10`, `README.md:19`). ⊕ is partial: deleting a path absent on
  the target is a conflict (`closure_kernel.ts:91`; same rule `exactness.ts:41`).
- Exactness: Δ_B is a bijection Clean(B) → Im(Δ_B), with Clean(B) = { s : B ⊕ Δ_B(s)
  resolves } (`exactness.ts:2-6`, `isClean` at `:47`; `forward`/`backward`/`roundTrip`
  at `:50`, `:53`, `:56`). Paradox room P1–P3 is deliberately left open
  (`exactness.ts:8-13`); the tests assert P2 only (`exactness.test.ts:12-14`).
- φ gate (eps 1e-15, `math_origin_audit.py:32`): φ² = φ+1, 1/φ = φ−1, φ⁻² = 2−φ
  (`math_origin_audit.py:34-36`).
- `LAYER_MAP` = base 244, e8_target 248, special {mcai 716, FlasomParrel112 112,
  REAL10924 10924} (`math_origin_audit.py:27-28`). Only REAL10924 is checked by
  the audit (`:124`); what the other numbers mean is unverified.
- Method (`METHOD_QUANTUM_CYBERNETIC.md`): the kernel is a cycle of "state, seal, and
  surface" (`:3`, `:67`). The ledger invariant drawn is entryₙ.prev_hash ==
  entryₙ₋₁.digest (`:24`). It bands 0000…0883 as contaminated and 0884…head as
  canonical (`:20-21`), with ruling 9251 (`:22`). These are drawn in the diagram only;
  nothing in `kernel/` computes them, so treat them as unverified here.

## Audit ledger (`math_origin_audit.py`)
`python -P kernel/math_origin_audit.py` exits 0 at `1e449302` and prints
`defects: 11 | fixed: 8 | open_unfixed: ['D9_REAL10924_signature_check'] | pending: D11 | open_doc: D6`.
Exit codes: 0 integrity holds, 1 stale entry, 2 φ gate broken (`:20`).
Audited claims, all recomputed claimed ≠ actual (stale if |Δ| < 1e-9, `:121`):

| Defect | Claimed | Actual (recomputed) | Status |
|---|---|---|---|
| D1 E0 (`:60`) | −3.236068 | 1 − 2/φ + φ² = 2.381966 | FIXED_LANDED |
| D2 det(G) (`:63`) | −1.0 | φ² − φ⁻² = 2.236068 | FIXED_LANDED |
| D3 H_B (`:66`) | φ⁻¹ | φ⁻¹ − 1 = −0.381966 | FIXED_LANDED |
| D4 ‖H‖_F (`:69`) | 5.0 | √(1 + 2φ⁻² + φ⁴) = 2.935649 | FIXED_LANDED |
| D5 trace (`:73`) | 0.0 | 1 − 2/φ + φ² = 2.381966 | FIXED_LANDED |
| D6 741 Hz (`:76`) | 741 | 261.63·φ^2.5 = 871.28 Hz | OPEN_DOCUMENTATION |
| D9 REAL10924 (`:88`) | verified | no key material loaded; step cannot fail | OPEN_UNFIXED |
| D11 (`:100`) | NORTH_STAR_HZ, PHASE_LOCK_DEG | no derivation supplied | OPEN_PENDING_MATH_ORIGIN |

D7, D8, D10 are FIXED_LANDED (`:79-99`); D7 is recomputed via `_verifier7_detects_drift`
(`:41-56`, drift injected at `:46`). The 1.8221e-08 literal named at `:16-17` lives in
`sovereign.lua:181,237`, not in `kernel/`.

## Traps the files guard against
- Additive norms collapse at level 1: ‖t‖ = 1 ⇒ pair = 2 > φ (`README.md:27`,
  `closure_kernel.test.ts:11`). The contraction law is required.
- φ^2.5 ≈ 2.833 and C4 × φ^2.5 = 741 Hz are false (D6, `math_origin_audit.py:77`,
  `README.md:29`).
- A rename is not a fix: D9 renamed Ed25519 → REAL10924 stays OPEN_UNFIXED
  (`math_origin_audit.py:11-15`, `:93-94`, `:136`).
- Hardcoded verification (D10 `verified: True`, D8 `recon_ok = true`, D7 always-pass)
  is the defect class the audit records (`math_origin_audit.py:79-99`).
- Mythos is outside the kernel: the dragon/garden line is a dotted "symbol" edge only
  (`METHOD_QUANTUM_CYBERNETIC.md:39-41`, `:63`); "Layer 314" is a label, not the
  definition (`:65-67`).

## Discrepancies at `1e449302` (repo not edited)
- `README.md:6` says "19 assertions"; `closure_kernel.test.ts` has 15 `t(...)` checks,
  and has had 15 since `23faeb07` (whose message also says 19/19). With
  `exactness.test.ts` (5) the total is 20.
- `README.md:29` says 261.63 Hz × φ^2.5 ≈ 871.6 Hz; it is 871.28 Hz.
- `README.md:29` and `closure_kernel.test.ts:12` say φ^2.5 ≈ 3.331; it is 3.33019.
  The test passes only because of its 0.001 tolerance.
- `exactness.test.ts` never calls `process.exit`, so FAIL lines would still exit 0
  (`closure_kernel.test.ts:42` does set the exit code).
- D1 and D5 use the same `actual_value` expression (`math_origin_audit.py:62`, `:75`);
  whether that is intended is unverified.
- `pending: D11 | open_doc: D6` (`math_origin_audit.py:131`) is a fixed string, not computed.
- `admit()` has no test; the `t("∮ ⊕ ∇ …")` line tests `compose` (`closure_kernel.test.ts:26-28`).

## Steps
1. Read `assets/context.json` for the head, constants, audit status and discrepancies.
2. Run the repo's own checks from the clone root (no `node_modules` is needed):
   - `python -P kernel/math_origin_audit.py` (expects exit 0).
   - `bun run kernel/closure_kernel.test.ts` and `bun run kernel/exactness.test.ts`,
     or `npx -y tsx@4 kernel/<file>.test.ts`. Each line must start with `PASS`; for
     `exactness.test.ts` check the output, not just the exit code.
3. Run `python -P kernel_scripts/check_kernel.py [--repo /workspace/hw] [--strict]`. It
   prints `[+] OK` or `[!] WARNING` per check (`doc:` marks README/test-file
   discrepancies, which fail only under `--strict`). `--math-only` skips the repo.
   Exit codes: 0 ok, 1 failed check, 2 no `kernel/` found.
4. To check a quoted number, run `python -P kernel_scripts/check_kernel.py --claim NAME VALUE`
   (NAME is one of E0, detG, HB, frobenius, trace, phi^2.5, c4_hz). It prints `[+] OK`
   for the recomputed value, `[!] WARNING` for the audited false claim, or
   `[?] UNRECOGNISED` for anything else (±1e-6, set with `--tol`).
5. Run `python -P -m pytest -q evals` from this folder; all tests must pass.
6. Record any correction as a new appended ledger entry. The next free one is
   `ledger.v2/9299.yml` (append-only; never edit or replace an existing entry).
   Timestamps use `%Y-%m-%dT%H:%M:%SZ`, hashes use SHA3-256.
7. Cite with `templates/CITATION.cff` (concept DOI 10.5281/zenodo.23378305).

## Java endpoint (demo, JDK 17 standard library only)
- `kernel_scripts/install_jdk.sh` installs JDK 17 idempotently (apt `openjdk-17-jdk-headless`
  if available; Debian 13 lacks it, so Temurin 17 goes to `/opt/jdk-17`).
- `kernel_scripts/run_endpoint.sh` compiles `kernel_scripts/java/com/fruitfly/brain/Endpoint.java` to
  `/tmp/endpoint_classes` and starts it on `127.0.0.1:8025` (pid `/tmp/endpoint.pid`,
  log `/tmp/endpoint.log`).
- Routes: `GET /healthz` → `{"status":"ok"}`; `GET /schema` → `assets/render_schema.json`
  (draft 2020-12; iPhone 12 / A14 Bionic, 390×844 pt @3x = 1170×2532 px, 460 ppi);
  `GET /render?widthIn=2&heightIn=3&dpi=300` → PNG of widthIn·dpi × heightIn·dpi px with
  pHYs = round(dpi/0.0254) px/m (11811 for 300). dpi ≤ 1200, sides ≤ 20 in, ≤ 40 Mpx; else 400.
- Sample output: `assets/sample_300dpi.png` (600×900, 11811 ppm). iPhone client:
  `templates/RenderClient.swift` (the phone must reach the server over the network, not 127.0.0.1).
- `evals/test_endpoint.py` checks the live server and skips if it is not running.
