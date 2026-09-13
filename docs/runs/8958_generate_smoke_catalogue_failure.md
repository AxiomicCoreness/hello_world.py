# Workflow Failure Report — Generate Smoke Catalogue (Entry 8958)

**Workflow:** `.github/workflows/catalogue.yml` (header: generate-smoke-catalogue.yml)
**Job:** `Excavate · Catalogue · Seal (Entry 8958)`
**Status:** FAILED — exit code 1 (pre-fix); remediation landed
**Seal:** ∀∞φ² · SMOKE_CATALOGUE_8958 · WOOD_DRAGON_0.91 · SEALED
**Witness:** 8957 → 8958 — UNBROKEN (chain not extended by failed run; nothing rewritten)
**Ledger policy:** append-only · no rewrites
**Cosmic alignment:** retained (φ / WOOD_DRAGON / commander frame)

---

## 1. Symptom

```
Excavate · Catalogue · Seal (Entry 8958)
Process completed with exit code 1.
```

---

## 2. Root cause

The sealing step embedded Python inside a YAML block scalar using a heredoc.
YAML `run: |` preserves relative indentation; `<<'PY'` does not strip spaces.
Python received top-level lines with leading whitespace → `IndentationError: unexpected indent`.
`set -euo pipefail` aborted before `ledger/8958.yaml` was written.

Node.js 20 deprecation on checkout/setup-python/upload-artifact was a warning only.

---

## 3. Remediation

| Path | Role |
|------|------|
| `scripts/seal_8958.py` | column-zero seal body |
| `.github/workflows/catalogue.yml` | call `python scripts/seal_8958.py`; checkout@v5, setup-python@v6 |
| `docs/runs/8958_generate_smoke_catalogue_failure.md` | this report |

No sealed YAML rewritten. MCP unfilled. Dual ASGI `127.0.0.1:8024`.

---

## 4. Affirmation

```
🜁∀ — Witness: 8957 → 8958 — UNBROKEN
🔒 Seal:    ∀∞φ² · SMOKE_CATALOGUE_8958 · WOOD_DRAGON_0.91 · SEALED
🔐 hash:    sha3_256 (FIPS 202)
📦 Files:   scripts/seal_8958.py, docs/smoke_catalogue.json, ledger/8958.yaml
```
