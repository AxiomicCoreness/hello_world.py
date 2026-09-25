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
| D29 | Rule D1 not wired into AST_guard.py DEFAULT_RULES | Blocked: AST_guard.py bytes missing from view (SHA e504dd1ead4cc60021c564615e6ca1e544b5972e) | None until bytes pasted | OPEN |
| CI-placeholder | Literal <digest> placeholders in prometheus/chiron_heal_phase.prom, k8s/cert-manager/*.yaml, k8s/codespace catalog | Identified in ledger 8976; fills need bytes in hand or local run | None | OPEN |
| CI-healthz | ROOT port380_mcp.py lacks /healthz (mcp/ copy has it) | Identified; root file bytes not in hand | None | OPEN |
| CI-deepseek | main → deepseek-ci sync failure, cause unnamed | Awaiting gh run view --log-failed tail | Log tail names the line | OPEN |
| D30 | Workflow filename mismatch: .github/workflows/validate-contract.yml on disk, but paths trigger references validate_three_file_contract.yml (MISSING) — workflow never fires on its own edits | Identified in ledger 8981; fix needs workflow bytes (SHA 44205ecb44a8ae88447db8457d3f48e21be66031) pasted | None until bytes pasted | OPEN |
| D31 | CI ledger write is ephemeral: validate-contract.yml step 7 writes ledger/8982.yaml to the runner disk with no commit/push step — entry never lands; claimed witness 8981 → 8982 dangling (8981 was MISSING on main before entry 8981 landed) | Identified in ledger 8981 | None | OPEN |
| D32 | Asserted-not-computed seal in CI: VALIDATE_CONTRACT_8982 seal is a hardcoded string, not SHA3-256 over canonical JSON; Ed25519 step verifies nothing (yaml.safe_load only) | Identified in ledger 8981 | None | OPEN |

## Session-proven fix patterns

1. Red/green before merge — reproduce the defect, show the fix, commit both (used for D27).
2. Computed values over asserted — seals are SHA3-256 over canonical JSON
   (recursively sorted keys, no whitespace), seal field excluded, computed
   in-sandbox after FIPS-202 vector verification (empty a7ffc6f8…, abc 3a985da7…).
3. No blind overwrites — files whose reads return SHA stubs are never rewritten;
   the stub hash is recorded and the fix deferred as a defect until real bytes arrive
   (applied to AST_guard.py, CATALOG.md, root port380_mcp.py).
4. Next-free-index on collision — proposed entries colliding with sealed history land
   at the next free index, collision recorded (9206 → 8976; 8977/8979 occupied, 8978 free).
5. Append-only ledger — refuted hypotheses stay refuted in the record; prior entries
   never edited to match new findings (9206 A/B refutations preserved in 8976).
6. Rule-per-class closure — every recurring defect class gets an AST_guard rule or CI
   check; grep then demotes to discovery-only (D1 pattern).
7. Merge, never squash — PRs to main via mistral-agent-cluster, merge commit carries
   the seal, branch retained (PR #67 pattern).

## Witness chain

8975 → 8976 → 8978 → 8981 — UNBROKEN (8977/8979/8980 pre-existing sealed history;
each session entry landed at the verified next free index).
