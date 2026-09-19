# Branch policy

## Active

| Branch | Role | Default |
|--------|------|---------|
| `main` | default; all merges land here | yes |
| `master` | mirror; kept in sync with main | no |

## Reserved

| Branch | Role | Status |
|--------|------|--------|
| `deepseek` | reserved; fires only if branch exists | inactive until created |
| `grok` | reserved; fires only if branch exists | inactive until created |
| `mistral` | reserved; fires only if branch exists | inactive until created |

## Trigger surface

- `north-star-witness.yml`, `sovereignty-python-package.yml`, `sovereign-stack-ci.yml` — push: `[main, master, deepseek, grok, mistral]`; PR: `[main, master]`
- `merge-engine.yml` — push: `[main, master]`

## CD combinator chain

`cd-combinator-argo-rollout.yml` fires on `workflow_run` for workflow **name** `Master Equation Integration Test` (exact string match, not filename).

## Cost note

Keeping `main` and `master` in sync doubles job volume. Merge engine verifies digests only; does not rewrite sealed ledgers.
