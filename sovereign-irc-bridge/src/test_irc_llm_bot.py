# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""IRC bot mode against a fake IRC server on 127.0.0.1 (offline; no real network, no model)."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import List, Optional

import pytest

from src import irc_llm_bot as bot_mod
from src.irc_llm_bot import BotConfig, ConfigError, IrcLlmBot

CHAN = "#axiomiccoreness"


class FakeIrcServer:
    """Minimal IRC server: registers, echoes JOIN, records every line the bot sends."""

    def __init__(self, nick_in_use: int = 0, names: str = "") -> None:
        self.names = names  # extra channel members announced in RPL_NAMREPLY
        self.lines: List[str] = []
        self.raw: List[bytes] = []
        self.conns: List[asyncio.StreamWriter] = []
        self.nick_in_use = nick_in_use
        self.server: Optional[asyncio.base_events.Server] = None
        self.port = 0

    async def start(self) -> "FakeIrcServer":
        self.server = await asyncio.start_server(self._client, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def stop(self) -> None:
        for w in self.conns:
            w.close()
        self.server.close()
        await self.server.wait_closed()

    @property
    def w(self) -> asyncio.StreamWriter:
        return self.conns[-1]

    async def send(self, line: str) -> None:
        self.w.write(line.encode("utf-8") + b"\r\n")
        await self.w.drain()

    async def drop(self) -> None:
        self.w.close()

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.conns.append(writer)
        nick = None
        user_seen = False
        cap_pending = False
        refusals = self.nick_in_use

        def welcome():
            writer.write(f":fake 001 {nick} :Welcome\r\n".encode())
        while True:
            raw = await reader.readline()
            if not raw:
                return
            self.raw.append(raw)
            line = raw.decode("utf-8").rstrip("\r\n")
            self.lines.append(line)
            parts = line.split(" ")
            if parts[0] == "NICK":
                if refusals:
                    refusals -= 1
                    writer.write(f":fake 433 * {parts[1]} :Nickname is already in use\r\n".encode())
                    continue
                nick = parts[1]
                if user_seen and not cap_pending:
                    welcome()
            elif parts[0] == "USER":
                user_seen = True
                if nick and not cap_pending:
                    welcome()
            elif line == "CAP REQ :sasl":
                cap_pending = True
                writer.write(b":fake CAP * ACK :sasl\r\n")
            elif line == "AUTHENTICATE PLAIN":
                writer.write(b"AUTHENTICATE +\r\n")
            elif parts[0] == "AUTHENTICATE":
                writer.write(f":fake 903 {nick or '*'} :SASL authentication successful\r\n".encode())
            elif line == "CAP END":
                cap_pending = False
                if nick and user_seen:
                    welcome()
            elif parts[0] == "JOIN":
                writer.write(f":{nick}!u@h JOIN {parts[1]}\r\n".encode())
                writer.write(f":fake 353 {nick} = {parts[1]} :{nick} {self.names}\r\n".encode())
            with contextlib_suppress():
                await writer.drain()


class contextlib_suppress:  # tiny local helper (ConnectionResetError during drop)
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return exc[0] is not None and issubclass(exc[0], (ConnectionError, OSError))


async def until(pred, timeout: float = 5.0) -> None:
    loop = asyncio.get_running_loop()
    end = loop.time() + timeout
    while not pred():
        if loop.time() > end:
            raise AssertionError("condition not met in time")
        await asyncio.sleep(0.01)


def cfg(port: int, **kw) -> BotConfig:
    base = dict(host="127.0.0.1", port=port, tls=False, send_interval_s=0.0, rate_s=0.0,
                backoff_base_s=0.05, backoff_max_s=0.2, ping_timeout_s=5.0)
    base.update(kw)
    return BotConfig(**base)


class StubLlm:
    def __init__(self, lines=None, exc=None):
        self.calls = []
        self.lines = lines or ["[Engine] llm: φ is the golden ratio."]
        self.exc = exc

    async def __call__(self, prompt, session):
        self.calls.append((prompt, session))
        if self.exc:
            raise self.exc
        return list(self.lines)


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, timeout=30))


async def started(server_kw=None, **cfg_kw):
    srv = await FakeIrcServer(**(server_kw or {})).start()
    llm = cfg_kw.pop("llm", None) or StubLlm()
    b = IrcLlmBot(cfg(srv.port, **cfg_kw), llm=llm)
    task = asyncio.ensure_future(b.run_forever())
    await until(lambda: b.joined.is_set())
    return srv, b, llm, task


