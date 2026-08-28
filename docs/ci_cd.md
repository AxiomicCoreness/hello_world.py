# CI/CD pivot (CAD / CAM / mill)

CAD is CAD. CNC is a mill. CI/CD is the software analogue, not a mill.

| Layer | Shop floor | This repo |
|---|---|---|
| CAD | model + constraints | POLICY.md, lattice table, Berry config |
| CAM | toolpath check | GitHub Actions test job |
| CNC mill | cutting stock | **not allocated** |
| CD | release to machine | `record_only` ledger append |

## Constraint

- CI may run tests on push/PR/`workflow_dispatch`.
- CD does not bind `0.0.0.0`, does not install crontab, does not fire.
- Cron nodes remain `wait`, `nudge_cronjob`, `record_only`.
- Existing workflows on `main` are not rewritten by this pivot.
- New workflow: `.github/workflows/garden-surgery.yml`.
