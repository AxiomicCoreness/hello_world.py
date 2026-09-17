# Sheaf reorganization — plan only (9204)

Not executed. Sealed ledger YAML stays in `ledger/`.
Do not reuse indices 9202 or 9203.

## Must not move or rewrite

- `ledger/*.yaml` including 91xx, 9200, 9201, 9202, 9203
- Fusion 515 / Hyperion 516
- Dual ASGI bind contract `127.0.0.1:8024`
- MCP `FILLED=false`

## Proposed non-ledger moves (not applied)

| Source | Target | Note |
|--------|--------|------|
| README.md | sheaf/meta/README.md | not moved |
| POLICY.md | sheaf/meta/POLICY.md | append-only at root; do not relocate |
| docs/SEARCH.md | sheaf/meta/SEARCH.md | path is docs/SEARCH.md |
| LEDGER_GAPS_README.md | sheaf/meta/LEDGER_GAPS_README.md | scope 0000-0514 only |
| docs/fastMCP_spec.md | sheaf/meta/fastMCP_spec.md | |
| docs/fastmcp_layer.md | sheaf/meta/fastmcp_layer.md | |
| docs/phase_lock_definition.md | sheaf/docs/phase_lock_definition.md | not docs/phase_lock.md |
| pythonIDE/* | sheaf/code/pythonIDE/ | |
| scripts/*.sh | sheaf/code/scripts/ | |
| garden_surgery/ | sheaf/code/garden_surgery/ | |
| k8s/*.yaml | sheaf/k8s/ | would break 9164/9179/9199 paths |
| .github/workflows/*.yml | sheaf/ci/ | GitHub requires .github/workflows |
| tests/*.py | sheaf/tests/ | |
| requirements-control.txt | sheaf/configs/ | |

GitHub Actions cannot run from `sheaf/ci/`. Leave workflows under `.github/workflows/`.
