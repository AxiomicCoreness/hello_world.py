# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Offline tests: backend Argo CI/CD sink, toolkit `argo`, Argo CD deploy standard."""
from __future__ import annotations

import base64
import hashlib
import json
import re
import socket
import threading
import urllib.request
from pathlib import Path

import pytest
import yaml

from pythonIDE import argo_sink
from pythonIDE.toolkit import SovereignToolkit

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "argocd" / "application-argo-cicd-backend.yaml"
BACKEND = ROOT / "argocd" / "argo-cicd-backend"
DIGEST_RE = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")


def _fake_fetch(url, token):
    wf = url.split("/workflows/")[1].split("/")[0]
    return {
        "workflow_runs": [
            {
                "id": 1,
                "name": f"name-{wf}",
                "run_number": 7,
                "event": "push",
                "status": "completed",
                "conclusion": "success",
                "head_branch": "main",
                "head_sha": "0123456789abcdef",
                "created_at": "2026-11-13T00:00:00Z",
                "html_url": "https://example.invalid",
            }
        ]
    }


def test_sink_bind_is_loopback_8024():
    assert argo_sink.BIND == "127.0.0.1:8024"
    assert argo_sink.FILLED is True
    with pytest.raises(argo_sink.SinkError):
        argo_sink.assert_loopback_host("0.0.0.0")
    with pytest.raises(argo_sink.SinkError):
        argo_sink.WSClient("ws://10.0.0.5:6680/cli")


def test_sink_workflows():
    assert set(argo_sink.WORKFLOWS) == {
        "argo-ci.yml",
        "cd-combinator-argo-rollout.yml",
        "sovereign-cicd.yml",
        "ci-cd-stack.yml",
    }
    for wf in argo_sink.WORKFLOWS:
        assert (ROOT / ".github" / "workflows" / wf).is_file(), wf


def test_poll_and_status_lines():
    res = argo_sink.poll_once(fetch=_fake_fetch, token="")
    assert len(res) == 4
    lines = [argo_sink.status_line(r) for r in res]
    assert all(line.startswith("[Argo] ") and "success" in line and "main@01234567" in line for line in lines)


def test_poll_error_is_contained():
    def boom(url, token):
        raise argo_sink.SinkError("offline")

    res = argo_sink.poll_once(fetch=boom, token="")
    assert all(r.get("error") == "offline" for r in res)
    assert argo_sink.summary(fetch=boom)["ok"] is False


def test_toolkit_argo_extension_keeps_54(monkeypatch):
    monkeypatch.setattr(argo_sink, "http_get_json", _fake_fetch)
    tk = SovereignToolkit()
    assert tk.count() == 54
    assert "argo" not in tk.list()
    assert tk.extensions() == ["argo"]
    out = tk.call("argo")
    assert out["ok"] is True and len(out["lines"]) == 4


def _ws_echo_server(received):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def frame(text):
        b = text.encode()
        return bytes([0x81, len(b)]) + b

    def serve():
        conn, _ = srv.accept()
        head = b""
        while b"\r\n\r\n" not in head:
            head += conn.recv(4096)
        key = re.search(rb"Sec-WebSocket-Key: (\S+)", head).group(1)
        acc = base64.b64encode(hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
        conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + acc + b"\r\n\r\n")
        conn.sendall(frame("[System] loopback CLI"))
        while True:
            hdr = conn.recv(2)
            if len(hdr) < 2:
                break
            op, n = hdr[0] & 0x0F, hdr[1] & 0x7F
            if op == 0x8:
                break
            mask = conn.recv(4)
            data = b""
            while len(data) < n:
                data += conn.recv(n - len(data))
            text = bytes(b ^ mask[i % 4] for i, b in enumerate(data)).decode()
            received.append(text)
            conn.sendall(frame(f"[Engine] ack: {text}"))
        conn.close()
        srv.close()

    threading.Thread(target=serve, daemon=True).start()
    return port


def test_push_lines_ws_client():
    got = []
    port = _ws_echo_server(got)
    res = argo_sink.push_lines(["[Argo] a", "[Argo] b"], url=f"ws://127.0.0.1:{port}/cli", probe=False)
    assert res["banner"] == ["[System] loopback CLI"]
    assert [e["replies"] for e in res["exchanges"]] == [["[Engine] ack: [Argo] a"], ["[Engine] ack: [Argo] b"]]
    assert got == ["[Argo] a", "[Argo] b"]


def test_http_server_health_loopback():
    srv = argo_sink.make_server("127.0.0.1", 0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        port = srv.server_address[1]
        assert srv.server_address[0] == "127.0.0.1"
        body = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3).read())
        assert body["ok"] is True and body["bind"] == "127.0.0.1:8024"
    finally:
        srv.shutdown()
        srv.server_close()


def test_application_deploy_standard():
    app = yaml.safe_load(APP.read_text())
    assert app["kind"] == "Application"
    assert app["metadata"]["namespace"] == "argocd"
    assert "resources-finalizer.argocd.argoproj.io" in app["metadata"]["finalizers"]
    spec = app["spec"]
    assert spec["source"]["path"] == "argocd/argo-cicd-backend"
    assert spec["source"]["targetRevision"] == "main"
    auto = spec["syncPolicy"]["automated"]
    assert auto["prune"] is True and auto["selfHeal"] is True
    assert spec["syncPolicy"]["retry"]["limit"] >= 1
    assert "CreateNamespace=true" in spec["syncPolicy"]["syncOptions"]


def _images(doc):
    spec = ((doc.get("spec") or {}).get("template") or {}).get("spec") or {}
    for key in ("initContainers", "containers"):
        for c in spec.get(key) or []:
            yield c["image"]


def test_backend_images_pinned_by_digest():
    imgs = []
    for p in sorted(BACKEND.glob("*.yaml")):
        for d in yaml.safe_load_all(p.read_text()):
            if d:
                imgs.extend(_images(d))
    assert imgs, "no container images under argocd/argo-cicd-backend"
    for img in imgs:
        assert DIGEST_RE.match(img), f"image not pinned by sha256 digest: {img}"
        assert ":latest" not in img


def test_backend_no_push_in_cluster_and_nonroot():
    dep = yaml.safe_load((BACKEND / "deployment.yaml").read_text())
    pod = dep["spec"]["template"]["spec"]
    assert pod["securityContext"]["runAsNonRoot"] is True
    env = {e["name"]: e for e in pod["containers"][0]["env"]}
    assert env["ARGO_SINK_PUSH"]["value"] == "0"
    assert env["GITHUB_TOKEN"]["valueFrom"]["secretKeyRef"]["optional"] is True
