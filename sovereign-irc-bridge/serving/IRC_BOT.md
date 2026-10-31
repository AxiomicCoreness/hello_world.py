# IRC bot mode (`!llm` in an IRC channel)

`src/irc_llm_bot.py` connects **out** to an IRC network, joins one channel and answers
`!llm <question>` there (and any private message) with the same `/llm` path the TeaVM page uses:
DeepInfer on 127.0.0.1:8090 first, then the deepseek-r2 tutor on 127.0.0.1:8085, per-session
history, `[thinking]` replies, `!llm status`, `!llm reset`. It needs **no domain, no `wss://` and
no open ports**: the PC only makes an outgoing TLS connection. The model stays on 127.0.0.1.

Default network: **abjects** (`irc.abjects.net:6697`, TLS), the same network the bridge and the
Pages chatbox (`wss://irc.abjects.net:6680/`) use. 6697 is abjects' documented SSL port
(<https://www.abjects.net/faq.html>: `/server irc.abjects.net:+6697`; the network MOTD lists SSL on
6697 and 6699). On abjects `IRC_OWNER` is optional and no SASL secret is needed. Libera.Chat and
other networks still work by env, e.g. `IRC_HOST=irc.libera.chat` (then Libera's rules below apply).

## Commands in IRC

| You type | What happens |
|---|---|
| `!llm <question>` (in the channel) | answer in the channel, `yournick: …`, max `IRC_MAX_LINES` (4) lines, then `…(truncated, ask in PM for more)` |
| `/msg ClarkeTutorBot <question>` | answer in PM, up to `IRC_MAX_LINES_PM` (25) lines |
| `!llm status` | the bridge's `/llm status` (DeepInfer deps, GGUF sha256) |
| `!llm reset` | archives **your** history only (session `irc-<yournick>`) |
| `!llm help` | one-line help |

Every line the bot sends starts with `[LLM]`. Each nick has its own history session
`irc-<nick>` (lower-cased, other characters → `_`, `[A-Za-z0-9_-]{1,64}`). Per nick: one question
every `IRC_RATE_S` (15) seconds and one at a time; the model answers one question at a time.

## Settings (env)

| Var | Default | |
|---|---|---|
| `IRC_HOST` | `irc.abjects.net` | `irc.libera.chat` etc. also work |
| `IRC_PORT` | `6697` (TLS); with `IRC_TLS=0`: `6669` on abjects (the bridge's known port), `6667` elsewhere | |
| `IRC_TLS` | `1` | plaintext only with an explicit `IRC_TLS=0`; TLS on a plaintext port (6666-6669, 7000) is refused at startup |
| `IRC_TLS_VERIFY` | `1` | `0` skips certificate checks (warning logged) |
| `IRC_NICK` | `ClarkeTutorBot` | |
| `IRC_CHANNEL` | `#axiomiccoreness` | the only channel it ever joins |
| `IRC_OWNER` | — | **your** nick; optional on abjects, required on Libera. Shown in the bot's realname as admin |
| `IRC_REQUIRE_OWNER` | `1` on Libera (with `IRC_OWNER`), `0` elsewhere | `1`: channel answers only while you are in the channel (opt-in on abjects) |
| `IRC_SASL_PASS` / `IRC_SASL_USER` | — / `IRC_NICK` | optional SASL PLAIN login (needed on Libera from cloud IPs; not needed on abjects) |
| `IRC_NICKSERV_PASS` | — | `IDENTIFY` after connect, only when SASL is not set |
| `IRC_LLM_TAG` | `[LLM]` | prefix on every line |
| `IRC_SEND_INTERVAL_S` | `2.0` | one line every 2 s on every network |
| `IRC_MAX_LINES` / `IRC_MAX_LINES_PM` | `4` / `25` | |
| `IRC_RATE_S` | `15` | per-nick |
| `IRC_SHOW_THINKING` | `0` | `1` also sends the `[thinking]` block (otherwise one "hidden" line) |
| `IRC_BACKOFF_MAX_S` | `300` | reconnect backoff 1, 2, 4 … 300 s, forever |
| `IRC_PING_TIMEOUT_S` | `240` | silence → bot PINGs; silence again → reconnect |

Passwords are read from env only and never logged. `launch-irc-bot.sh` sets the same `LLM_*`
values as `launch-6680-deepseek-r2.sh`.

The bot never exits on idle, on a disconnect, on a server `ERROR`/K-line or on a model error; it
reconnects with backoff forever. Only a bad setting at startup stops it (exit code 2 with one clear
message, e.g. a model URL that is not 127.0.0.1). Ctrl-C / SIGTERM sends `QUIT` and stops.

## Etiquette on every network (abjects default)

The bot always: joins only `IRC_CHANNEL` (ignores `INVITE`; model output can never make it join
anything), does not rejoin after a `KICK`, labels itself an LLM bot in its realname (with its admin
when `IRC_OWNER` is set), tags every line `[LLM]`, sends only `!llm` lines and PMs addressed to it
to the model, rate-limits each nick (`IRC_RATE_S`) and sends at most one line every 2 s.
abjects' AUP (<https://www.abjects.net/aup.html>, "Bots Policy") allows bots that are not
malicious and removes them if asked; it has no LLM-specific rule and no owner/SASL requirement.
Still, say in the channel topic that an `[LLM]` bot answers `!llm`, and don't mass-register nicks.

## Libera.Chat rules (only when `IRC_HOST` is a Libera host)

From <https://libera.chat/policies/#bots> (bot + LLM policy). The bot refuses to start on Libera
without `IRC_OWNER` and, there, stays silent in the channel while its owner is absent:

1. **Use a channel you run, opted in to LLMs.** Channels are opted out of LLMs by default.
   Register it and put the disclosure in the topic (as its op):
   `/msg ChanServ REGISTER #axiomiccoreness` then
   `/topic #axiomiccoreness LLM bot present: ClarkeTutorBot answers !llm (replies tagged [LLM]); messages starting with !llm and PMs to it are sent to a local model and kept as history.`
2. **Be in the channel with it.** An LLM bot must be accompanied by its admin; with `IRC_OWNER`
   set the bot stays silent in the channel while you are not there.
3. **Voice the bot** so it is visibly marked and exempt from flood mitigation:
   `/msg ChanServ FLAGS #axiomiccoreness ClarkeTutorBot +V`.
4. **Register the bot's nick** (from a home connection, not a VPN/cloud IP):
   connect as `ClarkeTutorBot` with any client, `/msg NickServ REGISTER <password> <email>`, verify
   the e-mail. Then give the bot `IRC_SASL_PASS=<password>`.
5. The bot already: joins only `IRC_CHANNEL` (ignores `INVITE`, model output can never make it
   join anything), does not rejoin after a `KICK`, names its admin in its realname, tags every
   line `[LLM]`, sends only `!llm` lines and PMs addressed to it to the model, and sends at most
   one line every 2 s.

## Run it on your PC (always-on)

Linux / macOS (model first, then the bot):

```bash
git clone https://github.com/AxiomicCoreness/hello_world.py.git && cd hello_world.py/sovereign-irc-bridge && python3 -m pip install -e .
./serving/models/fetch-deepseek-r2.sh
LLAMA_SERVER=/path/to/llama-server ./serving/launch-8085-deepseek-r2.sh &
bash serving/launch-irc-bot.sh                       # abjects, TLS 6697, no owner/SASL needed
# optional: IRC_OWNER=YourNick (admin in realname); IRC_NICKSERV_PASS=... if you registered the nick
# Libera instead: IRC_HOST=irc.libera.chat IRC_OWNER=YourNick IRC_SASL_PASS='bot-nickserv-password' bash serving/launch-irc-bot.sh
# plaintext abjects (only if TLS 6697 is blocked on your network): IRC_TLS=0 bash serving/launch-irc-bot.sh  → 6669
```

`llama-server`: build llama.cpp, or on macOS `brew install llama.cpp`, or unpack a release from
<https://github.com/ggml-org/llama.cpp/releases>. To keep both running after logout and reboots on
Linux, use the example user units in `serving/systemd/` (`llama-8085.service`,
`irc-llm-bot.service`; secrets go in `~/.config/sovereign-bridge/irc.env`, `chmod 600`).
On macOS use a LaunchAgent or simply `caffeinate -s bash serving/launch-irc-bot.sh` in a Terminal tab;
the Mac must not sleep.

Windows (PowerShell; Python 3.11+, llama.cpp Windows zip from the releases page):

```powershell
cd hello_world.py\sovereign-irc-bridge; py -m pip install -e .
# download deepseek-r2-1.5b-Q4_K_M.gguf from the release link in serving/README.md into serving\models\
Start-Process .\llama-server.exe -ArgumentList '-m serving\models\deepseek-r2-1.5b-Q4_K_M.gguf --jinja --host 127.0.0.1 --port 8085 -c 4096 -np 1 --alias deepseek-r2-1.5b'
$env:IRC_HOST='irc.abjects.net'; $env:LLM_BACKEND='deepinfer'; $env:LLM_FALLBACK='clarkeyoursatee'; $env:LLM_CLARKEYOURSATEE_URL='http://127.0.0.1:8085/v1/chat/completions'; $env:LLM_CLARKEYOURSATEE_MODEL='deepseek-r2-1.5b'; $env:LLM_MAX_TOKENS='1024'; $env:LLM_HISTORY_PATH="$env:LOCALAPPDATA\sovereign-bridge\llm_history.jsonl"
py -m src.irc_llm_bot
```

(Optional: `$env:IRC_OWNER='YourNick'`; for Libera also `$env:IRC_HOST='irc.libera.chat'`, `$env:IRC_OWNER` and `$env:IRC_SASL_PASS`.)
Turn off sleep in Power settings; Task Scheduler ("At log on", "Restart on failure") keeps it running.

## Run it from GitHub Actions (temporary, NOT always-on)

`.github/workflows/irc-llm-bot-session.yml` is a **manual** workflow (Actions → *IRC LLM bot
session (manual, temporary)* → Run workflow). It downloads a pinned, sha256-checked llama.cpp
build and the pinned deepseek-r2 GGUF from this repo's release, starts llama-server on the
runner's 127.0.0.1:8085 and runs the bot for `minutes` (max 330). The job is capped at 350 minutes,
under GitHub's 6-hour limit, so **each run is one session of at most ~5.5 hours**; afterwards the
bot quits until someone runs it again. It runs the bot directly on the runner (a kind/Kubernetes
cluster would add nothing for a single process). It never runs on push, pull requests or a schedule
and is not a required check.

On abjects (the default `irc_host`) no secret and no `irc_owner` are needed. Only for
`*.libera.chat`: Libera puts cloud IP ranges (GitHub runners included) on SASL-only access, so the
workflow refuses to start there unless the repository secret `IRC_SASL_PASS` is set (optional
`IRC_SASL_USER`) and `irc_owner` is filled in. The CPU-only runner answers slowly (tens of seconds per reply).

## Tests

`python -I -m pytest -q src/test_irc_llm_bot.py` runs offline against a fake IRC server on
127.0.0.1 (registration, SASL, JOIN, PING/PONG, `!llm` routing incl. through the real
`llm_chat.handle_llm` with a stub llama-server, 512-byte UTF-8 splitting, CR/LF stripping, rate
limits, abjects defaults without owner/SASL, Libera-only owner requirement and presence gating, KICK/INVITE handling, reconnect after a drop, server down at start, ping
timeout). A live run against a real IRC network has to happen on your PC.