async def finish(srv, b, task):
    b.stop()
    await asyncio.wait_for(task, 5)
    await srv.stop()


def privmsgs(srv, target=None):
    out = [l for l in srv.lines if l.startswith("PRIVMSG ")]
    return [l for l in out if target is None or l.split(" ", 2)[1] == target]


# ------------------------------------------------------------------ config

def test_config_defaults_are_abjects_tls_no_owner_no_sasl():
    c = BotConfig.from_env({})  # abjects: IRC_OWNER and SASL are optional
    assert (c.host, c.port, c.tls, c.nick, c.channel) == (
        "irc.abjects.net", 6697, True, "ClarkeTutorBot", "#axiomiccoreness")
    assert c.tls_verify is True and c.llm_tag == "[LLM]" and c.send_interval_s == 2.0
    assert c.rate_s == 15.0 and c.max_lines == 4 and c.max_lines_pm == 25
    assert c.owner == "" and c.require_owner is False and c.sasl_pass == "" and c.sasl_user == ""
    owned = BotConfig.from_env({"IRC_OWNER": "ClarkeYoursaTee"})
    assert owned.owner == "ClarkeYoursaTee" and owned.require_owner is False  # no owner gating on abjects
    opted = BotConfig.from_env({"IRC_OWNER": "ClarkeYoursaTee", "IRC_REQUIRE_OWNER": "1"})
    assert opted.require_owner is True  # still available as an explicit opt-in
    plain = BotConfig.from_env({"IRC_TLS": "0"})  # plaintext only with an explicit IRC_TLS=0
    assert (plain.host, plain.tls, plain.port) == ("irc.abjects.net", False, 6669)
    assert plain.require_owner is False


def test_libera_requires_an_owner_nick_and_gates_on_presence():
    lib = {"IRC_HOST": "irc.libera.chat"}
    with pytest.raises(ConfigError, match="IRC_OWNER"):
        BotConfig.from_env(lib)
    with pytest.raises(ConfigError, match="IRC_OWNER"):
        BotConfig.from_env({**lib, "IRC_OWNER": "ClarkeTutorBot"})
    c = BotConfig.from_env({**lib, "IRC_OWNER": "ClarkeYoursaTee"})
    assert (c.host, c.port, c.tls) == ("irc.libera.chat", 6697, True)
    assert c.require_owner is True and c.owner == "ClarkeYoursaTee"
    assert BotConfig.from_env({"IRC_HOST": "irc.eu.libera.chat", "IRC_OWNER": "me"}).require_owner is True
    with pytest.raises(ConfigError, match="IRC_OWNER"):
        BotConfig.from_env({"IRC_HOST": "irc.libera.chat.", "IRC_TLS": "0"})
    assert BotConfig.from_env({"IRC_HOST": "irc.libera.chat", "IRC_TLS": "0", "IRC_OWNER": "me"}).port == 6667
    # abjects (and other networks): no owner requirement
    assert BotConfig.from_env({"IRC_HOST": "irc.abjects.net"}).owner == ""
    assert BotConfig.from_env({"IRC_HOST": "irc.example.org"}).owner == ""
    assert bot_mod.is_libera("irc.libera.chat") and not bot_mod.is_libera("notlibera.chat")
    assert bot_mod.is_abjects("irc.us.abjects.net") and not bot_mod.is_abjects("irc.libera.chat")


def test_sasl_user_defaults_to_nick_and_is_secret():
    c = BotConfig.from_env({"IRC_OWNER": "me", "IRC_SASL_PASS": "pw-xyz"})
    assert c.sasl_user == "ClarkeTutorBot" and "pw-xyz" not in repr(c)


@pytest.mark.parametrize("env, msg", [
    ({"IRC_PORT": "6667"}, "IRC_TLS=0"),
    ({"IRC_PORT": "6669"}, "IRC_TLS=0"),  # abjects plaintext port needs an explicit IRC_TLS=0
    ({"IRC_TLS": "maybe"}, "IRC_TLS"),
    ({"IRC_PORT": "abc"}, "IRC_PORT"),
    ({"IRC_NICK": "bad nick"}, "IRC_NICK"),
    ({"IRC_CHANNEL": "nochan"}, "IRC_CHANNEL"),
    ({"IRC_NICKSERV_PASS": "x\r\nQUIT"}, "line break"),
    ({"IRC_MAX_LINES": "0"}, "IRC_MAX_LINES"),
])
def test_config_errors(env, msg):
    with pytest.raises(ConfigError, match=msg):
        BotConfig.from_env({"IRC_OWNER": "ClarkeYoursaTee", **env})


