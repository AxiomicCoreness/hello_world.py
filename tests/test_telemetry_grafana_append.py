# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Clarke Yoursa Tee (AxiomicCoreness)
# Zenodo DOI: 10.5281/zenodo.23378305 (https://doi.org/10.5281/zenodo.23378305)
# Design by Clarke Yoursa Tee
"""Tests for Clarke's append-only telemetry, /cdp/status, data_miner,
Prometheus counter/rate/StaleNaN/entanglement, Grafana panels 100..105, and SPDX/AKLT.
"""
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]

from orchestrator import data_miner  # noqa: E402
from prometheus import metrics_server, tsdb_telemetry  # noqa: E402


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_new_code_files_have_required_header():
    expected_lines = [
        "# SPDX-License-Identifier: MIT",
        "# Copyright (c) 2026 Clarke Yoursa Tee (AxiomicCoreness)",
        "# Zenodo DOI: 10.5281/zenodo.23378305 (https://doi.org/10.5281/zenodo.23378305)",
        "# Design by Clarke Yoursa Tee",
    ]
    for rel in [
        "orchestrator/data_miner.py",
        "prometheus/tsdb_telemetry.py",
        "tests/test_telemetry_grafana_append.py",
    ]:
        head = (ROOT / rel).read_text(encoding="utf-8").splitlines()[:4]
        assert head == expected_lines, f"Header mismatch in {rel}"


def test_aklt_spdx_and_delta_invariant():
    for name, rel in [("lower", ".container/aklt_gap.py"), ("upper", "scripts/AKLT_gap.py")]:
        p = ROOT / rel
        lines = p.read_text(encoding="utf-8").splitlines()
        assert any("SPDX-License-Identifier: MIT" in ln for ln in lines[:10]), rel
        mod = _load_module(f"aklt_{name}_test", p)
        assert mod.DELTA_AKLT == pytest.approx(0.41050, abs=1e-12)


