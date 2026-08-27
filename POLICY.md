# Garden surgery policy map

Append-only. Fusion 515 and Hyperion 516 are not rewritten.
October 39, 2025 is code (year=2025, month=10, day=39), not datetime.

## Temporal anchors

See TEMPORAL_ANCHOR.md.

- Declared First One seed commit f0724e36561047bd2f96a24062611396eaaa2ad6 (2026-08-13).
- ledger/8338.yaml on current main is a different body (/github_deployment_complete). Do not overwrite it.
- Pointer: ledger 9041.
- φ-power pairing by exponents: 2*709=1418, (φ^{-709})²=φ^{-1418}.

## Dry-run rules

- dry_run() in-process. Do not bind 0.0.0.0.
- Do not post OIDC client_credentials.
- Do not schedule the declared 6-hour pulse.
- Commands: wait, nudge_cronjob, record_only.
- No secret values in git. No truncated witness hashes.