def test_nickserv_pass_not_in_repr():
    c = BotConfig.from_env({"IRC_OWNER": "me", "IRC_NICKSERV_PASS": "hunter2"})
    assert c.nickserv_pass == "hunter2" and "hunter2" not in repr(c)


def test_main_bad_config_returns_2_without_raising(monkeypatch, capsys):
    monkeypatch.setenv("IRC_PORT", "6667")
    monkeypatch.delenv("IRC_TLS", raising=False)
    assert bot_mod.main([]) == 2
    assert "configuration error" in capsys.readouterr().err


def test_main_rejects_non_loopback_model(monkeypatch, capsys):
    monkeypatch.setenv("IRC_OWNER", "ClarkeYoursaTee")
    monkeypatch.setenv("LLM_CLARKEYOURSATEE_URL", "http://10.0.0.5:8085/v1/chat/completions")
    assert bot_mod.main([]) == 2
    assert "LLM_CLARKEYOURSATEE_URL" in capsys.readouterr().err


def test_no_process_exit_in_run_loop():
    src = Path(bot_mod.__file__).read_text(encoding="utf-8")
    assert "sys.exit" not in src and "os._exit" not in src
    # The only SystemExit is the __main__ guard returning main()'s code.
    assert src.count("SystemExit") == 1 and "raise SystemExit(main())" in src


# ------------------------------------------------------------------ wire helpers

def test_session_for_matches_bridge_rule():
    from src import llm_chat

    for nick in ("Alice", "[m]ike|away", "x" * 40, "ñandú", "a^b`c{d}"):
        s = bot_mod.session_for(nick)
        assert re.fullmatch(r"[A-Za-z0-9_-]{1,64}", s) and s.startswith("irc-")
        assert llm_chat.normalize_session(s) == s
    assert bot_mod.session_for("Alice") == bot_mod.session_for("alice")


def test_split_utf8_never_breaks_characters():
    text = ("φ golden ratio ∀∞ 🙂 " * 80).strip()
    for limit in (17, 50, 200, 400):
        parts = bot_mod.split_utf8(text, limit)
        assert all(len(p.encode("utf-8")) <= limit for p in parts)
        assert " ".join(parts).split() == text.split()
    long_word = "φ" * 300  # no spaces: hard cut on a character boundary
    parts = bot_mod.split_utf8(long_word, 51)
    assert "".join(parts) == long_word and all(len(p.encode()) <= 51 for p in parts)


def test_sanitize_strips_crlf_nul_ctcp():
    s = bot_mod.sanitize("hi\r\nQUIT :x\n\x00JOIN #evil\x01ACTION\x01")
    assert "\r" not in s and "\n" not in s and "\x00" not in s and "\x01" not in s
    assert s.startswith("hi QUIT :x")


def test_parse_line():
    assert bot_mod.parse_line(":a!u@h PRIVMSG #c :!llm hi there") == ("a!u@h", "PRIVMSG", ["#c", "!llm hi there"])
    assert bot_mod.parse_line("PING :xyz") == ("", "PING", ["xyz"])


def test_bridge_lines_to_irc_hides_thinking_and_routing():
    lines = [
        "[System] llm session: irc-alice",
        "[System] llm ctx: plain (no neuron snapshot / traceback; spike prompt off)",
        "[System] llm order: deepinfer offline → clarkeyoursatee",
        "[Engine] llm: [ClarkeYoursaTee (deepseek-r2-1.5b)] [thinking]",
        "[Engine] llm: [ClarkeYoursaTee (deepseek-r2-1.5b)] step one",
        "[Engine] llm: [ClarkeYoursaTee (deepseek-r2-1.5b)] step two",
        "[Engine] llm: [ClarkeYoursaTee (deepseek-r2-1.5b)] [/thinking]",
        "[Engine] llm: [ClarkeYoursaTee (deepseek-r2-1.5b)] Answer line 1",
        "[Engine] llm: [ClarkeYoursaTee (deepseek-r2-1.5b)] Answer line 2",
        "[System] llm route: backend=clarkeyoursatee",
    ]
    out = bot_mod.bridge_lines_to_irc(lines, show_thinking=False)
    assert out == [
        "[System] llm order: deepinfer offline → clarkeyoursatee",
        "[ClarkeYoursaTee (deepseek-r2-1.5b)] (thinking: 2 line(s) hidden; IRC_SHOW_THINKING=1 shows them)",
        "Answer line 1",
        "Answer line 2",
    ]
    full = bot_mod.bridge_lines_to_irc(lines, show_thinking=True)
    assert "step one" in full and "[/thinking]" in full


