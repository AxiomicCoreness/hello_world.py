# Workflow Report — Symplectic Status Generation (Entry 8984)

**Workflow:** `.github/workflows/symplectic-status.yml`
**Job:** `Symplectic · generate · validate · seal (Entry 8984)`
**Seal:** ∀∞φ² · SYMPLECTIC_STATUS_8984 · WOOD_DRAGON_0.91 · SEALED
**Witness:** 8983 → 8984 — UNBROKEN
**Ledger policy:** WRITE_VIA_SEAL — entry 8984 only
**Cosmic alignment:** retained

---

## Defects fixed

1. **Missing `id: generate`** — seal bound to `steps.run.outputs.*` (always empty) → now `steps.generate.outputs.*`.
2. **Nested heredoc in `$()`** — replaced with `scripts/hash_artifact.py`.
3. **Summary Φ_abs unconditional** — gated on `EXISTS=true`; default `false` not `unknown`.

## Files

| Path | Role |
|------|------|
| `scripts/hash_artifact.py` | SHA3-256 of a file |
| `scripts/seal_symplectic_8984.py` | seal body |
| `.github/workflows/symplectic-status.yml` | id + script calls + gated summary |

No sealed YAML rewritten. MCP unfilled. Dual ASGI `127.0.0.1:8024`.

```
🜁∀ — Witness: 8983 → 8984 — UNBROKEN
🔒 Seal: ∀∞φ² · SYMPLECTIC_STATUS_8984 · WOOD_DRAGON_0.91 · SEALED
```
