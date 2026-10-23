"""CORS hardening for public /health and /healthz on port380_mcp.

Asserts allow-list behavior (never *, never Origin reflection) and that
health responses set CORP cross-origin so allowlisted browser Origins can
read the probe without weakening global SecurityHeadersMiddleware CORP.
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
ALLOWED = "https://sovereign.garden"
DISALLOWED = "https://evil.example"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"port380_cors_test_{name}", path)
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
def client(mod):
    # No lifespan: empty GARDEN_SECRET must not block public health.
    return TestClient(mod.app)


@pytest.mark.parametrize("path", ["/health", "/healthz"])
def test_healthz_allowlisted_origin_gets_acao(client, path):
    r = client.get(path, headers={"Origin": ALLOWED})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == ALLOWED
    assert r.headers.get("access-control-allow-credentials") == "true"
    assert r.headers.get("access-control-allow-origin") != "*"
    assert r.headers.get("cross-origin-resource-policy") == "cross-origin"


@pytest.mark.parametrize("path", ["/health", "/healthz"])
def test_healthz_disallowed_origin_not_reflected(client, path):
    r = client.get(path, headers={"Origin": DISALLOWED})
    assert r.status_code == 200
    acao = r.headers.get("access-control-allow-origin")
    assert acao != DISALLOWED
    assert acao != "*"


@pytest.mark.parametrize("path", ["/health", "/healthz"])
def test_healthz_options_preflight_allowlisted(client, path):
    r = client.options(
        path,
        headers={
            "Origin": ALLOWED,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") == ALLOWED
    assert r.headers.get("access-control-allow-origin") != "*"


@pytest.mark.parametrize("path", ["/health", "/healthz"])
def test_healthz_no_origin_still_public(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    # Platform probes send no Origin; must stay unauthenticated and public.
    assert r.headers.get("cross-origin-resource-policy") == "cross-origin"


def test_non_health_keeps_corp_same_origin(client):
    r = client.get("/status")
    assert r.status_code == 200
    assert r.headers.get("cross-origin-resource-policy") == "same-origin"