def test_backoff_doubles_and_caps():
    delays = [bot_mod.backoff_delay(a, 1.0, 300.0, jitter=0.0) for a in range(12)]
    assert delays[:5] == [1, 2, 4, 8, 16] and max(delays) == 300 and delays[-1] == 300
    assert bot_mod.backoff_delay(100, 1.0, 300.0) <= 300


# ------------------------------------------------------------------ fake IRC server

def test_registration_join_and_ping_pong():
    async def go():
        srv, b, _, task = await started()
        assert srv.lines[0] == "NICK ClarkeTutorBot"
        assert srv.lines[1].startswith("USER ")
        assert f"JOIN {CHAN}" in srv.lines
        await srv.send("PING :fake.server.42")
        await until(lambda: "PONG :fake.server.42" in srv.lines)
        await finish(srv, b, task)
        assert any(l.startswith("QUIT") for l in srv.lines)
    run(go())


def test_nick_in_use_retries_with_new_nick():
    async def go():
        srv, b, _, task = await started(server_kw={"nick_in_use": 1})
        nicks = [l for l in srv.lines if l.startswith("NICK ")]
        assert nicks[0] == "NICK ClarkeTutorBot" and nicks[1] == "NICK ClarkeTutorBot_"
        assert b.nick == "ClarkeTutorBot_"
        await finish(srv, b, task)
    run(go())


def test_nickserv_identify_sent_but_never_logged(caplog):
    async def go():
        caplog.set_level(logging.DEBUG, logger="sovereign-irc-bridge.irc-bot")
        srv, b, _, task = await started(nickserv_pass="s3cr3t-pw")
        assert "PRIVMSG NickServ :IDENTIFY s3cr3t-pw" in srv.lines
        await finish(srv, b, task)
    run(go())
    assert "s3cr3t-pw" not in caplog.text
    assert "IDENTIFY" in caplog.text  # the event is logged, the password is not


def test_channel_trigger_routes_to_llm_with_per_nick_session():
    async def go():
        srv, b, llm, task = await started()
        await srv.send(f":alice!a@h PRIVMSG {CHAN} :hello everyone")
        await srv.send(f":alice!a@h PRIVMSG {CHAN} :!llmx not me")
        await srv.send(f":alice!a@h PRIVMSG {CHAN} :!llm what is phi?")
        await until(lambda: privmsgs(srv, CHAN))
        assert llm.calls == [("what is phi?", "irc-alice")]
        assert privmsgs(srv, CHAN) == [f"PRIVMSG {CHAN} :[LLM] alice: φ is the golden ratio."]
        await srv.send(f":Bob!b@h PRIVMSG {CHAN} :!llm status")
        await until(lambda: len(privmsgs(srv, CHAN)) == 2)
        await srv.send(f":Bob!b@h PRIVMSG {CHAN} :!LLM reset")
        await until(lambda: len(llm.calls) == 3)
        assert llm.calls[1:] == [("status", "irc-bob"), ("reset", "irc-bob")]
        await finish(srv, b, task)
    run(go())


def test_private_message_is_a_prompt_and_reply_goes_to_sender():
    async def go():
        srv, b, llm, task = await started()
        await srv.send(":carol!c@h PRIVMSG ClarkeTutorBot :explain RK4")
        await srv.send(":carol!c@h PRIVMSG ClarkeTutorBot :\x01VERSION\x01")  # CTCP ignored
        await until(lambda: privmsgs(srv, "carol"))
        assert llm.calls == [("explain RK4", "irc-carol")]
        assert privmsgs(srv, "carol") == ["PRIVMSG carol :[LLM] φ is the golden ratio."]
        await finish(srv, b, task)
    run(go())


