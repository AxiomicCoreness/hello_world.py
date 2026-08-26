# GitHub Actions secrets context

Seal: `∀∞φ² · CI_SECRETS_8832 · WOOD_DRAGON_0.91 · SEALED`

This repository does not read an environment variable named `GARDEN_SECRETS`.
This repository does not read `SUPERSECRET`.
This repository does not read a repository secret named `github_token`.
This repository does not read `NPM_TOKEN`.

## Name map from the requested JSON

| Requested blank | Name the code actually reads | Actions context |
|-----------------|------------------------------|-----------------|
| `github_token` | `GITHUB_TOKEN` (automatic job token) | `${{ secrets.GITHUB_TOKEN }}` assigned to `GH_TOKEN` for `gh` |
| `NPM_TOKEN` | none | unused |
| `SUPERSECRET` | `GARDEN_SECRET` | `${{ secrets.GARDEN_SECRET }}` sent as header `X-Garden-Secret` |

## Repository secrets to create

| Secret | Required | Consumer |
|--------|----------|----------|
| `GARDEN_SECRET` | yes for authenticated `/pulse` | `port380_mcp.py`, `sovereign-pulse.yml` |
| `MCP_URL` | yes for a remote pulse | `sovereign-pulse.yml`; local default `http://127.0.0.1:380` |
| `DEEPSEEK_API_KEY` | no | DeepSeek online probe only |
| `DEEPSEEK_BASE_URL` | no | default `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | no | default `deepseek-chat` |

Create them in the repository Actions secrets page or with the GitHub CLI. The CLI prompts for the value on stdin when `--body` is omitted.

```bash
gh secret set GARDEN_SECRET --repo AxiomicCoreness/hello_world.py
gh secret set MCP_URL --repo AxiomicCoreness/hello_world.py --body "http://127.0.0.1:380"
```

## Example: secrets context plus strategy context

```yaml
name: Open new issue
on: workflow_dispatch
jobs:
  open-issue:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - run: |
          gh issue --repo ${{ github.repository }} \
            create --title "Issue title" --body "Issue body"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  pulse-matrix:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        target: [health, pulse]
    env:
      MCP_URL: ${{ secrets.MCP_URL }}
      GARDEN_SECRET: ${{ secrets.GARDEN_SECRET }}
    steps:
      - run: |
          echo "strategy.job-index=${{ strategy.job-index }}"
          echo "strategy.job-total=${{ strategy.job-total }}"
          echo "matrix.target=${{ matrix.target }}"
```

`strategy.job-index` is the zero-based index of the current matrix job.
`strategy.job-total` is the number of matrix combinations.
`matrix.target` is `health` or `pulse` from the list above.

Companion machine-readable file: `docs/secrets-context.json`.
Contract file: `contracts/ci-secrets.yaml`.
Workflow example: `.github/workflows/secrets-context-example.yml`.
