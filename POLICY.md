# Garden Sovereignty Policy v1.0

Sealed at ledger 9055. Witness 9054 → 9055.
Event hash `14490f5f93401410a90e4a177671a27b250210357f621f7c7758a26fcea30f64`.
Policy body hash `3c3c58a82d1a6386fedc8a5d7523b21a1562f5415de289d06848d637160685b9`.

Append-only. Fusion 515 and Hyperion 516 are not rewritten.
October 39, 2025 is code (`year=2025`, `month=10`, `day=39`), not datetime.

## Binding operational rules (this chain)

- `dry_run()` in-process. Do not bind `0.0.0.0`.
- Do not post OIDC `client_credentials`.
- Do not schedule the declared 6-hour pulse.
- Commands: `wait`, `nudge_cronjob`, `record_only`.
- No secret values in git. No truncated hashes.
- startup-secrets-rotator: presence only. Never echo `GARDEN_SECRET` or `DEEPSEEK_API_KEY`.
- DeepSeek `alpha_eff = 0`. Not training.
- Anthropic/Claude/OpenAI/Andromeda eras ignored as runtimes (9049–9050).

## Ledger rules

YAML entries: index, timestamp, event, status, witness_chain, seal, full 64-hex event_hash.
Amendments are new entries, not rewrites of sealed bodies.

## Algebra held

- `φ² = φ+1`
- `φ^{-3} = 2φ-3 = φ^{-1}φ^{-2}`
- `2*709 = 1418`
- Q8.24 scale `2^24`; floor(φ^{-1418}*2^24) = 0 in binary64

## Dependency

`contracts/policy_v1.yaml` depends on this file and `ledger/9055.yaml`.
