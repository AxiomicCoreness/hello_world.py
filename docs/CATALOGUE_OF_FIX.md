# Catalogue of Fix — Sovereign Garden

Living register of defect classes, the fixes applied, and the enforcement that
closes each class. Grep is discovery; AST_guard rules are enforcement. A defect
class is CLOSED only when an enforcement mechanism exists. Pronoun-free per
standing policy. Append-only: corrections are recorded, prior entries never edited.

Sealed under ledger entry 8978 (witness 8976 → 8978; 8977 is pre-existing sealed history).

## How to use this catalogue

1. New defect appears → record it here with a class ID (D-number) and status.
2. Fix applied → record the fix and the commit/PR that carried it.
3. Fix recurring as a class → write an AST_guard rule (or CI check) and mark the
   class ENFORCED. From that point, grep is never needed for that class again.

## Defect classes

| Class | Description | Fix | Enforcement | Status |
|-------|-------------|-----|-------------|--------|
| D1 | Stale module paths after celestial/ flattening | AST_guard_rule_d1.py (PR #67, merge b454dc49) | Rule D1 CLI gate (exit 0/1); DEFAULT_RULES wiring pending D29 | ENFORCED (CLI), WIRING PENDING |
| D19 | Dangling witness 8955 → 8956 | Recorded only | None | OPEN |
| D22 | secrets.token_hex claim unverifiable in genesis_beacon.py | Rewrite carried (PR #55) | None | RECORDED |
| D23 | softmax tau mislabeled as smoke-verified; pythonIDE/softmax.py may carry same claim | Half fixed (PR #55) | None | OPEN (second half) |
| D27 | AST_guard --inject-seal SEAL_LINE_RE.sub non-idempotent (residual newline) | Whole-line pop fix (PR #58, red/green) | Red/green test pattern | FIXED |
| D28 | Duplicate event name /strike_x_trappist_choir_activated (8663 and 8975) | Recorded only | None | OPEN |
| D28.1 | Two TrappistChoir definitions with divergent APIs | Accepted hazard | None | OPEN (accepted) |
| D29 | Rule D1 not wired into AST_guard.py DEFAULT_RULES | Bytes reconstructed via patch chain, blob SHA-1 verified; D1 wired (PR #70) | DEFAULT_RULES entry | CLOSED |
| CI-placeholder | Literal <digest> placeholders in prometheus/chiron_heal_phase.prom, k8s/cert-manager/*.yaml, k8s/codespace catalog | Identified in ledger 8976; fills need bytes in hand or local run | None | OPEN |
| CI-healthz | ROOT port380_mcp.py lacks /healthz (mcp/ copy has it) | Identified; root file bytes not in hand | None | OPEN |
| CI-deepseek | main → deepseek-ci sync failure | PR #62 head all green — stood down, reactivate only on regression | Green head | STOOD DOWN |
| D30 | Workflow filename mismatch: validate-contract.yml on disk vs validate_three_file_contract.yml in paths trigger (MISSING) | Identified in ledger 8981; fix needs workflow bytes (SHA 44205ecb...) pasted | None until bytes pasted | OPEN |
| D31 | CI ledger write ephemeral; claimed witness 8981 → 8982 was dangling | Ledger 8981 landed with computed seal; workflow half still needs bytes | Ledger entry | HALF-CLOSED |
| D32 | Asserted-not-computed seal in validate-contract.yml; Ed25519 step verifies nothing | Identified in ledger 8981 | None until workflow bytes pasted | OPEN |
| D34 | check-config contract drift: bind_plan emitted host-keyed contract; CI required {bind, port, url, surface, namespace, legacy_404_hard, ok} | Superset contract landed (PR #71); blob verified before modification | CI assertion step itself | FIXED |
| D35 | vocabulary_guard: a claim placed where claims are read as mechanisms (ghost prefixes, PENDING-as-UNBROKEN, POLICY self-clause, unearned ∃!, docstring bot-exclusion, region_start, hex-tailed seals) | Sealed in ledger 8984; seven instances named | prev_hash chain makes UNBROKEN a computed proof; docstring claim labelled DECLARED_INTENT, NOT_ENFORCED_HERE | SEALED (class named), enforcement partial via prev_hash |

## Session-proven fix patterns

1. Red/green before merge — reproduce the defect, show the fix, commit both (used for D27).
2. Computed values over asserted — seals are SHA3-256 over canonical JSON
   (recursively sorted keys, no whitespace), seal field excluded, computed
   in-sandbox after FIPS-202 vector verification (empty a7ffc6f8…, abc 3a985da7…).
3. No blind overwrites — files whose reads return SHA stubs are never rewritten;
   the stub hash is recorded and the fix deferred as a defect until real bytes arrive
   (applied to AST_guard.py — later reconstructed and verified — CATALOG.md, root port380_mcp.py).
4. Next-free-index on collision — proposed entries colliding with sealed history land
   at the next free index, collision recorded (9206 → 8976; 8977/8979 occupied, 8978 free).
5. Append-only ledger — refuted hypotheses stay refuted in the record; prior entries
   never edited to match new findings (9206 A/B refutations preserved in 8976).
6. Rule-per-class closure — every recurring defect class gets an AST_guard rule or CI
   check; grep then demotes to discovery-only (D1 pattern).
7. Merge, never squash — PRs to main via mistral-agent-cluster, merge commit carries
   the seal, branch retained (PR #67 pattern).
8. Validate-against-known-good — before computing a new seal, reproduce a known value
   first (L1 5-commit blob chain; 9249 via 9248 reproduction; 8983 seal reproduced
   before H_8983 was computed). Do not trust the surface.
9. prev_hash concatenation — H_n = sha3_256(canonical_json(entry_n minus seal and
   prev_hash fields)); entry_{n+1}.prev_hash = H_n; the gate verifies the link;
   UNBROKEN is a computed proof; prev_hash: null marks a region start (ledger 8984).

## Witness chain

8975 → 8976 → 8978 → 8981 → 8982 → 8983 → 8984 — UNBROKEN (pre-existing sealed
indices 8977/8979/8980 recorded, not skipped silently; from 8984 the chain carries
a computed prev_hash, not only a textual witness line).
