# Startup Secrets Rotator

Seal: `∀∞φ² · STARTUP_SECRETS_ROTATOR · WOOD_DRAGON_0.91 · SEALED`

## Purpose

At process or deploy **startup**, verify which CI/runtime secrets are present and optionally mint a new `GARDEN_SECRET` **fingerprint** without committing secret values to git.

## Commands

```bash
PYTHONPATH=. python3 scripts/startup_secrets_rotator.py --check
PYTHONPATH=. python3 scripts/startup_secrets_rotator.py --rotate-garden --show-once
PYTHONPATH=. python3 scripts/startup_secrets_rotator.py --check --json
```

## Related

- `contracts/ci-secrets.yaml`
- `docs/github-actions-secrets.md`
- `.github/workflows/deepseek-ci-secrets.yml`
- Grok skill: `startup-secrets-rotator` (local skills directory)

## AWS HMAC rotator (separate)

`.github/workflows/api-key-rotator.yml` + `ci_cd_key_rotator.py` rotate Hamiltonian HMAC material in AWS Secrets Manager via OIDC. That path is independent of DeepSeek API keys.
