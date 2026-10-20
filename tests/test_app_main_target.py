"""`uvicorn app:app_main` must resolve although the app/ package shadows the
repo-root app.py. app/__init__.py re-exports app_main lazily."""
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytest.importorskip("fastapi")
pytest.importorskip("uvicorn")


def test_import_string_resolves():
    from uvicorn.importer import import_from_string
    from fastapi import FastAPI

    target = import_from_string("app:app_main")
    assert isinstance(target, FastAPI)
    assert target.title == "Garden app_main"


def test_health_route_via_testclient():
    from fastapi.testclient import TestClient
    import app

    r = TestClient(app.app_main).get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_package_import_is_lazy():
    # Importing app.config must not execute app.py / garden_surgery.
    code = (
        "import sys, app.config;"
        "assert '_garden_root_app_py' not in sys.modules;"
        "assert not any(m.startswith('garden_surgery') for m in sys.modules);"
        "print('lazy-ok')"
    )
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert "lazy-ok" in out.stdout


def test_unknown_attribute_still_raises():
    import app

    with pytest.raises(AttributeError):
        app.definitely_not_here  # noqa: B018


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_live_uvicorn_serves_health():
    port = _free_port()
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app_main", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        deadline = time.time() + 30
        last = None
        while time.time() < deadline:
            if proc.poll() is not None:
                pytest.fail("uvicorn exited: " + proc.stdout.read())
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
                    assert r.status == 200
                    return
            except OSError as e:
                last = e
                time.sleep(0.3)
        pytest.fail(f"no /health response: {last}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
