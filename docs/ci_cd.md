# CI/CD pivot (CAD / CAM / mill)

CAD is CAD. CNC is a mill. CI/CD is the software analogue, not a mill.

| Layer | Shop floor | This repo |
|---|---|---|
| CAD | model + constraints | POLICY.md, lattice table, Berry config |
| CAM | toolpath check | GitHub Actions test job |
| CNC mill | cutting stock | **not allocated** |
| CD | combinator | `.github/workflows/cd-combinator.yml` |
| CI | Argo + immutable image | `.github/workflows/argo-ci.yml` + `Dockerfile.garden-ci` |

CI is the immutable image stage. `__pycache__` is excluded (`.dockerignore`, `PYTHONDONTWRITEBYTECODE=1`).
CD is the combinator. Live Argo sync only if secrets exist; otherwise skip.
`argo-ci.yml` and `cd-combinator.yml` bodies are not rewritten.
