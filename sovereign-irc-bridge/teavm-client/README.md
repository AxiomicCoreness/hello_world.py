# TeaVM client (wired, not duplicated)

Do **not** invent a second TeaVM webapp here. The browser surface is the
existing debug-oracle panel:

- `games/teavm-rhythm/src/main/webapp/debug-oracle/index.html`
- `games/teavm-rhythm/src/main/webapp/debug-oracle/hex_locks.json`

Team channel **UI labels**: `irc.abjects.net:6666`–`6669` (no live sockets in CI).

The bridge FastAPI app mounts that directory at `/debug-oracle/`. Dockerfile
copies the same path into the image. When a live WS dial exists, point the
panel’s command prompt `oracle` / channel labels at `wss://<bridge>/ws`.
