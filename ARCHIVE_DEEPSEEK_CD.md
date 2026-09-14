# ARCHIVE — deepseek-cd (frozen witness)

**Status:** FROZEN — do not merge into or from this branch for routine work.

| Marker | Value |
|--------|--------|
| Named freeze SHA | `5b47a91d7619107836623fd65f9445c4e901dde7` |
| Tip at archive | `899776f2e116b12b19c63512c742f65385acd728` |
| Tag (local/ops) | `deepseek-cd-witness-5b47a91d` |
| Successor | **`deepseek-cd-next`** (cut from `main`) |

## Durable artifacts only

- `.github/workflows/deepseek-cd.yml` (scoped vocab + H_9240)
- `.github/workflows/toolkit-54-exorcise.yml`
- `scripts/exorcise_toolkit_54.py`
- `pythonIDE/toolkit.py` (54 honest)
- Regime B anchors H_9240 / H_9241

## Tag command (ops — MCP has no create-tag)

```bash
git fetch origin
git tag deepseek-cd-witness-5b47a91d 5b47a91d7619107836623fd65f9445c4e901dde7
git tag deepseek-cd-tip-899776f2 899776f2e116b12b19c63512c742f65385acd728
git push origin deepseek-cd-witness-5b47a91d deepseek-cd-tip-899776f2
```

PR #30 closed as superseded. Future CD → `deepseek-cd-next`.
