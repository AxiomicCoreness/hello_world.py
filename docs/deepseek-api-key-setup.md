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
