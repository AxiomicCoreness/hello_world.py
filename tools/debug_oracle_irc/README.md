# Debug Oracle IRC (team v1)

TeaVM-surface debug environment: left **directory panel**, right **chat
emergent from literal 64-hex locks**, and a command prompt. Team channel
endpoints are **UI labels only**:

- `irc.abjects.net:6666`
- `irc.abjects.net:6667`
- `irc.abjects.net:6668`
- `irc.abjects.net:6669`

**No live IRC sockets** in CI or in this tool.

## Paths

| Path | Role |
|------|------|
| `games/teavm-rhythm/src/main/webapp/debug-oracle/index.html` | Browser panel (served with TeaVM `target/webapp`) |
| `games/teavm-rhythm/src/main/webapp/debug-oracle/hex_locks.json` | Full 64-hex digests (9300 seal, Layer 314 Anchor/Leaf) |
| `tools/debug_oracle_irc/oracle_shell.py` | Local directory / command-prompt TUI |

## Roots (left panel)

`ledger.v2`, `deepinfer`, `games/teavm-rhythm`, `skills`, `quantum`, `argocd`

## Run

```bash
# browser (after mvn package, or open the webapp path directly)
open games/teavm-rhythm/src/main/webapp/debug-oracle/index.html

# shell (CI-safe one-shots)
python3 tools/debug_oracle_irc/oracle_shell.py --once hex
python3 tools/debug_oracle_irc/oracle_shell.py --once channels
python3 tools/debug_oracle_irc/oracle_shell.py   # interactive TUI
```

## Policy

- Full digests only (no `[:16]` / `[:32]` truncation).
- Append-only ledger elsewhere; this panel does not seal.
- Companion to `.github/workflows/debug-environment.yml` (read-only CI dump).
