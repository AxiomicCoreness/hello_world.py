# Private loopback CORS Anywhere

Local/dev **only** CORS proxy for AxiomicCoreness. **Not** an open proxy.

| Constraint | Value |
|---|---|
| Bind | **`127.0.0.1` only** (Cosmic Alignment — never `0.0.0.0`) |
| Origins | Whitelist only (`CORSANYWHERE_WHITELIST`) |
| Public demo | **Do not use** `https://cors-anywhere.herokuapp.com/` |
| port380 | **Do not weaken** harden-CORS on `/health`/`/healthz` — separate concern |

Based on [Rob--W/cors-anywhere](https://github.com/Rob--W/cors-anywhere) (MIT), wrapped so empty whitelist and non-loopback binds refuse to start.

## Quick start

```bash
cd tools/cors-anywhere
npm install
npm start
# → http://127.0.0.1:8080/
```

Syntax check (no listen):

```bash
npm run check
```

## How to call it

Prefix the target URL with the proxy base (same API as upstream):

```text
http://127.0.0.1:8080/https://example.com/
http://127.0.0.1:8080/example.com
http://127.0.0.1:8080/example.com:443   # → https://example.com/
http://127.0.0.1:8080/                   # help.txt
```

Browsers must send **`Origin`** or **`X-Requested-With`**. Cookies are stripped.

## Whitelist

Default `CORSANYWHERE_WHITELIST` (override via env) mirrors `PORT380_ALLOWED_ORIGINS` plus axiomiccoreness / localhost variants:

- `https://api.sovereign.garden`
- `https://sovereign.garden`
- `http://localhost:380`, `http://localhost:8080`, `http://localhost`
- `http://127.0.0.1:380`, `http://127.0.0.1:8080`, `http://127.0.0.1`
- `https://axiomiccoreness.com`, `https://www.axiomiccoreness.com`
- `https://bridge.axiomiccoreness.com`
- `https://axiomiccoreness.github.io`

Example override:

```bash
export CORSANYWHERE_WHITELIST='https://sovereign.garden,http://localhost:380'
npm start
```

An **empty** whitelist exits with `FATAL` (upstream treats empty as allow-all).

## Bind

Always listens on **`127.0.0.1`**. If `HOST` / `BIND_HOST` is set to anything other than `127.0.0.1` or `localhost` (including `0.0.0.0`), the process exits with `FATAL`.

```bash
export PORT=8080          # default 8080
# HOST=0.0.0.0            # refused
npm start
```

## Rate limit

Default: `CORSANYWHERE_RATELIMIT='50 1'` (50 requests per origin per minute). See upstream docs for the `max period [unlimitedHost…]` syntax.

## Env summary

| Variable | Default | Notes |
|---|---|---|
| `PORT` | `8080` | Listen port |
| `HOST` / `BIND_HOST` | `127.0.0.1` | Must be loopback alias; listen is always `127.0.0.1` |
| `CORSANYWHERE_WHITELIST` | (see above) | Comma-separated Origins; required non-empty |
| `CORSANYWHERE_BLACKLIST` | _(empty)_ | Optional Origin block list |
| `CORSANYWHERE_RATELIMIT` | `50 1` | Upstream rate-limit string |

## Relation to port380

port380 `CORSMiddleware` + `/healthz` CORP override (`feat/harden-cors-healthz`) stays as-is. This tool is an optional local browser proxy for third-party fetches during TeaVM/Pages/dev work — it does not replace or relax gate CORS.
