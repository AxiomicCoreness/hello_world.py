"""Pentad rank {-2,-1,0,1,2} for the Port-380 FAL gate.

-1/0/+1 must behave exactly as before (snapshot taken from main 7b51afd).
+2/-2 are strong pass / strong invert (2x the +1/-1 scaling) and are only
reachable by explicit override (CLI, HTTP body, function argument). CDP/OAuth
derivation still yields only -1/0/+1.

The gate module is loaded by file path because the quantum.radar_lindblad
package __init__ imports modules that are not in the repo.
"""
import importlib.util
import itertools
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "quantum" / "radar_lindblad" / "port_380_gate.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_gate():
    spec = importlib.util.spec_from_file_location("port_380_gate_pentad_test", GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load_gate()

PENTAD = (-2, -1, 0, 1, 2)
H = 0.7337473231
HARMONIES = (H, -0.5, 0.0, 1.0, 3.25)
BAD = (3, -3, 1.5, "x", None)

# Snapshot of main 7b51afd behaviour for the ternary subset.
SNAPSHOT_MODES = {1: "identity", 0: "nullify", -1: "invert"}
SNAPSHOT_CLI = {
    -1: "Port 380 Ternary Gate: -1 → -0.7337473231\n",
    0: "Port 380 Ternary Gate: 0 → 0.0000000000\n",
    1: "Port 380 Ternary Gate: 1 → 0.7337473231\n",
}
SNAPSHOT_EVAL_KEYS = {
    "harmony_in", "ternary", "harmony_out", "phi", "layer", "fal", "mode",
    "websocket_ready", "oauth_validated",
}
SNAPSHOT_DERIVE = {
    (False, False, None): 0, (False, False, "gpt"): -1,
    (False, True, None): 0, (False, True, "gpt"): -1,
    (True, False, None): 0, (True, False, "gpt"): -1,
    (True, True, None): 1, (True, True, "gpt"): -1,
}


def _snapshot_scale(h, t):
    return {1: float(h), 0: 0.0, -1: -float(h)}[t]


# ─── 1. ternary subset unchanged ─────────────────────────────────────

@pytest.mark.parametrize("h", HARMONIES)
@pytest.mark.parametrize("t", (-1, 0, 1))
def test_ternary_outputs_unchanged(h, t):
    want = _snapshot_scale(h, t)
    assert gate.apply_ternary_scaling(h, t) == want
    assert gate.apply_pentad_scaling(h, t) == want
    ev = gate.evaluate_gate(h, ternary=t)
    assert SNAPSHOT_EVAL_KEYS <= set(ev)
    assert ev["harmony_out"] == want
    assert ev["ternary"] == t
    assert ev["mode"] == SNAPSHOT_MODES[t]
    assert ev["fal"] == "ternary_scaling"
    assert ev["layer"] == 314
    assert ev["websocket_ready"] is None and ev["oauth_validated"] is False


def test_ternary_alias_is_strict_subset():
    assert set(gate.TERNARY_VALUES) == {-1, 0, 1}
    assert set(gate.TERNARY_VALUES) < set(gate.PENTAD_VALUES)
    for r in (2, -2):
        with pytest.raises(ValueError):
            gate.apply_ternary_scaling(H, r)


# ─── 2. ±2 behaviour ─────────────────────────────────────────────────

@pytest.mark.parametrize("h", HARMONIES)
def test_strong_pass_and_invert(h):
    assert gate.apply_pentad_scaling(h, 2) == 2.0 * gate.apply_pentad_scaling(h, 1)
    assert gate.apply_pentad_scaling(h, -2) == 2.0 * gate.apply_pentad_scaling(h, -1)
    assert gate.evaluate_gate(h, ternary=2)["mode"] == "strong_identity"
    assert gate.evaluate_gate(h, ternary=-2)["mode"] == "strong_invert"
    assert gate.evaluate_gate(h, ternary=2)["ternary"] == 2


def test_pentad_constants():
    assert tuple(gate.PENTAD_VALUES) == PENTAD
    assert gate.PENTAD_MODES == {
        -2: "strong_invert", -1: "invert", 0: "nullify",
        1: "identity", 2: "strong_identity",
    }


def test_override_accepts_pentad():
    for r in PENTAD:
        assert gate.ternary_from_cdp(websocket_ready=False, override=r) == r


# ─── 3. rejection ────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", BAD)
def test_rejects_out_of_set(bad):
    with pytest.raises(ValueError):
        gate.apply_pentad_scaling(H, bad)
    with pytest.raises(ValueError):
        gate.evaluate_gate(H, ternary=bad)
    if bad is not None:
        with pytest.raises(ValueError):
            gate.ternary_from_cdp(websocket_ready=True, override=bad)


# ─── 4. CLI ──────────────────────────────────────────────────────────

def _cli(*args):
    return subprocess.run(
        [sys.executable, str(GATE_PATH), *args],
        capture_output=True, text=True, cwd=str(ROOT), timeout=60,
    )


@pytest.mark.parametrize("t", (-1, 0, 1))
def test_cli_ternary_output_unchanged(t):
    r = _cli("--ternary", str(t))
    assert r.returncode == 0, r.stderr
    assert r.stdout == SNAPSHOT_CLI[t]


@pytest.mark.parametrize("flag", ("--ternary", "--pentad"))
def test_cli_accepts_pm2(flag):
    r = _cli(flag, "2")
    assert r.returncode == 0, r.stderr
    assert r.stdout == f"Port 380 Ternary Gate: 2 → {2 * H:.10f}\n"
    r = _cli(flag, "-2")
    assert r.returncode == 0, r.stderr
    assert r.stdout == f"Port 380 Ternary Gate: -2 → {-2 * H:.10f}\n"


@pytest.mark.parametrize("bad", ("3", "-3", "1.5", "x"))
def test_cli_rejects_bad(bad):
    r = _cli("--ternary", bad)
    assert r.returncode == 2
    assert "invalid" in r.stderr


# ─── 5. derivation never yields ±2 ───────────────────────────────────

@pytest.mark.parametrize("ws,oa,fm", list(itertools.product((True, False), (True, False), (None, "gpt", ""))))
def test_derivation_is_ternary(ws, oa, fm):
    r = gate.ternary_from_cdp(websocket_ready=ws, oauth_validated=oa, foreign_model_trace=fm)
    assert r in (-1, 0, 1)
    key = (ws, oa, fm if fm else None)
    assert r == SNAPSHOT_DERIVE[key]
    ev = gate.evaluate_gate(H, ternary=2, websocket_ready=ws, oauth_validated=oa, foreign_model_trace=fm)
    assert ev["ternary"] in (-1, 0, 1)


def test_cdp_schema_derivation_is_ternary():
    from quantum.cdp_convergence import cdp_schema as cs
    for ws, oa, fm in itertools.product((True, False), (True, False), (None, "gpt")):
        d = cs.CdpStatus(websocket_ready=ws, oauth_validated=oa, foreign_model_trace=fm).to_dict()
        assert d["fal_ternary"] == SNAPSHOT_DERIVE[(ws, oa, fm)]
        assert d["harmony_out"] == _snapshot_scale(cs.DEFAULT_HARMONY, d["fal_ternary"])
        assert d["fal_mode"] == SNAPSHOT_MODES[d["fal_ternary"]]


# ─── 6. HTTP endpoint ────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from quantum.deepseek_mesh import endpoint
    return TestClient(endpoint.app)


@pytest.mark.parametrize("t", (-1, 0, 1))
def test_endpoint_ternary_unchanged(client, t):
    r = client.post("/gate", json={"ternary": t})
    assert r.status_code == 200
    j = r.json()
    assert j["harmony_index"] == _snapshot_scale(H, t)
    assert j["ternary"] == t
    assert j["fal_mode"] == SNAPSHOT_MODES[t]
    assert j["mode"] == "fal_ternary"


def test_endpoint_default_and_websocket_bodies_unchanged(client):
    # Snapshot: the endpoint's local gate ignores CDP fields and uses +1.
    for body in ({}, {"websocket_ready": False}, {"websocket_ready": True, "oauth_validated": True}):
        j = client.post("/gate", json=body).json()
        assert j["ternary"] == 1 and j["harmony_index"] == H and j["fal_mode"] == "identity"
    j = client.post("/gate", json={"ternary": 1, "override": True}).json()
    assert j["harmony_index"] == 1.2880567176564381


@pytest.mark.parametrize("r,mode", ((2, "strong_identity"), (-2, "strong_invert")))
def test_endpoint_accepts_pm2(client, r, mode):
    resp = client.post("/gate", json={"ternary": r})
    assert resp.status_code == 200
    j = resp.json()
    assert j["ternary"] == r
    assert j["harmony_index"] == r * H
    assert j["fal_mode"] == mode


@pytest.mark.parametrize("bad", (3, -3, 5, -100))
def test_endpoint_400_out_of_range(client, bad):
    resp = client.post("/gate", json={"ternary": bad})
    assert resp.status_code == 400
    assert "-2, -1, 0, 1, 2" in resp.json()["detail"]


@pytest.mark.parametrize("bad", (1.5, "x"))
def test_endpoint_422_non_integer(client, bad):
    assert client.post("/gate", json={"ternary": bad}).status_code == 422


def test_endpoint_status_lists_allowed(client):
    for path in ("/status", "/380", "/"):
        j = client.get(path).json()
        assert j["fal_allowed"] == list(PENTAD), path


# ─── 7. cross-layer consistency ──────────────────────────────────────

def _accepted_by_gate():
    out = set()
    for v in range(-6, 7):
        try:
            gate.apply_pentad_scaling(H, v)
            out.add(v)
        except ValueError:
            pass
    return out


def test_cross_layer_same_set_and_modes(client):
    from quantum.deepseek_mesh import endpoint
    from quantum.cdp_convergence import cdp_schema as cs
    gate_set = _accepted_by_gate()
    assert gate_set == set(PENTAD)
    assert set(endpoint.PENTAD_VALUES) == gate_set
    assert set(cs.PENTAD_VALUES) == gate_set
    assert endpoint.PENTAD_MODES == gate.PENTAD_MODES == cs.PENTAD_MODES
    http_set = {v for v in range(-6, 7)
                if client.post("/gate", json={"ternary": v}).status_code == 200}
    assert http_set == gate_set
    # Whichever implementation the endpoint is using (gate module or its local
    # fallback), it scales exactly like the gate.
    for v in PENTAD:
        for h in HARMONIES:
            assert endpoint.evaluate_gate(h, ternary=v)["harmony_out"] == gate.apply_pentad_scaling(h, v)
            assert endpoint.evaluate_gate(h, ternary=v)["mode"] == gate.PENTAD_MODES[v]


def test_endpoint_fallback_matches_gate():
    """The endpoint's local fallback copy must accept and scale the same set."""
    pytest.importorskip("fastapi")
    from quantum.deepseek_mesh import endpoint
    fb = endpoint._fallback_apply_pentad_scaling
    for v in range(-6, 7):
        for h in HARMONIES:
            try:
                want = gate.apply_pentad_scaling(h, v)
            except ValueError:
                with pytest.raises(ValueError):
                    fb(h, v)
            else:
                assert fb(h, v) == want
    for bad in BAD:
        with pytest.raises(ValueError):
            fb(H, bad)
