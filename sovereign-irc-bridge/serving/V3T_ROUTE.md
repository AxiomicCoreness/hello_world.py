# v3t `/llm` route (single-user, authenticated)

Clarke Yoursa Tee is the only user. One **owner token** is shared by Clarke Pocket on the iPhone and
the TeaVM CLI page in the browser. The server stores only its sha256; there is one shared history.

```
iPhone (Server (v3t) engine) ─┐                                   ┌─ llama-server 127.0.0.1:8085
TeaVM page  (/v3t …)        ──┼─ https://bridge.axiomiccoreness.com ─► v3t_route 127.0.0.1:8087 ─┤
                              │      (tunnel / reverse proxy — NOT live yet, see below)            └─ SQLite (mode 600, outside repo)
```

* Start: `serving/launch-v3t-route.sh` (binds 127.0.0.1 only; refuses anything else).
* Token admin (prints no token values):
  `V3T_DB=… python3 -I src/device_tokens.py mint owner --out /path/owner.token` · `revoke owner` · `list`.
  Minting `owner` again rotates it (old one revoked).
* History: #171 schema (`sessions` / `messages`) + `v3t_turn_meta` (conversation id, client label,
  model sha256, ISO 8601 `+00:00` ts). `GET /llm/history`, `GET /llm/history/<id>`.
* CORS: `https://axiomiccoreness.github.io` and loopback pages only.
* iPhone: Settings → Server (v3t) → paste token (saved in Keychain). TeaVM: `/v3t token <tok>`
  (saved only in that browser's localStorage), then `/v3t <text>`, `/v3t history`, `/v3t open <id>`.
* Chat history is private: never on Pages, never in CI artifacts, never in the repo.

## Public hostname

`bridge.axiomiccoreness.com` is **not** currently routed to the serving box (no tunnel runs; the
box's outbound network has blocked Cloudflare tunnel edges before). Until a tunnel or reverse proxy
that terminates TLS and forwards `/llm/*` to `127.0.0.1:8087` is in place, only loopback clients work.

## Time and web tools

* Every request gets the v3t identity prompt (if none was sent), a tool few-shot, and a fresh
  `Current time: <America/New_York ±hh:mm> (UTC …Z)` line.
* llama-server 8085 uses `chat-templates/clarkeyoursatee-v3t-time.jinja` (run with
  `TZ=America/New_York … --jinja --chat-template-file …`), so its built-in UI also defaults to the
  identity and the current time (UTC computed from `strftime_now('%s')`).
* Tools: `web_fetch(url)` / `web_search(query)` in Qwen `<tool_call>` format, up to 3 rounds.
  http(s) only, 512 KiB cap, 10 s timeout, public addresses only (checked on resolve and on the
  connected peer, every redirect), User-Agent only. `V3T_FETCH_ALLOW_NETS` is an explicit opt-in for
  a sandbox resolver that maps names into a reserved range (e.g. `198.18.0.0/15`); loopback stays blocked.
