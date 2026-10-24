# TeaVM client (wired, not duplicated)

Do **not** invent a second TeaVM webapp here. The browser surface is the
existing debug-oracle panel:

- `games/teavm-rhythm/src/main/webapp/debug-oracle/index.html`
- `games/teavm-rhythm/src/main/webapp/debug-oracle/hex_locks.json`

Java-side TeaVM → IRC mTLS bridge stubs (pure logic, no live sockets):

- `games/teavm-rhythm/src/main/java/com/fruitfly/games/rhythm/irc/IrcBridgeConfig.java`
- `games/teavm-rhythm/src/main/java/com/fruitfly/games/rhythm/irc/MtlsToolCall.java` — `/mtls` tool call
- `games/teavm-rhythm/src/main/java/com/fruitfly/games/rhythm/irc/IrcBridgeClientStub.java` — WS dial *plan* only

Team channel **UI labels**: `irc.abjects.net:6666`–`6669` (no live sockets in CI).
Live path: TeaVM/browser → `ws(s)://<bridge>/ws` → bridge mTLS TCP →
`irc.abjects.net:6697` (PEMs via `IRC__MTLS_*`).

The bridge FastAPI app mounts that directory at `/debug-oracle/`. Dockerfile
copies the same path into the image. When a live WS dial exists, point the
panel’s command prompt `oracle` / channel labels at `wss://<bridge>/ws`.

## Rhythm page left CLI

The main game page (`games/teavm-rhythm/src/main/webapp/index.html`) also
hosts `#irc-chatbox` to the **left** of the stage (game + Euclidean docs stay
to the right). Java: `IrcChatCli` + `IrcChatBox`, default target
`irc.abjects.net:6669`, dial via `IrcBridgeClientStub.planDial()` (no live WS
in CI). Commands: `/connect`, `/mtls`, `/status`, `/disconnect`, `/help`.

## Rhythm page left CLI (Cosmic Alignment)

Layout grid `300px 1fr 350px`: `#cli-column` | stage | Euclidean `.side`.

- Java: `web/CliClient` → **`ws://127.0.0.1:6680/cli`** (loopback only).
- Bridge: `python -m src.cli_loopback` binds **127.0.0.1:6680** (rejects `0.0.0.0`).
- Remote label: `irc.abjects.net:6669` behind the bridge — not a browser-direct dial.

### pythonIDE in the left CLI

Commands `/py help`, `/py list`, `/py call <cap>`, `/py pointer` are handled by
`src/cli_loopback.py` via `pythonIDE.toolkit` / `pointer_2300`. Failures return
`[Traceback]` lines into chat history. Local/CI: `ws://127.0.0.1:6680/cli`.

Demos on the same path:

- `/py deepinfer` — `engine.deepinfer_accelerator` status (optional `demo`/`probe`/`complete`)
- `/py katex` / `/katex` — runs `mvn test -Dtest=KaTeXMacroSetTest` when Maven is
  available, otherwise a python mirror of `KaTeXTreeValidator` + darklambda check
- Aliases: `/deepinfer`, `/katex`
