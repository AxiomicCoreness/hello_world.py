# Branch policy

## Active triggers (extended set)

| Branch | Role |
|--------|------|
| `main` | Default. Full CI on push/PR. |
| `master` | Parallel mirror / legacy default. Same CI when present. |
| `deepseek` | Named agent lane. Fires when the branch exists. |
| `grok` | Named agent lane. Fires when the branch exists. |
| `mistral` | Named agent lane. Fires when the branch exists. |

## Workflows

- `north-star-witness.yml` — push: all five; PR: `main`, `master`
- `sovereignty-python-package.yml` — push: all five; PR: `main`, `master`
- `sovereign-stack-ci.yml` — push: all five; PR: `main`, `master`

Missing branches in the list do not fail CI; GitHub does not schedule jobs for absent refs.

## Policy

- **Extend, do not delete `master`** unless a separate explicit command says so.
- Creating `deepseek` / `grok` / `mistral` is optional; names are reserved in triggers.