def test_long_reply_split_under_512_bytes_and_truncated_in_channel():
    long = "[Engine] llm: " + " ".join(["φ∀∞🙂 golden"] * 400)
    async def go():
        srv, b, llm, task = await started(llm=StubLlm(lines=[long]), max_lines=4, max_lines_pm=6)
        await srv.send(f":dave!d@h PRIVMSG {CHAN} :!llm long please")
        await until(lambda: len(privmsgs(srv, CHAN)) == 4)
        await asyncio.sleep(0.1)
        msgs = privmsgs(srv, CHAN)
        assert len(msgs) == 4 and msgs[-1].endswith("…(truncated, ask in PM for more)")
        assert all(m.startswith(f"PRIVMSG {CHAN} :[LLM] dave: ") for m in msgs)
        relay = len(":ClarkeTutorBot!clarketuto@" .encode()) + 63 + 1
        for raw in [r for r in srv.raw if r.startswith(b"PRIVMSG")]:
            raw.decode("utf-8")  # whole characters only
            assert len(raw) + relay <= 512
        await srv.send(":dave!d@h PRIVMSG ClarkeTutorBot :long please")
        await until(lambda: len(privmsgs(srv, "dave")) == b.cfg.max_lines_pm)
        assert privmsgs(srv, "dave")[-1].endswith("…(truncated)")
        await finish(srv, b, task)
    run(go())


def test_crlf_in_model_reply_cannot_inject_commands():
    evil = StubLlm(lines=["[Engine] llm: hi\r\nQUIT :pwned\nJOIN #evil", "[Engine] llm: ok\x00MODE x"])
    async def go():
        srv, b, llm, task = await started(llm=evil)
        await srv.send(f":eve!e@h PRIVMSG {CHAN} :!llm hi\rPRIVMSG NickServ :DROP")
        await until(lambda: len(privmsgs(srv, CHAN)) >= 2)
        await asyncio.sleep(0.1)
        assert not any(l.startswith(("QUIT", "JOIN #evil", "MODE")) for l in srv.lines)
        assert all(l.startswith("PRIVMSG") or l.startswith(("NICK", "USER", "JOIN #axiom")) for l in srv.lines)
        assert evil.calls[0][0] == "hi PRIVMSG NickServ :DROP"
        assert all(b"\r" not in r[:-2] and b"\x00" not in r for r in srv.raw)
        await finish(srv, b, task)
    run(go())


def test_per_nick_rate_limit():
    async def go():
        srv, b, llm, task = await started(rate_s=60.0)
        clock = [1000.0]
        b.clock = lambda: clock[0]
        await srv.send(f":fred!f@h PRIVMSG {CHAN} :!llm one")
        await until(lambda: len(llm.calls) == 1)
        await srv.send(f":fred!f@h PRIVMSG {CHAN} :!llm two")
        await srv.send(f":fred!f@h PRIVMSG {CHAN} :!llm three")
        await srv.send(f":gina!g@h PRIVMSG {CHAN} :!llm other nick is fine")
        await until(lambda: len(llm.calls) == 2)
        await until(lambda: any(l.startswith("NOTICE fred :[LLM] slow down") for l in srv.lines))
        await asyncio.sleep(0.1)
        assert [c[0] for c in llm.calls] == ["one", "other nick is fine"]
        assert sum(l.startswith("NOTICE fred") for l in srv.lines) == 1  # warned once, not per message
        clock[0] += 61
        await srv.send(f":fred!f@h PRIVMSG {CHAN} :!llm later")
        await until(lambda: len(llm.calls) == 3)
        await finish(srv, b, task)
    run(go())


def test_llm_error_does_not_kill_the_bot():
    async def go():
        srv, b, llm, task = await started(llm=StubLlm(exc=RuntimeError("boom")))
        await srv.send(f":hank!h@h PRIVMSG {CHAN} :!llm crash?")
        await until(lambda: privmsgs(srv, CHAN))
        assert "llm error: RuntimeError" in privmsgs(srv, CHAN)[0]
        await srv.send("PING :still-alive")
        await until(lambda: "PONG :still-alive" in srv.lines)
        assert not task.done()
        await finish(srv, b, task)
    run(go())


def test_reconnects_after_server_drop_and_error():
    async def go():
        srv, b, llm, task = await started()
        assert b.connections == 1
        await srv.drop()
        await until(lambda: b.connections == 2 and b.joined.is_set())
        await srv.send(":fake ERROR :Closing Link (K-lined)")
        await until(lambda: b.connections == 3 and b.joined.is_set())
        assert srv.lines.count(f"JOIN {CHAN}") == 3
        await srv.send(f":ivy!i@h PRIVMSG {CHAN} :!llm back?")
        await until(lambda: privmsgs(srv, CHAN))
        assert not task.done()
        await finish(srv, b, task)
    run(go())