def test_data_miner_append_only_preserves_prior_bytes(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_MINER_OUT_DIR", str(tmp_path))
    monkeypatch.delenv("DATA_MINER_LOG_PATH", raising=False)
    resolved = data_miner.resolve_log_path()
    assert resolved == tmp_path / "data_miner_ledger.jsonl"

    r0 = data_miner.append_batch_record(0, [1.0, 3.0])
    assert r0["k"] == 0
    assert r0["batch_size"] == 2
    assert r0["mean"] == pytest.approx(2.0)
    assert r0["max_tau"] == pytest.approx(3.0)
    assert r0["iota_seal"] == "DATA_MINING_CONVERGENCE_8837"
    bytes_after_0 = resolved.read_bytes()

    r1 = data_miner.append_batch_record(
        1,
        [{"value": 10.0, "tau": 0.4}, {"value": 20.0, "tau": 2.5}],
    )
    assert r1["k"] == 1
    assert r1["batch_size"] == 2
    assert r1["mean"] == pytest.approx(15.0)
    assert r1["max_tau"] == pytest.approx(2.5)
    assert r1["iota_seal"] == "DATA_MINING_CONVERGENCE_8837"

    bytes_after_1 = resolved.read_bytes()
    assert bytes_after_1.startswith(bytes_after_0)
    rows = data_miner.read_ledger(resolved)
    assert len(rows) == 2


def test_data_miner_default_work_out_path(monkeypatch):
    monkeypatch.delenv("DATA_MINER_LOG_PATH", raising=False)
    monkeypatch.delenv("DATA_MINER_OUT_DIR", raising=False)
    assert data_miner.resolve_log_path() == Path("/work/out/data_miner_ledger.jsonl")


def test_prometheus_counter_reset_rate_and_stale_nan():
    assert tsdb_telemetry.counter_delta(10.0, 15.0) == pytest.approx(5.0)
    # Reset rule: C[j] < C[j-1] -> delta = C[j]
    assert tsdb_telemetry.counter_delta(15.0, 3.0) == pytest.approx(3.0)

    samples = [
        (0.0, 10.0),
        (10.0, 15.0),  # +5
        (20.0, 3.0),   # reset -> +3
        (30.0, 7.0),   # +4
    ]
    # Total delta = 5 + 3 + 4 = 12 over W = [0, 30] -> 12 / 30 = 0.4
    assert tsdb_telemetry.counter_rate(samples, 0.0, 30.0) == pytest.approx(0.4)

    # StaleNaN after lookback
    assert tsdb_telemetry.eval_with_lookback(1.25, t_sample=100.0, t_last=50.0, lookback=60.0) == pytest.approx(1.25)
    assert math.isnan(tsdb_telemetry.eval_with_lookback(1.25, t_sample=120.0, t_last=50.0, lookback=60.0))

    # Registry metrics & exclusion of sovereign_workload
    names = set(tsdb_telemetry.TELEMETRY_REGISTRY.metric_names())
    assert {"tau_handover", "batch_index", "handover_active", "entanglement", "cdp_batches_total"} <= names
    assert "sovereign_workload" not in names

    ms_metrics = metrics_server.get_metrics()
    assert {"tau_handover", "batch_index", "handover_active", "entanglement", "cdp_batches_total"} <= set(ms_metrics)


def test_grafana_panels_append_and_dashboard_unique_ids():
    panels = json.loads((ROOT / "grafana_panels_append.json").read_text(encoding="utf-8"))
    ids = [p["id"] for p in panels]
    assert ids == [100, 101, 102, 103, 104, 105]
    assert len(ids) == len(set(ids))
    for p in panels:
        assert p["type"] == "timeseries"
        assert "Design by Clarke Yoursa Tee" in p["description"]
        assert p["options"]["connectNulls"] is False
        assert p["fieldConfig"]["defaults"]["custom"]["connectNulls"] is False
        assert p["fieldConfig"]["defaults"]["custom"]["spanNulls"] is False

    p105 = [p for p in panels if p["id"] == 105][0]
    exprs_105 = [t["expr"] for t in p105["targets"]]
    assert "entanglement" in exprs_105
    assert all("sovereign_workload" not in e for p in panels for t in p["targets"] for e in [t["expr"]])

    all_exprs = [t["expr"] for p in panels for t in p["targets"]]
    assert any("tau_handover" in e for e in all_exprs)
    assert any("handover_active" in e for e in all_exprs)
    assert any("batch_index" in e for e in all_exprs)
    assert any("rate(" in e for e in all_exprs)
    assert any("min_over_time" in e for e in all_exprs)
    assert any("max_over_time" in e for e in all_exprs)

    dash = json.loads((ROOT / "monitoring" / "grafana-dashboard.json").read_text(encoding="utf-8"))
    dash_ids = [p.get("id") for p in dash["panels"] if p.get("id") is not None]
    assert len(dash_ids) == len(set(dash_ids))
    assert set(ids) <= set(dash_ids)
    assert len(dash["panels"]) >= 13


@pytest.mark.parametrize("rel", ["port380_mcp.py", "mcp/port380_mcp.py"])
def test_port380_cdp_status_schema(rel, monkeypatch):
    mod = _load_module("port380_cdp_test_" + rel.replace("/", "_"), ROOT / rel)
    client = TestClient(mod.app)

    monkeypatch.delenv("CDP_SESSION_STATUS", raising=False)
    mod.set_cdp_session_state("disconnected", tau_handover=1.5)
    r0 = client.get("/cdp/status")
    assert r0.status_code == 200
    d0 = r0.json()
    assert isinstance(d0["tau_handover"], float) and d0["tau_handover"] >= 0.0
    assert d0["sigma_session"] == 0
    assert d0["iota_seal"] == "DATA_MINING_CONVERGENCE_8837"
    assert d0["S_t"] == [d0["tau_handover"], 0, "DATA_MINING_CONVERGENCE_8837"]

    mod.set_cdp_session_state("auto handover established", tau_handover=0.75)
    r1 = client.get("/cdp/status")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["tau_handover"] == pytest.approx(0.75)
    assert d1["sigma_session"] == 1
    assert d1["iota_seal"] == "DATA_MINING_CONVERGENCE_8837"


def test_grafana_envelope_projection_and_stale_gaps():
    env = tsdb_telemetry.project_grafana_envelope(
        samples=[(0.0, 1.0), (1.0, 5.0), (2.0, 3.0), (19.0, 2.0)],
        t_start=0.0,
        t_end=20.0,
        width_px=4,
        height_px=100,
        lookback=5.0,
    )
    assert env["connect_nulls"] is False
    buckets = env["buckets"]
    assert len(buckets) == 4
    assert buckets[0]["min_v"] == pytest.approx(1.0)
    assert buckets[0]["max_v"] == pytest.approx(5.0)
    assert buckets[1]["stale"] is True and buckets[1]["min_v"] is None
    assert buckets[2]["stale"] is True and buckets[2]["max_v"] is None
    assert buckets[3]["stale"] is False and buckets[3]["min_v"] == pytest.approx(2.0)
