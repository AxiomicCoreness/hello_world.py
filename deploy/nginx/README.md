# nginx config for bridge.axiomiccoreness.com

`bridge.axiomiccoreness.com.conf` terminates TLS for the public bridge
host and passes the `/cli` WebSocket through to the local bridge.

Nothing in this repo deploys it automatically. The host admin does these steps:

1. Issue the certificate, for example `certbot certonly -d bridge.axiomiccoreness.com`.
   Adjust the `ssl_certificate` paths in the conf if certbot puts them somewhere else.
2. Add the map block and the rate-limit zone inside the `http {}` block of `nginx.conf`:

   ```nginx
   map $http_upgrade $connection_upgrade {
       default upgrade;
       ''      close;
   }
   limit_req_zone $binary_remote_addr zone=qwen_abliterated:10m rate=6r/m;
   ```

3. Install the conf, for example into `/etc/nginx/conf.d/`, then run
   `nginx -t` and reload with `nginx -s reload` or `systemctl reload nginx`.

## What stays where

- The bridge stays bound to `127.0.0.1:6680` (Cosmic Alignment, never `0.0.0.0`).
  nginx on 443 is the only public listener.
- The Pages client already dials `wss://bridge.axiomiccoreness.com/cli`
  (see `irc/CliLines.java`). Local play still uses `ws://127.0.0.1:6680/cli`.
- `/llm` is a chat command sent over the `/cli` socket, so it has no `location` of its own.
- cors-anywhere (`127.0.0.1:8080`) stays internal on purpose. Publishing it
  would make the host an open relay.

## Public abliterated Qwen route

URL: `https://bridge.axiomiccoreness.com/qwen-abliterated/v1/chat/completions`

nginx strips the `/qwen-abliterated` prefix and passes requests to the
llama-server on `127.0.0.1:8083`, so `/qwen-abliterated/health` and
`/qwen-abliterated/v1/...` reach `/health` and `/v1/...`. llama-server stays bound
to `127.0.0.1` (Cosmic Alignment). nginx is still the only public listener.

**Risk:** this route exposes an uncensored (abliterated) model to the public
internet with **no authentication**. Anyone who finds the URL can use it.

**Recommended:** start llama-server with `--api-key <key>` so it checks its own
bearer token (`Authorization: Bearer <key>`). Keep the key on the host only; it
must never be committed to this repo. Adding `auth_basic` in the location, with an
htpasswd file kept off the repo, is another option.

Limits in the location block:

- Per-IP rate limit from the `qwen_abliterated` zone above, 6 requests a minute
  with `burst=5`. Over the limit gets `429`.
- Only `GET` and `POST` (GET also admits HEAD); other methods get `403`.
- `client_max_body_size 1m`, `proxy_buffering off` so streamed responses pass
  straight through, and `proxy_read_timeout 300s` for slow CPU generation.

Model provenance:
`mradermacher/Qwen2.5-1.5B-Instruct-abliterated-GGUF@36d335ab94cb641e885c327f110600342663eee2`,
file Q4_K_M, sha256
`59aa9f44bde5349dbe292d7024d197db605f422b8baf65f3246a59abbde4e8e9`.

The bridge's own `/llm` fallback tier for this model is separate. It lives on the
unmerged branch `feat/llm-qwen-abliterated`.

## Note on `http2`

The conf uses `listen 443 ssl;` plus `http2 on;` rather than
`listen 443 ssl http2;`. nginx 1.25.1 and later warn that the `http2`
listen parameter is deprecated. On nginx older than 1.25.1, `http2 on;` is not
recognised; use `listen 443 ssl http2;` there instead.

## Checked on

nginx 1.26.3: `nginx -t` passed with the map block and self-signed stand-in certs.
A WebSocket upgrade through `/cli` to the live bridge on 127.0.0.1:6680 returned
`101 Switching Protocols`. Through `/qwen-abliterated/`, the live llama-server on
127.0.0.1:8083 answered `GET /health` with 200 and a `max_tokens: 8` chat completion
with 200. The rate limit returned 429 after the burst, and `DELETE` returned 403.
