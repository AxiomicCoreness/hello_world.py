# Immutable without exposing secrets

## Rules

1. **Digests are full length**
   - SHA-256 / HMAC-SHA256 / SHA3: **64 hex characters** (or full algorithm width).
   - Never truncate for display, logs, ledgers, or Grafana labels.

2. **Secrets never leave the boundary**
   - Do **not** export `OIDC_CLIENT_SECRET`, fallback tokens, or HMAC keys in:
     - `/metrics` or Prometheus labels
     - Grafana panels or annotations
     - `/status`, `/compression`, agent JSONL
     - ledger YAML
   - Allowed: `secret_len` (e.g. 64), `oidc_fallback_level`, `oidc_integrity`, optional **8-char prefix** only when needed for correlation.

3. **Immutability**
   - Ledger seals and commit SHAs are append-only references.
   - Once sealed, entries are not rewritten; corrections are new entries.

4. **Grafana**
   - Query gauges such as `hyperian_oidc_secret_len` (expect 64).
   - Never add a panel that plots or tables a secret string.

## Implementation anchors

| Surface | Behavior |
|---------|----------|
| `sovereign_engine.get_oidc_secret` | Full hexdigest Phase-3 |
| `batch_oidc_tokenizer` | Full HMAC sig |
| `hyperian_json_server` `/oidc` | `secret_len` + optional 8-char prefix |
| `prometheus/metrics_server` | Gauges only; no secret series |
| Commit / ledger hashes | Full 40-char Git SHA or full content digest |

Seal: ∀∞φ² · IMMUTABLE_NO_SECRETS_8634 · SEALED
