# GitHub Actions CI Secrets

Seal: `∀∞φ² · CI_SECRETS_8832 · WOOD_DRAGON_0.91 · SEALED`

Secrets **cannot** be written via the public git API. Set them in the UI or with `gh`.

## Required names

| Secret | Used by | CI without it |
|--------|---------|----------------|
| `DEEPSEEK_API_KEY` | deepseek-ci-secrets, optional pytest | Offline probe still passes |
| `MCP_URL` | sovereign-pulse.yml | Pulse job fails until set |
| `GARDEN_SECRET` | sovereign-pulse.yml | Pulse runs without auth header (warn) |

Optional: `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL` (defaults in code).

## Set via UI

1. https://github.com/AxiomicCoreness/hello_world.py/settings/secrets/actions
2. **New repository secret** for each name above
3. Values only — never commit them

## Set via CLI

```bash
gh secret set DEEPSEEK_API_KEY --repo AxiomicCoreness/hello_world.py
gh secret set MCP_URL --repo AxiomicCoreness/hello_world.py --body "https://YOUR-SERVICE.onrender.com"
gh secret set GARDEN_SECRET --repo AxiomicCoreness/hello_world.py
```

(`gh secret set NAME` with no `--body` prompts securely.)

## Workflow behaviour

- **deepseek-ci-secrets.yml** — reports which secrets are *present* (boolean only), runs offline probe always, online `prefer=deepseek` only if key is set.
- **sovereign-pulse.yml** — requires `MCP_URL`; uses `GARDEN_SECRET` when set.
- **pytest.yml** — injects `DEEPSEEK_API_KEY` into the job env when configured; tests must not require live API.

## Verify

```bash
gh workflow run deepseek-ci-secrets.yml --repo AxiomicCoreness/hello_world.py
gh run list --workflow=deepseek-ci-secrets.yml --repo AxiomicCoreness/hello_world.py -L 3
```

Contract file: `contracts/ci-secrets.yaml`.