def test_reconnects_when_server_is_down_at_start():
    async def go():
        srv = await FakeIrcServer().start()
        port = srv.port
        await srv.stop()  # nothing listening: connection refused, keep retrying
        b = IrcLlmBot(cfg(port), llm=StubLlm())
        task = asyncio.ensure_future(b.run_forever())
        await asyncio.sleep(0.5)
        assert not task.done() and b.connections == 0
        srv2 = FakeIrcServer()
        srv2.server = await asyncio.start_server(srv2._client, "127.0.0.1", port)
        srv2.port = port
        await until(lambda: b.joined.is_set())
        await finish(srv2, b, task)
    run(go())


def test_ping_timeout_triggers_client_ping_then_reconnect():
    async def go():
        srv, b, llm, task = await started(ping_timeout_s=0.2)
        await until(lambda: any(l.startswith("PING ") for l in srv.lines))
        # The fake server never answers our PING → second timeout → reconnect.
        await until(lambda: b.connections >= 2)
        await finish(srv, b, task)
    run(go())


# ------------------------------------------------------------------ through the real /llm path

class _Llama(BaseHTTPRequestHandler):
    bodies: list = []

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).bodies.append(body)
        out = json.dumps({"choices": [{"message": {"role": "assistant", "content": "Stub tutor says hi."}}]})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out.encode())

    def do_GET(self):  # noqa: N802
        props = {"chat_template": "{% for m in messages %}<|im_start|>{{ m.role }}\n{{ m.content }}<|im_end|>\n{% endfor %}"}
        self.send_response(200 if self.path == "/props" else 404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if self.path == "/props":
            self.wfile.write(json.dumps(props).encode())

    def log_message(self, *a):
        pass


def test_bang_llm_goes_through_bridge_llm_chat_with_history(monkeypatch, tmp_path):
    from src import llm_backend

    _Llama.bodies = []
    http = HTTPServer(("127.0.0.1", 0), _Llama)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    hist = tmp_path / "llm_history.jsonl"
    for k in ("LLM_FALLBACK", "DEEPINFER_URL", "LLM_SYSTEM_PROMPT"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("LLM_BACKEND", "gguf")
    monkeypatch.setenv("LLM_URL", f"http://127.0.0.1:{http.server_port}/v1/chat/completions")
    monkeypatch.setenv("LLM_MODEL", "stub-gguf")
    monkeypatch.setenv("LLM_BUILD_FEEDBACK", "0")
    monkeypatch.setenv("LLM_RAW_REPLY", "1")
    monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
    llm_backend.reset_state()

    async def go():
        srv = await FakeIrcServer().start()
        b = IrcLlmBot(cfg(srv.port))  # default handler = src.llm_chat.handle_llm
        task = asyncio.ensure_future(b.run_forever())
        await until(lambda: b.joined.is_set())
        await srv.send(f":Alice!a@h PRIVMSG {CHAN} :!llm first question")
        await until(lambda: privmsgs(srv, CHAN))
        assert privmsgs(srv, CHAN) == [f"PRIVMSG {CHAN} :[LLM] Alice: Stub tutor says hi."]
        await srv.send(f":Alice!a@h PRIVMSG {CHAN} :!llm second question")
        await until(lambda: len(privmsgs(srv, CHAN)) == 2)
        await srv.send(f":Alice!a@h PRIVMSG {CHAN} :!llm reset")
        await until(lambda: len(privmsgs(srv, CHAN)) == 3)
        assert "session=irc-alice history archived" in privmsgs(srv, CHAN)[2]
        await finish(srv, b, task)

    try:
        run(go())
    finally:
        http.shutdown()
        http.server_close()
        llm_backend.reset_state()
    # The second call carried the first turn as history (same per-nick session).
    second = _Llama.bodies[1]["messages"]
    assert any(m["role"] == "user" and m["content"].endswith("first question") for m in second[:-1])
    assert any(m["role"] == "assistant" and m["content"] == "Stub tutor says hi." for m in second)
    archived = list(tmp_path.glob("llm_history.jsonl.reset-irc-alice-*"))
    assert len(archived) == 1
    rows = [json.loads(l) for l in archived[0].read_text().splitlines()]
    assert {r["session"] for r in rows} == {"irc-alice"} and len(rows) == 4


# ------------------------------------------------------------------ etiquette (all networks; owner gating Libera-only)

def test_realname_labels_bot_and_admin():
    async def go():
        srv, b, _, task = await started(owner="ClarkeYoursaTee", server_kw={"names": "ClarkeYoursaTee"})
        user = next(l for l in srv.lines if l.startswith("USER "))
        assert "LLM bot" in user and "admin: ClarkeYoursaTee" in user
        await finish(srv, b, task)
    run(go())


def test_sasl_plain_login_before_registration(caplog):
    import base64

    async def go():
        caplog.set_level(logging.DEBUG, logger="sovereign-irc-bridge.irc-bot")
        srv, b, _, task = await started(sasl_user="ClarkeTutorBot", sasl_pass="sasl-pw-1")
        assert srv.lines[0] == "CAP REQ :sasl"
        auth = [l for l in srv.lines if l.startswith("AUTHENTICATE ") and l != "AUTHENTICATE PLAIN"]
        assert base64.b64decode(auth[0].split(" ", 1)[1]) == b"ClarkeTutorBot\0ClarkeTutorBot\0sasl-pw-1"
        assert "CAP END" in srv.lines
        assert not any("IDENTIFY" in l for l in srv.lines)  # SASL replaces NickServ IDENTIFY
        await finish(srv, b, task)
    run(go())
    assert "sasl-pw-1" not in caplog.text
    assert base64.b64encode(b"ClarkeTutorBot\0ClarkeTutorBot\0sasl-pw-1").decode() not in caplog.text


def test_answers_in_channel_only_while_owner_present():
    async def go():
        srv, b, llm, task = await started(owner="Owner", require_owner=True, server_kw={"names": "@Owner +someone"})
        assert b.owner_present
        await srv.send(f":alice!a@h PRIVMSG {CHAN} :!llm one")
        await until(lambda: len(llm.calls) == 1)
        await srv.send(f":Owner!o@h PART {CHAN} :brb")
        await until(lambda: not b.owner_present)
        await srv.send(f":alice!a@h PRIVMSG {CHAN} :!llm two")
        await srv.send(":alice!a@h PRIVMSG ClarkeTutorBot :pm still works")
        await until(lambda: len(llm.calls) == 2)
        await asyncio.sleep(0.1)
        assert [c[0] for c in llm.calls] == ["one", "pm still works"]
        await srv.send(f":Owner!o@h JOIN {CHAN}")
        await until(lambda: b.owner_present)
        await srv.send(f":Owner!o@h NICK Owner_away")
        await until(lambda: not b.owner_present)
        await finish(srv, b, task)
    run(go())


def test_abjects_env_answers_without_owner_or_sasl():
    """abjects defaults (from_env): owner absent and no SASL; still answers, still [LLM]-tagged."""
    async def go():
        env_cfg = BotConfig.from_env({"IRC_OWNER": "Owner"})
        assert env_cfg.host == "irc.abjects.net" and env_cfg.require_owner is False
        srv, b, llm, task = await started(owner="Owner", require_owner=env_cfg.require_owner,
                                          server_kw={"names": "+someone"})
        assert not any(l.startswith("CAP REQ") for l in srv.lines)  # no SASL without IRC_SASL_PASS
        assert b.owner_present  # nothing to require on abjects
        await srv.send(f":alice!a@h PRIVMSG {CHAN} :!llm hello")
        await until(lambda: len(llm.calls) == 1)
        await until(lambda: privmsgs(srv, CHAN))
        assert all(l.split(" :", 1)[1].startswith("[LLM] ") for l in privmsgs(srv, CHAN))
        await finish(srv, b, task)
    run(go())


def test_kick_means_no_rejoin_and_invite_is_ignored():
    async def go():
        srv, b, llm, task = await started()
        await srv.send(f":fake INVITE ClarkeTutorBot #elsewhere")
        await srv.send(f":op!o@h KICK {CHAN} ClarkeTutorBot :no bots")
        await until(lambda: not b.joined.is_set())
        await srv.drop()  # even after a reconnect it stays out of the channel
        await until(lambda: b.connections == 2 and b.registered.is_set())
        await asyncio.sleep(0.2)
        joins = [l for l in srv.lines if l.startswith("JOIN")]
        assert joins == [f"JOIN {CHAN}"]
        b.stop()
        await asyncio.wait_for(task, 5)
        await srv.stop()
    run(go())
