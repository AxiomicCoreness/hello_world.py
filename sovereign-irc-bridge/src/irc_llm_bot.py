# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""IRC bot mode for the `/llm` chat: connect OUT to an IRC network and answer in a channel.

Run on the PC that serves the model (llama-server stays on 127.0.0.1)::

    python -m src.irc_llm_bot

The bot only makes an outgoing TCP (TLS by default) connection, so it needs no
domain, no ``wss://`` and no open ports. Every model call goes through
:func:`src.llm_chat.handle_llm` — same backend order (DeepInfer 127.0.0.1:8090,
then the tutor on 127.0.0.1:8085 via ``LLM_FALLBACK``), same per-session history,
same raw ``[thinking]`` replies, same ``/llm status`` and ``/llm reset``. This
module only adds the IRC transport; it holds no LLM logic of its own.

Who it answers:
  * channel messages that start with ``!llm `` (``!llm status``, ``!llm reset``,
    ``!llm help``, ``!llm <question>``);
  * any private message to the bot (the whole line is the prompt; a leading
    ``!llm`` is accepted too).
Each nick gets its own history session ``irc-<sanitized nick>`` (matches the
bridge's ``[A-Za-z0-9_-]{1,64}`` session rule), so ``!llm reset`` only clears
that nick's turns.

Env (all optional):
  IRC_HOST            irc.abjects.net (irc.libera.chat and other networks via env)
  IRC_PORT            6697 (TLS; abjects' documented SSL port, /server irc.abjects.net:+6697);
                      plaintext needs an explicit IRC_TLS=0 and then defaults to 6669 on abjects
                      (the bridge's known port), 6667 elsewhere
  IRC_TLS             1. Plaintext only with an explicit IRC_TLS=0.
  IRC_TLS_VERIFY      1. 0 accepts any server certificate (logged as a warning).
  IRC_NICK            ClarkeTutorBot
  IRC_CHANNEL         #axiomiccoreness
  IRC_CHANNEL_KEY     channel key (+k), if the channel has one
  IRC_OWNER           your own IRC nick: shown in the bot's realname as its admin, and
                      on Libera.Chat the bot only answers in the channel while you are in it.
                      Required on Libera.Chat (bot + LLM policy); optional on abjects.
  IRC_REQUIRE_OWNER   default 1 on Libera.Chat (IRC_OWNER must be present for channel answers),
                      0 elsewhere; set 1 with IRC_OWNER to opt in on abjects
  IRC_LLM_TAG         [LLM]  prefix on every line the bot sends (LLM output must be marked)
  IRC_SASL_USER       SASL PLAIN account (default: IRC_NICK). Optional everywhere in the bot;
  IRC_SASL_PASS       Libera requires SASL from cloud ranges (e.g. GitHub Actions); never logged
  IRC_NICKSERV_PASS   sent to NickServ as IDENTIFY after registration when SASL is not set; never logged
  IRC_SEND_INTERVAL_S 2.0   flood control (Libera: one message every two seconds): seconds between outgoing lines
  IRC_MAX_LINES       4     lines per reply in the channel, then "…(truncated, ask in PM for more)"
  IRC_MAX_LINES_PM    25    lines per reply in a private message
  IRC_RATE_S          15    per-nick: minimum seconds between two questions
  IRC_SHOW_THINKING   0     1 = also send the model's [thinking] block (costs lines)
  IRC_BACKOFF_MAX_S   300   reconnect backoff cap (1, 2, 4 … 300 s, forever)
  IRC_PING_TIMEOUT_S  240   silence before the bot PINGs the server; twice that → reconnect

Network etiquette (kept on every network; modelled on the Libera.Chat bot/LLM policy,
https://libera.chat/policies/#bots, whose admin-present rule is enforced only on Libera):
the bot joins only IRC_CHANNEL (never on INVITE, never because of model output),
does not rejoin after a KICK, labels itself as a bot with its admin in the realname,
marks every line with IRC_LLM_TAG, sends only the ``!llm`` lines and PMs addressed
to it to the model (it does not read other channel traffic), and is rate-limited.

Lifecycle: the bot never exits on idle, on a disconnect, on a K-line or on a
model error — it reconnects with exponential backoff forever. Only an invalid
configuration at startup ends the process (exit code 2, one clear message).
SIGINT/SIGTERM send QUIT and stop cleanly.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import random
import re
import signal
import ssl
import sys
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, List, Mapping, Optional, Tuple

logger = logging.getLogger("sovereign-irc-bridge.irc-bot")

ABJECTS_HOST = "irc.abjects.net"
LIBERA_HOST = "irc.libera.chat"  # still selectable: IRC_HOST=irc.libera.chat
DEFAULT_HOST = ABJECTS_HOST
DEFAULT_TLS_PORT = 6697  # abjects FAQ: /server irc.abjects.net:+6697 (MOTD: SSL 6697, 6699)
DEFAULT_PLAIN_PORT = 6667
ABJECTS_PLAIN_PORT = 6669  # the bridge's known abjects port; only with an explicit IRC_TLS=0
PLAINTEXT_PORTS = (6666, 6667, 6668, 6669, 7000)  # abjects MOTD "standard" ports; 6667 everywhere
DEFAULT_NICK = "ClarkeTutorBot"
DEFAULT_CHANNEL = "#axiomiccoreness"
TRIGGER = "!llm"
DEFAULT_LLM_TAG = "[LLM]"  # LLM-generated content is explicitly marked on every network
IRC_LINE_MAX = 512  # bytes, including the trailing CRLF (RFC 1459 §2.3)
# Room the server adds when it relays our PRIVMSG: ":nick!user@host " (host ≤ 63).
RELAY_PREFIX_RESERVE = 1 + 1 + 1 + 10 + 1 + 63 + 1
TRUNCATED_CHANNEL = "…(truncated, ask in PM for more)"
TRUNCATED_PM = "…(truncated)"
NICK_RE = re.compile(r"^[A-Za-z\[\]\\`_^{|}][A-Za-z0-9\[\]\\`_^{|}-]{0,29}$")
CHANNEL_RE = re.compile(r"^[#&][^\x00\x07\r\n ,:]{1,49}$")
SESSION_SAFE_RE = re.compile(r"[^A-Za-z0-9_-]")
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")  # C0 controls incl. IRC colour codes; CR/LF/TAB mapped first
# Bridge reply lines that only describe routing; IRC users get the answer, not the plumbing.
_QUIET_SYSTEM = ("[System] llm session:", "[System] llm ctx:", "[System] llm route:")
_ENGINE_PREFIX = "[Engine] llm: "
_PROV_RE = re.compile(r"^\[[^\]]*\] ")
_THINK_MARK_RE = re.compile(r"\[(/?)thinking\]")

LlmHandler = Callable[[str, str], Awaitable[List[str]]]


def _host_is(host: str, domain: str) -> bool:
    h = host.lower().rstrip(".")
    return h == domain or h.endswith("." + domain)


def is_libera(host: str) -> bool:
    """True for Libera.Chat hosts (libera.chat and *.libera.chat): Libera-only rules apply."""
    return _host_is(host, "libera.chat")


def is_abjects(host: str) -> bool:
    return any(_host_is(host, d) for d in ("abjects.net", "abjects.org", "abjects.com", "abjects.us"))


class ConfigError(ValueError):
    """Invalid IRC bot configuration — the only reason the bot exits."""


def _flag(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    v = raw.strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    raise ConfigError(f"{name} must be 0 or 1, got {raw!r}")


def _number(env: Mapping[str, str], name: str, default: float, lo: float, hi: float) -> float:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        v = float(raw)
    except ValueError:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from None
    if not lo <= v <= hi:
        raise ConfigError(f"{name} must be between {lo:g} and {hi:g}, got {raw!r}")
    return v


@dataclass(frozen=True)
class BotConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_TLS_PORT
    tls: bool = True
    tls_verify: bool = True
    nick: str = DEFAULT_NICK
    channel: str = DEFAULT_CHANNEL
    channel_key: str = field(default="", repr=False)
    nickserv_pass: str = field(default="", repr=False)
    owner: str = ""
    require_owner: bool = False
    llm_tag: str = DEFAULT_LLM_TAG
    sasl_user: str = ""
    sasl_pass: str = field(default="", repr=False)
    send_interval_s: float = 2.0
    max_lines: int = 4
    max_lines_pm: int = 25
    rate_s: float = 15.0
    show_thinking: bool = False
    backoff_base_s: float = 1.0
    backoff_max_s: float = 300.0
    ping_timeout_s: float = 240.0
    ca_file: str = ""  # tests: trust a local CA

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "BotConfig":
        env = os.environ if env is None else env
        tls = _flag(env, "IRC_TLS", True)
        host = (env.get("IRC_HOST") or DEFAULT_HOST).strip()
        if not host or any(c in host for c in " /\r\n"):
            raise ConfigError(f"IRC_HOST is not a hostname: {host!r}")
        raw_port = (env.get("IRC_PORT") or "").strip()
        if raw_port:
            try:
                port = int(raw_port)
            except ValueError:
                raise ConfigError(f"IRC_PORT must be an integer, got {raw_port!r}") from None
            if not 1 <= port <= 65535:
                raise ConfigError(f"IRC_PORT out of range: {port}")
        else:
            port = DEFAULT_TLS_PORT if tls else (ABJECTS_PLAIN_PORT if is_abjects(host) else DEFAULT_PLAIN_PORT)
        if tls and port in PLAINTEXT_PORTS:
            raise ConfigError(f"IRC_PORT={port} is a plaintext port; set IRC_TLS=0 to allow plaintext, "
                              "or use 6697 with TLS")
        nick = (env.get("IRC_NICK") or DEFAULT_NICK).strip()
        if not NICK_RE.fullmatch(nick):
            raise ConfigError(f"IRC_NICK is not a valid IRC nick: {nick!r}")
        channel = (env.get("IRC_CHANNEL") or DEFAULT_CHANNEL).strip()
        if not CHANNEL_RE.fullmatch(channel):
            raise ConfigError(f"IRC_CHANNEL must look like #name, got {channel!r}")
        key = env.get("IRC_CHANNEL_KEY") or ""
        pw = env.get("IRC_NICKSERV_PASS") or ""
        sasl_pass = env.get("IRC_SASL_PASS") or ""
        sasl_user = (env.get("IRC_SASL_USER") or "").strip() or (nick if sasl_pass else "")
        owner = (env.get("IRC_OWNER") or "").strip()
        if owner and not NICK_RE.fullmatch(owner):
            raise ConfigError(f"IRC_OWNER is not a valid IRC nick: {owner!r}")
        if owner and owner.lower() == nick.lower():
            raise ConfigError("IRC_OWNER must be a person, not the bot's own nick")
        libera = is_libera(host)
        if libera and not owner:
            raise ConfigError("Libera.Chat requires a bot to name a reachable admin: set IRC_OWNER to your own nick "
                              "(and be in the channel with the bot)")
        tag = (env.get("IRC_LLM_TAG") if env.get("IRC_LLM_TAG") is not None else DEFAULT_LLM_TAG).strip()
        for name, val in (("IRC_CHANNEL_KEY", key), ("IRC_NICKSERV_PASS", pw), ("IRC_SASL_PASS", sasl_pass),
                          ("IRC_SASL_USER", sasl_user), ("IRC_LLM_TAG", tag)):
            if any(c in val for c in "\r\n\x00"):
                raise ConfigError(f"{name} contains a line break")
        if " " in key:
            raise ConfigError("IRC_CHANNEL_KEY contains a space")
        return cls(
            host=host, port=port, tls=tls, tls_verify=_flag(env, "IRC_TLS_VERIFY", True),
            nick=nick, channel=channel, channel_key=key, nickserv_pass=pw,
            owner=owner, require_owner=_flag(env, "IRC_REQUIRE_OWNER", libera) and bool(owner),
            llm_tag=tag, sasl_user=sasl_user, sasl_pass=sasl_pass,
            send_interval_s=_number(env, "IRC_SEND_INTERVAL_S", 2.0, 0.0, 60.0),
            max_lines=int(_number(env, "IRC_MAX_LINES", 4, 1, 50)),
            max_lines_pm=int(_number(env, "IRC_MAX_LINES_PM", 25, 1, 500)),
            rate_s=_number(env, "IRC_RATE_S", 15.0, 0.0, 3600.0),
            show_thinking=_flag(env, "IRC_SHOW_THINKING", False),
            backoff_base_s=_number(env, "IRC_BACKOFF_BASE_S", 1.0, 0.01, 60.0),
            backoff_max_s=_number(env, "IRC_BACKOFF_MAX_S", 300.0, 0.01, 3600.0),
            ping_timeout_s=_number(env, "IRC_PING_TIMEOUT_S", 240.0, 0.05, 3600.0),
            ca_file=(env.get("IRC_CA_FILE") or "").strip(),
        )


# ---------------------------------------------------------------- IRC wire helpers

def sanitize(text: str) -> str:
    """One safe IRC parameter: no CR/LF/NUL (no command injection), no CTCP \\x01."""
    text = (text or "").replace("\r\n", " ").replace("\r", " ").replace("\n", " ").replace("\t", "    ")
    return _CTRL_RE.sub("", text.replace("\x01", "")).strip("\x00")


def session_for(nick: str) -> str:
    """IRC nick → bridge session ``irc-<nick>`` within ``[A-Za-z0-9_-]{1,64}``."""
    safe = SESSION_SAFE_RE.sub("_", (nick or "").lower())[:60] or "anon"
    return f"irc-{safe}"


def parse_line(line: str) -> Tuple[str, str, List[str]]:
    """``:prefix CMD a b :trailing`` → (prefix, CMD, [a, b, trailing])."""
    prefix = ""
    if line.startswith(":"):
        prefix, _, line = line[1:].partition(" ")
    if " :" in line:
        head, _, trailing = line.partition(" :")
        params = head.split()
        params.append(trailing)
    else:
        params = line.split()
    cmd = params.pop(0).upper() if params else ""
    return prefix, cmd, params


def nick_of(prefix: str) -> str:
    return prefix.split("!", 1)[0]


def split_utf8(text: str, max_bytes: int) -> List[str]:
    """Split ``text`` into pieces of ≤ ``max_bytes`` UTF-8 bytes, never inside a character;
    prefers to break at the last space."""
    max_bytes = max(8, max_bytes)
    out: List[str] = []
    text = text.strip()
    while text:
        if len(text.encode("utf-8")) <= max_bytes:
            out.append(text)
            break
        used, cut = 0, 0
        for i, ch in enumerate(text):
            used += len(ch.encode("utf-8"))
            if used > max_bytes:
                cut = i
                break
        space = text.rfind(" ", 0, cut + 1)
        if space > cut // 2:
            cut = space
        piece = text[:cut].rstrip()
        out.append(piece if piece else text[:1])
        text = text[max(cut, 1):].lstrip()
    return out


def payload_budget(nick: str, target: str) -> int:
    """Bytes left for the message text once the server relays ``PRIVMSG target :…``."""
    overhead = len(f"PRIVMSG {target} :\r\n".encode("utf-8")) + RELAY_PREFIX_RESERVE + len(nick.encode("utf-8"))
    return IRC_LINE_MAX - overhead


def bridge_lines_to_irc(lines: List[str], *, show_thinking: bool) -> List[str]:
    """``handle_llm`` output → plain chat lines.

    Routing chatter (session/ctx/route) is dropped; ``[System]`` answers such as
    ``llm order``, ``llm offline``, status and reset are kept. The provenance
    prefix (e.g. ``[ClarkeYoursaTee (deepseek-r2-1.5b)] ``) is kept on the first
    reply line only, to save IRC bytes. The ``[thinking]`` block is collapsed to
    one line unless ``show_thinking``.
    """
    out: List[str] = []
    in_think = False
    hidden = 0
    seen_prov = ""

    def emit(prov: str, body: str) -> None:
        nonlocal seen_prov
        if prov and prov != seen_prov:
            seen_prov = prov
            out.append(prov + body)
        else:
            out.append(body)

    for raw in lines:
        if any(raw.startswith(p) for p in _QUIET_SYSTEM):
            continue
        if not raw.startswith(_ENGINE_PREFIX):
            if raw.strip():
                out.append(raw)
            continue
        text = raw[len(_ENGINE_PREFIX):]
        m = _PROV_RE.match(text)
        prov = m.group(0) if m else ""
        body = text[len(prov):]
        marker = _THINK_MARK_RE.fullmatch(body.strip())
        if marker:
            in_think = marker.group(1) == ""
            if show_thinking:
                emit(prov, body)
            elif not in_think and hidden:
                emit(prov, f"(thinking: {hidden} line(s) hidden; IRC_SHOW_THINKING=1 shows them)")
            if not in_think:
                hidden = 0
            continue
        if in_think and not show_thinking:
            if body.strip():
                hidden += 1
            continue
        if body.strip():
            emit(prov, body)
    return out or ["(empty reply)"]


async def default_llm_handler(prompt: str, session: str) -> List[str]:
    """The bridge's own `/llm` path — no LLM logic lives in this module."""
    from src import llm_chat

    return await llm_chat.handle_llm(f"/llm {prompt}".rstrip(), session)


def check_loopback_backends() -> None:
    """Fail fast if any model URL leaves 127.0.0.1 (the model never faces the network)."""
    from src import llm_backend, llm_chat

    try:
        llm_chat.llm_url()
        llm_chat.deepinfer_url()
        llm_chat.assert_loopback_url(llm_backend.clarkeyoursatee_url_raw(), "LLM_CLARKEYOURSATEE_URL")
        llm_chat.assert_loopback_url(llm_backend.abliterated_url_raw(), "LLM_ABLITERATED_URL")
    except llm_chat.LlmConfigError as exc:
        raise ConfigError(str(exc)) from None


def backoff_delay(attempt: int, base: float, cap: float, jitter: float = 0.2) -> float:
    """Exponential reconnect delay: base·2^attempt, capped at ``cap``, minus up to 20 % jitter."""
    delay = min(cap, base * (2 ** min(attempt, 30)))
    return delay * (1.0 - random.uniform(0.0, jitter))


# ---------------------------------------------------------------- the bot

class IrcLlmBot:
    def __init__(self, cfg: BotConfig, llm: Optional[LlmHandler] = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.cfg = cfg
        self.llm = llm or default_llm_handler
        self.clock = clock
        self.nick = cfg.nick
        self.registered = asyncio.Event()
        self.joined = asyncio.Event()
        self.connections = 0
        self._stop = asyncio.Event()
        self._writer: Optional[asyncio.StreamWriter] = None
        self._outq: "asyncio.Queue[str]" = asyncio.Queue()
        self._last_ask: Dict[str, float] = {}
        self._warned: Dict[str, float] = {}
        self._inflight: set = set()
        self._model_lock = asyncio.Lock()
        self._tasks: set = set()
        self._nick_tries = 0
        self._kicked = False          # Libera etiquette: never auto-rejoin after a KICK
        self.members: set = set()     # lower-cased nicks in IRC_CHANNEL (owner-presence check)

    @property
    def owner_present(self) -> bool:
        return not self.cfg.require_owner or self.cfg.owner.lower() in self.members

    def realname(self) -> str:
        admin = f", admin: {self.cfg.owner}" if self.cfg.owner else ""
        return f"LLM bot (ClarkeYoursaTee /llm tutor; replies tagged {self.cfg.llm_tag or 'LLM'}){admin}"

    # -- lifecycle ---------------------------------------------------------
    def stop(self) -> None:
        self._stop.set()

    async def run_forever(self) -> None:
        """Connect, serve, and on ANY drop reconnect with backoff — until stop()."""
        attempt = 0
        while not self._stop.is_set():
            started = self.clock()
            session = asyncio.ensure_future(self._session())
            stopper = asyncio.ensure_future(self._stop.wait())
            await asyncio.wait({session, stopper}, return_when=asyncio.FIRST_COMPLETED)
            stopper.cancel()
            if self._stop.is_set():
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(self._raw("QUIT :bye"), timeout=2)
                session.cancel()
                with contextlib.suppress(BaseException):
                    await session
                break
            exc = session.exception()
            # Any drop is recoverable: network, TLS, ping timeout, server ERROR/K-line.
            reason = "server closed the connection" if exc is None else f"{type(exc).__name__}: {exc}"
            if self.clock() - started > 60 or self.registered.is_set():
                attempt = 0
            delay = backoff_delay(attempt, self.cfg.backoff_base_s, self.cfg.backoff_max_s)
            attempt = min(attempt + 1, 30)
            logger.warning("irc: disconnected (%s); reconnecting in %.1fs", reason, delay)
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._stop.wait(), timeout=delay)
        logger.info("irc: stopped")

    async def _open(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        ctx: Optional[ssl.SSLContext] = None
        if self.cfg.tls:
            ctx = ssl.create_default_context(cafile=self.cfg.ca_file or None)
            if not self.cfg.tls_verify:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
        return await asyncio.wait_for(
            asyncio.open_connection(self.cfg.host, self.cfg.port, ssl=ctx,
                                    server_hostname=self.cfg.host if ctx else None),
            timeout=30,
        )

    async def _session(self) -> None:
        self.registered.clear()
        self.joined.clear()
        self.members = set()
        self.nick = self.cfg.nick
        self._nick_tries = 0
        logger.info("irc: connecting to %s:%d (%s)", self.cfg.host, self.cfg.port,
                    "TLS" if self.cfg.tls else "plaintext")
        reader, writer = await self._open()
        self._writer = writer
        self.connections += 1
        sender = asyncio.create_task(self._sender(writer))
        try:
            if self.cfg.sasl_pass:
                await self._raw("CAP REQ :sasl")
            await self._raw(f"NICK {self.nick}")
            await self._raw(f"USER {self.cfg.nick.lower()[:10]} 0 * :{self.realname()}")
            await self._reader_loop(reader)
        finally:
            sender.cancel()
            with contextlib.suppress(BaseException):
                await sender
            self._writer = None
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    async def _reader_loop(self, reader: asyncio.StreamReader) -> None:
        pinged = False
        while not self._stop.is_set():
            try:
                raw = await asyncio.wait_for(reader.readline(), timeout=self.cfg.ping_timeout_s)
            except asyncio.TimeoutError:
                if pinged:
                    raise ConnectionError("ping timeout (server silent)") from None
                pinged = True
                await self._raw(f"PING :{self.cfg.host}")
                continue
            if not raw:
                return
            pinged = False
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if line:
                await self._on_line(line)

    # -- output ------------------------------------------------------------
    async def _raw(self, line: str, *, secret: bool = False) -> None:
        """Write one protocol line now (bypasses flood queue: PONG, registration)."""
        w = self._writer
        if w is None or w.is_closing():
            return
        line = line.replace("\r", " ").replace("\n", " ").replace("\x00", "")
        data = line.encode("utf-8")[: IRC_LINE_MAX - 2] + b"\r\n"
        if not secret:
            logger.debug("irc >> %s", line)
        w.write(data)
        await w.drain()

    def _tag(self) -> str:
        return f"{sanitize(self.cfg.llm_tag)} " if self.cfg.llm_tag else ""

    def say(self, target: str, text: str, cmd: str = "PRIVMSG") -> None:
        """Queue one message (tagged, sanitized, split to fit 512 bytes); flood-controlled."""
        tag = self._tag()
        for piece in split_utf8(sanitize(text), payload_budget(self.nick, target) - len(tag.encode("utf-8"))):
            self._outq.put_nowait(f"{cmd} {target} :{tag}{piece}")

    def notice(self, target: str, text: str) -> None:
        self.say(target, text, cmd="NOTICE")

    async def _sender(self, writer: asyncio.StreamWriter) -> None:
        await self.registered.wait()
        with contextlib.suppress(asyncio.TimeoutError):  # channel replies need the JOIN first
            await asyncio.wait_for(self.joined.wait(), timeout=10)
        while True:
            line = await self._outq.get()
            if writer.is_closing():
                self._outq.put_nowait(line)
                return
            await self._raw(line)
            if self.cfg.send_interval_s:
                await asyncio.sleep(self.cfg.send_interval_s)

    # -- input -------------------------------------------------------------
    async def _on_line(self, line: str) -> None:
        prefix, cmd, params = parse_line(line)
        if cmd == "PING":
            await self._raw(f"PONG :{params[-1] if params else ''}")
        elif cmd == "CAP" and len(params) >= 3:
            sub, caps = params[1].upper(), params[-1].split()
            if sub == "ACK" and "sasl" in caps:
                await self._raw("AUTHENTICATE PLAIN")
            elif sub == "NAK":
                logger.error("irc: server refused SASL; continuing without it")
                await self._raw("CAP END")
        elif cmd == "AUTHENTICATE" and params and params[0] == "+":
            import base64

            blob = f"{self.cfg.sasl_user}\0{self.cfg.sasl_user}\0{self.cfg.sasl_pass}".encode("utf-8")
            await self._raw("AUTHENTICATE " + base64.b64encode(blob).decode("ascii"), secret=True)
        elif cmd == "903":
            logger.info("irc: SASL login ok as %s", self.cfg.sasl_user)
            await self._raw("CAP END")
        elif cmd in ("902", "904", "905", "906", "908"):
            logger.error("irc: SASL login failed (%s %s); check IRC_SASL_USER / IRC_SASL_PASS", cmd, params[-1:])
            await self._raw("CAP END")
        elif cmd == "001":
            if params:
                self.nick = params[0]
            self.registered.set()
            logger.info("irc: registered as %s", self.nick)
            if self.cfg.nickserv_pass and not self.cfg.sasl_pass:
                await self._raw(f"PRIVMSG NickServ :IDENTIFY {self.cfg.nickserv_pass}", secret=True)
                logger.info("irc: sent NickServ IDENTIFY (password not logged)")
            if self._kicked:
                logger.warning("irc: not rejoining %s after a KICK; restart the bot once an op allows it",
                               self.cfg.channel)
            else:
                key = f" {self.cfg.channel_key}" if self.cfg.channel_key else ""
                await self._raw(f"JOIN {self.cfg.channel}{key}")
        elif cmd in ("433", "432", "436") and not self.registered.is_set():
            self._nick_tries += 1
            base = self.cfg.nick[: 30 - 3]
            self.nick = f"{base}{'_' * min(self._nick_tries, 2)}{random.randint(0, 9) if self._nick_tries > 2 else ''}"
            await self._raw(f"NICK {self.nick}")
        elif cmd == "NICK" and nick_of(prefix) == self.nick and params:
            self.members.discard(self.nick.lower())
            self.nick = params[-1]
            self.members.add(self.nick.lower())
        elif cmd == "JOIN" and params and params[0].lower() == self.cfg.channel.lower():
            self.members.add(nick_of(prefix).lower())
            if nick_of(prefix) == self.nick:
                self.joined.set()
                logger.info("irc: joined %s", self.cfg.channel)
        elif cmd == "353" and len(params) >= 3 and params[-2].lower() == self.cfg.channel.lower():
            self.members.update(n.lstrip("~&@%+").lower() for n in params[-1].split())
        elif cmd == "PART" and params and params[0].lower() == self.cfg.channel.lower():
            self.members.discard(nick_of(prefix).lower())
        elif cmd == "QUIT":
            self.members.discard(nick_of(prefix).lower())
        elif cmd == "NICK" and params:
            old = nick_of(prefix).lower()
            if old in self.members:
                self.members.discard(old)
                self.members.add(params[-1].lower())
        elif cmd == "KICK" and len(params) >= 2:
            self.members.discard(params[1].lower())
            if params[1] == self.nick:
                self.joined.clear()
                self._kicked = True
                logger.warning("irc: kicked from %s by %s (%s); staying out (no auto-rejoin)",
                               params[0], nick_of(prefix), params[-1] if len(params) > 2 else "")
        elif cmd == "INVITE":
            logger.info("irc: ignoring INVITE from %s (joins only IRC_CHANNEL)", nick_of(prefix))
        elif cmd in ("471", "473", "474", "475", "477"):
            logger.warning("irc: cannot join %s (%s %s); not retrying until reconnect/restart",
                           self.cfg.channel, cmd, params[-1:])
        elif cmd == "ERROR":
            raise ConnectionError(f"server ERROR: {params[-1] if params else ''}")
        elif cmd == "PRIVMSG" and len(params) >= 2:
            self._on_privmsg(nick_of(prefix), params[0], params[1])

    def _spawn(self, coro: Awaitable[None]) -> None:
        t = asyncio.ensure_future(coro)
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    def _on_privmsg(self, sender: str, target: str, text: str) -> None:
        if not sender or sender.lower() == self.nick.lower() or text.startswith("\x01"):
            return  # self, or CTCP (ACTION/VERSION/…)
        text = sanitize(text)
        private = target.lower() == self.nick.lower()
        if private:
            prompt = text
            low = prompt.lower()
            if low == TRIGGER or low.startswith(TRIGGER + " "):
                prompt = prompt[len(TRIGGER):].strip()
            reply_to = sender
        elif target.lower() == self.cfg.channel.lower() and (text.lower() == TRIGGER or text.lower().startswith(TRIGGER + " ")):
            prompt = text[len(TRIGGER):].strip()
            reply_to = target
            if not self.owner_present:
                return  # Libera: an LLM bot must be accompanied by its admin in the channel
        else:
            return
        if prompt.lower() in ("", "help"):
            self.say(reply_to, self._help())
            return
        key = sender.lower()
        now = self.clock()
        if key in self._inflight or now - self._last_ask.get(key, -1e18) < self.cfg.rate_s:
            if now - self._warned.get(key, -1e18) >= self.cfg.rate_s:
                self._warned[key] = now
                wait = max(1, int(self.cfg.rate_s - (now - self._last_ask.get(key, now))))
                self.notice(sender, f"slow down: one !llm question per {self.cfg.rate_s:g}s per nick (try again in ~{wait}s)")
            return
        self._last_ask[key] = now
        self._inflight.add(key)
        self._spawn(self._answer(sender, reply_to, prompt, private))

    def _help(self) -> str:
        return (f"{TRIGGER} <question> asks the local model · {TRIGGER} status · {TRIGGER} reset "
                f"(clears only your history) · PM me for longer answers")

    async def _answer(self, sender: str, reply_to: str, prompt: str, private: bool) -> None:
        session = session_for(sender)
        try:
            async with self._model_lock:  # one model call at a time on a home PC
                lines = await self.llm(prompt, session)
            out = bridge_lines_to_irc(lines, show_thinking=self.cfg.show_thinking)
        except Exception as exc:  # the model path never takes the bot down
            logger.exception("irc: llm call failed for session=%s", session)
            out = [f"[System] llm error: {type(exc).__name__}"]
        finally:
            self._inflight.discard(sender.lower())
        budget = payload_budget(self.nick, reply_to)
        lead = self._tag() + ("" if private else f"{sender}: ")
        pieces: List[str] = []
        for ln in out:
            pieces.extend(split_utf8(sanitize(ln), budget - len(lead.encode("utf-8"))))
        limit = self.cfg.max_lines_pm if private else self.cfg.max_lines
        if len(pieces) > limit:
            pieces = pieces[: limit - 1] + [TRUNCATED_PM if private else TRUNCATED_CHANNEL]
        for p in pieces:
            self._outq.put_nowait(f"PRIVMSG {reply_to} :{lead}{p}")


# ---------------------------------------------------------------- entry point

def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=os.environ.get("IRC_LOG_LEVEL", "INFO").upper(),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        cfg = BotConfig.from_env()
        check_loopback_backends()
    except ConfigError as exc:
        print(f"irc_llm_bot: configuration error: {exc}", file=sys.stderr)
        return 2
    if not cfg.tls:
        logger.warning("irc: IRC_TLS=0 — plaintext connection to %s:%d", cfg.host, cfg.port)
    elif not cfg.tls_verify:
        logger.warning("irc: IRC_TLS_VERIFY=0 — server certificate NOT verified")
    logger.info("irc: %s on %s:%d as %s in %s", "TLS" if cfg.tls else "plaintext",
                cfg.host, cfg.port, cfg.nick, cfg.channel)

    async def _run() -> None:
        bot = IrcLlmBot(cfg)
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            with contextlib.suppress(NotImplementedError, RuntimeError):  # Windows
                loop.add_signal_handler(sig, bot.stop)
        await bot.run_forever()

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
