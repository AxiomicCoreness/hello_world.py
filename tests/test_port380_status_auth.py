"""GET /status split on port380_mcp (root and mcp/ copies).

/status stays public but minimal (unauthenticated callers exist:
scripts/cluster_reset.sh, gravastar MAPPED_PORTS check path). The former
diagnostic payload moved to /status/internal behind verify_secret
(hmac.compare_digest; 503 when GARDEN_SECRET unset), same as /pulse.
"""
import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
COPIES = {
    "root": ROOT / "port380_mcp.py",
    "mcp": ROOT / "mcp" / "port380_mcp.py",
}
SECRET = "s3cret-for-tests"
DIAG_KEYS = {"uptime", "seal", "gate_identity", "version", "layer"}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"port380_mcp_status_test_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(params=sorted(COPIES), ids=sorted(COPIES))
def mod(request):
    path = COPIES[request.param]
    if not path.is_file():
        pytest.skip(f"{path} absent")
    return _load(request.param, path)


@pytest.fixture
def client(mod, monkeypatch):
    # verify_secret reads the module-level GARDEN_SECRET captured at import.
    monkeypatch.setattr(mod, "GARDEN_SECRET", SECRET)
    # No `with` block: lifespan (FATAL on empty env secret) is not run.
    return TestClient(mod.app)


def test_status_public_minimal(client):
    r = client.get("/status")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert set(body) == {"status", "service", "timestamp", "ledger_head"}
    assert not (DIAG_KEYS & set(body))


def test_status_public_even_with_secret_unset(mod, monkeypatch):
    monkeypatch.setattr(mod, "GARDEN_SECRET", "")
    r = TestClient(mod.app).get("/status")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_status_internal_no_header_403(client):
    assert client.get("/status/internal").status_code == 403


def test_status_internal_wrong_secret_403(client):
    r = client.get("/status/internal", headers={"X-Garden-Secret": "wrong"})
    assert r.status_code == 403


def test_status_internal_prefix_of_secret_403(client):
    r = client.get("/status/internal", headers={"X-Garden-Secret": SECRET[:-1]})
    assert r.status_code == 403


def test_status_internal_right_secret_200(client):
    r = client.get("/status/internal", headers={"X-Garden-Secret": SECRET})
    assert r.status_code == 200
    body = r.json()
    assert DIAG_KEYS <= set(body)
    assert "ledger_head" in body
    assert isinstance(body["uptime"], (int, float))


@pytest.mark.parametrize("unset", ["", "   "])
def test_status_internal_unset_secret_503(mod, monkeypatch, unset):
    monkeypatch.setattr(mod, "GARDEN_SECRET", unset)
    c = TestClient(mod.app)
    assert c.get("/status/internal").status_code == 503
    assert c.get("/status/internal", headers={"X-Garden-Secret": "x"}).status_code == 503


@pytest.mark.parametrize("path", ["/health", "/healthz"])
def test_health_routes_stay_public(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


@pytest.mark.parametrize("path", ["/health", "/healthz", "/status"])
def test_public_routes_ok_with_secret_unset(mod, monkeypatch, path):
    monkeypatch.setattr(mod, "GARDEN_SECRET", "")
    assert TestClient(mod.app).get(path).status_code == 200


def test_pulse_still_protected(client):
    assert client.post("/pulse", json={}).status_code == 403
    r = client.post("/pulse", json={"pulse_id": "t"}, headers={"X-Garden-Secret": SECRET})
    assert r.status_code == 200


def test_security_headers_on_status_routes(client):
    for path, hdrs in (("/status", {}), ("/status/internal", {"X-Garden-Secret": SECRET})):
        r = client.get(path, headers=hdrs)
        assert "content-security-policy" in {k.lower() for k in r.headers}, path
