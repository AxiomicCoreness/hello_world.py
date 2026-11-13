# CI/CD pivot (CAD / CAM / mill)

CAD is CAD. CNC is a mill. CI/CD is the software analogue, not a mill.

| Layer | Shop floor | This repo's `main` HEAD |
|---|---|---|
| CAD | model + constraints | lattice table, Berry config |
| CAM | toolpath check | GitHub Actions test job |
| CNC mill | cutting stock | **not allocated** |
| CD | combinator | `.github/workflows/cd-combinator.yml` |
| CI | Argo + immutable image | `.github/workflows/argo-ci.yml` + `Dockerfile.garden-ci` |
| CD (Argo CD) | backend CI/CD sink | `.github/workflows/argo-cd-deploy.yml` + `argocd/application-argo-cicd-backend.yaml` |

CI is the immutable image stage. `__pycache__` is excluded (`.dockerignore`, `PYTHONDONTWRITEBYTECODE=1`).

CD is the combinator. Live Argo sync only if secrets exist; otherwise skip.

`argo-ci.yml` and `cd-combinator.yml` bodies are not rewritten.

Backend Argo CI/CD sink: `pythonIDE/argo_sink.py` binds `127.0.0.1:8024`, polls the
`argo-ci.yml`, `cd-combinator-argo-rollout.yml`, `sovereign-cicd.yml` and
`ci-cd-stack.yml` runs on `main`, and pushes one `[Argo]` line per workflow to
`ws://127.0.0.1:6680/cli` as a WebSocket client (no browser needed). `/py call argo`
returns the same lines through the toolkit (an extension; the core count stays 54).
The Argo CD Application syncs `argocd/argo-cicd-backend/` with automated prune and
selfHeal; every image there is pinned by `sha256` digest. `argo-cd-deploy.yml`
validates on PR and syncs on `main` only if `ARGOCD_SERVER` and `ARGOCD_AUTH_TOKEN`
exist; otherwise it skips.
