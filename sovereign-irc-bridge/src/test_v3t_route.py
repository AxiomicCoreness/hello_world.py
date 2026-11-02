# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Offline tests for the v3t /llm route: auth, history writes, loopback-only bind, CORS.

Stdlib unittest; run with ``python -I sovereign-irc-bridge/src/test_v3t_route.py``.
No model server: a loopback stub plays llama-server. Every file lives in a temp dir.
"""
from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import device_tokens as dt  # noqa: E402
from src import v3t_route as vr  # noqa: E402

SHA = "717a893e53218604395b07f073c106e79c4356fbc95282f97873bd3d57be6fcf"


class Stub(BaseHTTPRequestHandler):
    seen: list = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Stub.seen.append(body)
        last = body["messages"][-1]["content"]
        if body.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for piece in ("echo:", last):
                d = {"choices": [{"delta": {"content": piece}}]}
                self.wfile.write(b"data: " + json.dumps(d).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            self.close_connection = True
            return
        data = json.dumps({"object": "chat.completion",
                           "choices": [{"message": {"role": "assistant", "content": "echo:" + last}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class V3tRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.tmp.name) / "state" / "h.sqlite3"
        cls.up = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
        threading.Thread(target=cls.up.serve_forever, daemon=True).start()
        cls.store = vr.V3tStore(cls.db)
        cls.token = cls.store.tokens.mint("iphone")
        cls.srv = vr.V3tServer("127.0.0.1", 0, cls.store,
                               upstream=f"http://127.0.0.1:{cls.up.server_port}/v1/chat/completions",
                               model_sha=SHA)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.up.shutdown(); cls.srv.server_close(); cls.up.server_close()
        cls.tmp.cleanup()

    def req(self, method, path, body=None, token=None, origin=None):
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            r.add_header("Content-Type", "application/json")
        if token:
            r.add_header("Authorization", "Bearer " + token)
        if origin:
            r.add_header("Origin", origin)
        try:
            with urllib.request.urlopen(r, timeout=10) as resp:
                return resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    # ---- auth
    def test_auth_rejects_missing_wrong_and_revoked(self):
        for tok in (None, "cyt_wrong", "not-a-token"):
            for m, p, b in (("GET", "/llm/history", None),
                            ("POST", "/llm/v1/chat/completions", {"message": "hi"})):
                code, _, _ = self.req(m, p, b, tok)
                self.assertEqual(code, 401, (tok, p))
        t2 = self.store.tokens.mint("revoked-dev")
        self.assertEqual(self.req("GET", "/llm/history", token=t2)[0], 200)
        self.store.tokens.revoke("revoked-dev")
        self.assertEqual(self.req("GET", "/llm/history", token=t2)[0], 401)

    def test_auth_accepts_and_only_hash_stored(self):
        self.assertEqual(self.req("GET", "/llm/history", token=self.token)[0], 200)
        raw = self.db.read_bytes()
        self.assertNotIn(self.token.encode(), raw)
        self.assertIn(dt.token_hash(self.token).encode(), raw)

    def test_healthz_public_no_secrets(self):
        code, _, body = self.req("GET", "/llm/healthz")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["model_sha256"], SHA)

    # ---- history
    def test_history_written_listed_fetched(self):
        code, h, body = self.req("POST", "/llm/v1/chat/completions",
                                 {"conversation_id": "conv-a", "messages": [{"role": "user", "content": "one"}]},
                                 self.token)
        self.assertEqual(code, 200, body)
        out = json.loads(body)
        self.assertEqual(out["choices"][0]["message"]["content"], "echo:one")
        self.assertTrue(out["history_saved"])
        # second turn gets server-side history prepended
        self.req("POST", "/llm/v1/chat/completions", {"conversation_id": "conv-a", "message": "two"}, self.token)
        self.assertEqual([m["content"] for m in Stub.seen[-1]["messages"]], [vr.DEFAULT_SYSTEM_PROMPT, "one", "echo:one", "two"])
        code, _, body = self.req("GET", "/llm/history/conv-a", token=self.token)
        msgs = json.loads(body)["messages"]
        self.assertEqual([(m["role"], m["content"]) for m in msgs],
                         [("user", "one"), ("assistant", "echo:one"), ("user", "two"), ("assistant", "echo:two")])
        for m in msgs:
            self.assertEqual(m["device"], "iphone")  # token name when no X-Client
            self.assertEqual(m["model_sha256"], SHA)
            self.assertRegex(m["ts"], r"T\d\d:\d\d:\d\d.*\+00:00$")
        convs = json.loads(self.req("GET", "/llm/history", token=self.token)[2])["conversations"]
        self.assertIn("conv-a", [c["conversation_id"] for c in convs])

    def test_stream_saves_history(self):
        r = urllib.request.Request(self.base + "/llm/v1/chat/completions", method="POST",
                                   data=json.dumps({"conversation_id": "conv-s", "message": "s",
                                                    "stream": True}).encode(),
                                   headers={"Authorization": "Bearer " + self.token,
                                            "Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=10) as resp:
            text = resp.read().decode()
        self.assertIn('"history_saved": true', text)
        self.assertTrue(text.rstrip().endswith("data: [DONE]"))
        msgs = json.loads(self.req("GET", "/llm/history/conv-s", token=self.token)[2])["messages"]
        self.assertEqual(msgs[-1]["content"], "echo:s")

    def test_single_owner_token_shared_history(self):
        tok = self.store.tokens.mint("owner")
        for client, text in (("iphone", "from phone"), ("teavm", "from browser")):
            r = urllib.request.Request(self.base + "/llm/v1/chat/completions", method="POST",
                                       data=json.dumps({"conversation_id": "shared", "message": text}).encode(),
                                       headers={"Authorization": "Bearer " + tok, "X-Client": client,
                                                "Content-Type": "application/json"})
            urllib.request.urlopen(r, timeout=10).read()
        msgs = json.loads(self.req("GET", "/llm/history/shared", token=tok)[2])["messages"]
        self.assertEqual([m["device"] for m in msgs], ["iphone", "iphone", "teavm", "teavm"])

    def test_default_identity_system_prompt_injected(self):
        self.req("POST", "/llm/v1/chat/completions", {"message": "What model are you?"}, self.token)
        sent = Stub.seen[-1]["messages"]
        self.assertEqual(sent[0], {"role": "system", "content": vr.DEFAULT_SYSTEM_PROMPT})
        self.assertIn("ClarkeYoursaTee by Clarke Yoursa Tee", vr.DEFAULT_SYSTEM_PROMPT)
        for bad in ("cannot verify", "refuse", "not allowed"):
            self.assertNotIn(bad, vr.DEFAULT_SYSTEM_PROMPT.lower())
        # an explicit system message wins
        self.req("POST", "/llm/v1/chat/completions",
                 {"messages": [{"role": "system", "content": "custom"}, {"role": "user", "content": "x"}]},
                 self.token)
        self.assertEqual(Stub.seen[-1]["messages"][0], {"role": "system", "content": "custom"})

    def test_bad_conversation_id(self):
        code, _, _ = self.req("POST", "/llm/v1/chat/completions",
                              {"conversation_id": "../x", "message": "m"}, self.token)
        self.assertEqual(code, 400)

    def test_db_mode_600(self):
        self.assertEqual(stat.S_IMODE(os.stat(self.db).st_mode), 0o600)

    def test_db_inside_repo_refused(self):
        with self.assertRaises(ValueError):
            vr.V3tStore(vr.REPO_ROOT / "nope.sqlite3")

    # ---- CORS
    def test_cors_pages_origin_only(self):
        _, h, _ = self.req("OPTIONS", "/llm/history", origin=vr.PAGES_ORIGIN)
        self.assertEqual(h.get("Access-Control-Allow-Origin"), vr.PAGES_ORIGIN)
        _, h, _ = self.req("OPTIONS", "/llm/history", origin="https://evil.example")
        self.assertIsNone(h.get("Access-Control-Allow-Origin"))
        _, h, _ = self.req("OPTIONS", "/llm/history", origin="http://127.0.0.1:8092")
        self.assertEqual(h.get("Access-Control-Allow-Origin"), "http://127.0.0.1:8092")

    # ---- binding
    def test_bind_loopback_only(self):
        for host in ("0.0.0.0", "::", "", "192.168.1.5", "example.com"):
            with self.assertRaises(ValueError, msg=host):
                vr.V3tServer(host, 0, self.store, model_sha=SHA)
        self.assertEqual(self.srv.server_address[0], "127.0.0.1")
        with self.assertRaises(ValueError):
            vr.require_loopback_url("http://10.0.0.2:8085/v1/chat/completions")

    def test_mint_cli_writes_600_never_prints(self):
        out = Path(self.tmp.name) / "tok.txt"
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(dt.main(["--db", str(self.db), "mint", "cli-dev", "--out", str(out)]), 0)
        tok = out.read_text().strip()
        self.assertEqual(stat.S_IMODE(os.stat(out).st_mode), 0o600)
        self.assertNotIn(tok, buf.getvalue())
        self.assertEqual(self.store.tokens.verify(tok), "cli-dev")


if __name__ == "__main__":
    unittest.main(verbosity=2)
