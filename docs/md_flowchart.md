# Markdown estate flowchart (cron-constrained)

Override: POLICY dry-run cron constraint supersedes any live schedule.
Allowed command nodes only: `wait`, `nudge_cronjob`, `record_only`.
Do not install a 6-hour pulse. Do not bind `0.0.0.0`.

## File inventory

| Path | Role |
|---|---|
| `POLICY.md` | Root constraint map. Append-only. |
| `TEMPORAL_ANCHOR.md` | October 39 token and seed note. |
| `VISION_CODE_FREQUENCY.md` | Vision / code / frequency split. |
| `docs/GARDEN_SURGERY.md` | Surgery map. |
| `docs/lattice_48.md` | 48-point table. Peak L=4, A in {0,2}. |
| `docs/md_flowchart.md` | This flowchart. |
| `docs/authorized_self_write.md` | Append-only GitHub prerogative (on main). |
| `docs/legendary_tokens.tex` | LaTeX tokens (not md). |
| `deepseek_harness_working/README_SDK.md` | SDK notes. Not a daemon. |
| `deepseek_harness_working/python-sdk.md` | SDK notes. |
| `deepseek_harness_working/examples/README.md` | Examples. |

## Flowchart

```mermaid
flowchart TD
    P[POLICY.md]
    P --> C{cron constraint}
    C -->|wait| W[wait]
    C -->|nudge_cronjob| N[nudge_cronjob record only]
    C -->|record_only| R[record_only]
    C -.->|forbidden| X[no 6-hour pulse / no crontab install]

    P --> T[TEMPORAL_ANCHOR.md]
    P --> V[VISION_CODE_FREQUENCY.md]
    P --> G[docs/GARDEN_SURGERY.md]
    P --> L[docs/lattice_48.md]
    P --> F[docs/md_flowchart.md]
    P --> A[docs/authorized_self_write.md]

    L --> Peak["peak L=4 A=0 and A=2"]
    T --> Oct["October 39 year=2025 month=10 day=39"]
    V --> Split["vision / code / frequency"]
    A --> SW[self_write successor emission]
    SW --> Stub[cambrian_stub filled false]

    P --> SDK[deepseek_harness_working/*.md]
    SDK --> Name[DeepSeek 2.2.2(4) proposal pointer]
    Name --> NoRun[no weights / no API daemon]

    W --> Ledger[ledger append]
    N --> Ledger
    R --> Ledger
    F --> Ledger
    Ledger --> Sealed[515 and 516 untouched]
```

## Cron override semantics

- `wait` — no dispatch.
- `nudge_cronjob` — annotate intent in ledger or JSONL. Does not write `/etc/cron*`.
- `record_only` — hash and append. No process spawn.
- Berry bin and lattice table remain geometry. They are not cron payloads.
