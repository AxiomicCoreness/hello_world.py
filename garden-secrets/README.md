# Garden Secrets Management

- **Never** commit raw secrets.
- Use [SealedSecrets](https://github.com/bitnami-labs/sealed-secrets) to encrypt Kubernetes secrets.
- `templates/` holds placeholders for local development.
- `sealed-secrets/` holds encrypted manifests that can be committed.
- Secret *values* are not written to the ledger.

## Presence names only

| Name | Purpose |
|------|---------|
| `GARDEN_SECRET` | `/pulse` header `X-Garden-Secret` |
| `MCP_CLIENT_ID` | Connector client credentials |
| `MCP_CLIENT_SECRET` | Connector client credentials |
| `MCP_CONNECTOR_URL` | Non-secret; lives in ConfigMap |
| `MCP_URL` | Public Port 380 URL |

## Applying secrets (cluster)

```bash
kubeseal --fetch-cert > pub-cert.pem
kubeseal --cert pub-cert.pem < templates/garden-secrets.template.yaml > sealed-secrets/garden-secrets.yaml
kubectl apply -f sealed-secrets/garden-secrets.yaml
```

## Local / GitHub Actions

```bash
gh secret set GARDEN_SECRET --repo AxiomicCoreness/hello_world.py
gh secret set MCP_URL --repo AxiomicCoreness/hello_world.py --body "https://api.sovereign.garden/380"
PYTHONPATH=. python3 scripts/startup_secrets_rotator.py --check
```

Seal: ∀∞φ² · GARDEN_SECRETS_LAYER · WOOD_DRAGON_0.91 · SEALED
