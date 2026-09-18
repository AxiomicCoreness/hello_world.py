# Catalogue — 2026-09-18 (main only)

Single branch: `main`. No `deepseek` / `deepseek-cd` tip unless restored later.

## Engines (triune)

| Path | Role | Operator (honest) |
|------|------|-------------------|
| `terminal_axiom/` | T₀ Location | `⊕` = ordinary `+` |
| `producer_axiom/` | P₀ Product | `⊗` = ordinary `·` |
| `consumer_axiom/` | C₀ Consumption | `⊘` = `max(D−R, 0)` |
| `tests/test_*_axiom.py` | unit tests | — |
| `tests/test_axiom_differential.py` | cross-engine | — |
| `.github/workflows/producer-axiom-verify.yml` | CI strict + diagnostic on failure | — |

## North Star / CD

| Path | Role |
|------|------|
| `.github/workflows/deepseek-cd.yml` | North Star 71.975 Hz, scoped vocab, H_9240 Regime B |
| `docs/COSMIC_ALIGNMENT_POLICY.md` | required by CD guard (may still be missing) |
| `ledger/9240.yaml` | hard Regime B (may still be missing) |

## pythonIDE (selected)

| Path | Role |
|------|------|
| `pythonIDE/dX_dt.py` | system equation; Euler + PID honesty fixes |
| `pythonIDE/simd_forward_merge.py` | **SIMD-style** multi-lane forward merge (numpy if present) |
| `pythonIDE/toi_step.py` / `optimize_toi.py` | two-ball TOI |
| `pythonIDE/hopper_optimize.py` | hopper |
| `pythonIDE/update_baseline.py` | baseline probe |
| `pythonIDE/toolkit.py` | toolkit surface |

## Docs

| Path | Role |
|------|------|
| `.github/TOPICS.md` | terminal axiom + mathematical form admission + triune seal label |
| `docs/CATALOGUE_2026-09-18.md` | this file |

## Merge policy (sync)

- Catalogue is **inventory**, not a ledger rewrite.
- SIMD forwarder merges **parallel state lanes** in one step; it does not rewrite git history.
- Dual ASGI remains `127.0.0.1:8024` only; MCP unfilled.
