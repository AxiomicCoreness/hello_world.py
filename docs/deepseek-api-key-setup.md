# DeepSeek API Key Setup

Garden surface: **DeepSeek MCP only** (`offline` | `deepseek` | `dsh`).  
Seal: `∀∞φ² · DEEPSEEK_KEY_SETUP · WOOD_DRAGON_0.91 · SEALED`

## 1. Obtain a key

1. Open [https://platform.deepseek.com](https://platform.deepseek.com)
2. Sign in → **API Keys** → create a key
3. Copy once; store only in secrets managers / local `.env` (never in git)

## 2. Environment variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DEEPSEEK_API_KEY` | for online | _(empty → offline)_ | Bearer token |
| `DEEPSEEK_BASE_URL` | no | `https://api.deepseek.com` | API host |
| `DEEPSEEK_MODEL` | no | `deepseek-chat` | Chat model |
| `DSH_MODEL` | no | same as above | Harness alias |
| `GARDEN_SECRET` | for `/pulse` auth | _(open if empty)_ | `X-Garden-Secret` |
| `PORT` | Render/local | `8000` | Bind port |

Without `DEEPSEEK_API_KEY`, the lattice stays in **offline** echo mode (valid for CI).

## 3. Local development

```bash
cp .env.example .env
# edit .env — set DEEPSEEK_API_KEY=sk-...

# load into shell (example)
export $(grep -v '^#' .env | xargs)

python -c "from quantum.deepseek_mesh.dsh_adapter import probe, complete; print(probe()); print(complete('ping', prefer='deepseek').mode)"
```

Expected online probe: `api_key_set: true`, mode `deepseek` or `dsh`.

MCP gate:

```bash
PYTHONPATH=. uvicorn quantum.deepseek_mesh.endpoint:app --host 0.0.0.0 --port ${PORT:-8000}
# or: python -m quantum.deepseek_mesh.endpoint  (if __main__)
```

## 4. Render

Dashboard → your web service → **Environment**:

| Key | Value |
|-----|--------|
| `DEEPSEEK_API_KEY` | your key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | `deepseek-chat` |
| `GARDEN_SECRET` | same string as GitHub secret |
| `PORT` | leave unset (Render injects) |

Redeploy after saving.

## 5. GitHub Actions (optional CI inference)

Repository → **Settings → Secrets and variables → Actions**:

- `DEEPSEEK_API_KEY` — only if a workflow must call the live API
- Keep unit tests offline-friendly (no key required)

Pulse secrets (separate):

- `MCP_URL` — `https://<your-service>.onrender.com`
- `GARDEN_SECRET` — matches Render

## 6. Mode behaviour (`dsh_adapter.complete`)

| `prefer` | Behaviour |
|----------|-----------|
| `auto` | `dsh` if SDK+key → else `deepseek` if key → else `offline` |
| `deepseek` | HTTPS to `DEEPSEEK_BASE_URL` |
| `dsh` | official `deepseek_harness` SDK |
| `offline` | local echo |

Legacy names (`openai`, `chatgpt`, …) are coerced to `deepseek`.

## 7. Security

- Never commit `.env` or real keys
- Rotate keys on platform.deepseek.com if leaked
- Prefer secret stores (Render env, GitHub Actions secrets, sealed secrets in cluster)

## 8. Quick verify

```bash
curl -s -X POST "$MCP_URL/pulse" \
  -H "Content-Type: application/json" \
  -H "X-Garden-Secret: $GARDEN_SECRET" \
  -d '{"source":"key-setup-check","entry":8831}'
```
