# Working order — Sovereign CI/CD badge

Date: 2026-10-02
Repo: AxiomicCoreness/hello_world.py
Branch: main

## What the badge is

The badge at

https://github.com/AxiomicCoreness/hello_world.py/actions/workflows/sovereign-ci-cd.yml/badge.svg

is the latest completed conclusion of `.github/workflows/sovereign-ci-cd.yml` on the default branch. It is not a file-exists check.

## Measured state

| Run | Event | Status |
|-----|--------|--------|
| 2448 (37048198492) | workflow_dispatch | queued since 2026-10-02T18:33Z |
| 2447 (37046964154) | workflow_dispatch | startup_failure |
| 2304 (36368582603) | push | success (2026-09-28) |
| 2049 (35470566667) | workflow_dispatch | success (2026-09-19) |

Contents write is active. Queueing a run returns 204. That does not make the badge green.

## Why it is not green

`startup_failure` means GitHub never built a job graph. A later rewrite of the YAML does not fix that. A run stuck in `queued` means no runner accepted the job.

Required outside this file:

1. Settings → Actions → General → Actions permissions: allow GitHub actions used by the workflow (`actions/checkout`, `actions/setup-python`, `actions/upload-artifact`), or allow all actions.
2. A runner that can take `ubuntu-latest` must be Idle. Billing/minutes must not be exhausted.
3. Do not rewrite committed `ledger/8977.yaml`. Job-local writers stay job-local. Next commit index is 8978+.

## Order that is already on main

1. `workloads.mk` — soft-skip targets, exit 0.
2. `.github/workflows/sovereign-workload-matrix.yml` — choice input, soft-skip, requires `GARDEN_SECRET`.
3. `.github/workflows/sovereign-ci-cd.yml` — 8977 frozen; seal job does not push.
4. `.github/workflows/sovereign-ci-green.yml` — no `uses:` actions; dispatch-only smoke. This is the file that can go green if the block is an actions allowlist.

## Dispatch

```bash
gh workflow run sovereign-ci-green.yml --ref main
gh workflow run sovereign-ci-cd.yml --ref main -f oidc_provider=offline
```

Badge turns green only after a run of `sovereign-ci-cd.yml` completes with conclusion `success`.
