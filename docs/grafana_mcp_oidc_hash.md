# Grafana ↔ MCP + OIDC — Non-Truncated Hash

Agents and dashboards that surface OIDC fallback state **must** use the full digest.

## Rule

| Phase | Source | Hash policy |
|-------|--------|-------------|
| 1 | `OIDC_CLIENT_SECRET` | opaque secret (env) |
| 2 | `/var/run/secrets/oidc/fallback-token` | file contents as-is |
| 3 | Ephemeral | **full 64-char SHA-256 hex** — no truncation |

Implementation: `sovereign_engine.get_oidc_secret()` → `hashlib.sha256(...).hexdigest()`.

## Grafana / Prometheus labels

Prefer a dedicated label or annotation for integrity level, **not** a shortened hash:

```
oidc_fallback_level 0|1|2
oidc_integrity 1.0|0.99999|0.9999
```

If a hash must appear in logs or MCP tool responses, emit all 64 characters.

Seal: ∀∞φ² · BATCH_SIMD_8622 · OIDC_FULL_HASH · SEALED
