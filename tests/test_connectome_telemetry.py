# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Clarke Yoursa Tee (AxiomicCoreness)
# Zenodo DOI: 10.5281/zenodo.23378305 (https://doi.org/10.5281/zenodo.23378305)
# DeepInfer model design is by Clarke Yoursa Tee
"""Tests for prometheus/connectome_telemetry.py: value parity with the repository
files, StaleNaN on absent data, metrics-server exposure, and Grafana panel ids.
"""
import csv
import json
import math
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import pytest

ROOT = Path(__file__).resolve().parents[1]

from prometheus import connectome_telemetry as ct  # noqa: E402
from prometheus import metrics_server, tsdb_telemetry  # noqa: E402

NEW_PANEL_IDS = [112, 113, 114, 115, 116, 117]
STALE_BY_CONSTRUCTION = {"connectome_edges_total", "connectome_roi_synapses"}


def _by_name(samples: List[ct.Sample]) -> Dict[str, ct.Sample]:
    out = {s.name: s for s in samples}
    assert len(out) == len(samples), "duplicate series name"
    return out


def _json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _copy_repo_subset(dst: Path, skip: Optional[str] = None) -> Path:
    rels = [
        ct.NEURON_INDEX_REL,
        ct.ROI_CONTEXT_REL,
        ct.DATASET_REL,
        ct.CHECKSUMS_REL,
        Path("data/cb2514/source/SOURCE_PROVENANCE.txt"),
    ]
    for ann in (ROOT / "data/cb2514/source/annotations").glob("CB2514_from_*.csv"):
        rels.append(ann.relative_to(ROOT))
    for rel in rels:
        if skip and str(rel) == skip:
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    return dst


def test_new_files_have_required_header():
    expected = [
        "# SPDX-License-Identifier: MIT",
        "# Copyright (c) 2026 Clarke Yoursa Tee (AxiomicCoreness)",
        "# Zenodo DOI: 10.5281/zenodo.23378305 (https://doi.org/10.5281/zenodo.23378305)",
        "# DeepInfer model design is by Clarke Yoursa Tee",
    ]
    for rel in ["prometheus/connectome_telemetry.py", "tests/test_connectome_telemetry.py"]:
        assert (ROOT / rel).read_text(encoding="utf-8").splitlines()[:4] == expected, rel


def test_values_match_source_files():
    s = _by_name(ct.collect(ROOT))
    index = _json("src/main/resources/connectome/neuron_index.json")
    roi = _json("src/main/resources/connectome/roi_context_PVLP_R.json")
    dataset = _json("data/cb2514/dataset.json")
    neurons = index["neurons"]

    assert s["connectome_neurons_total"].value == len(neurons) == index["count"]
    assert s["connectome_neurons_left_total"].value == index["laterality"]["L"]
    assert s["connectome_neurons_right_total"].value == index["laterality"]["R"]
    assert s["connectome_neurons_left_total"].value == sum(1 for n in neurons if n["somaSide"] == "L")
    assert s["connectome_skeletons_present_total"].value == sum(1 for n in neurons if n["skeleton_present"])
    assert s["connectome_skeletons_missing_total"].value == len(index["missing_skeletons"])

    csv_path = next((ROOT / "data/cb2514/source/annotations").glob("CB2514_from_*.csv"))
    with csv_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert s["connectome_annotation_rows_total"].value == len(rows) == dataset["expected_body_count"]
    assert sorted(int(r["bodyId"]) for r in rows) == sorted(dataset["expected_body_ids"]) == sorted(index["bodyIds"])

    assert s["connectome_roi_context_present"].value == 1.0
    assert s["connectome_roi_context_present"].labels == {"roi": roi["display"]}
    assert s["connectome_roi_membership_verified"].value == (0.0 if roi["chart_membership_unverified"] else 1.0)

    assert s["connectome_dataset_checksum_ok"].value == 1.0
    assert s["cb2514_identity_ok"].value == 1.0
    assert s["cb2514_distillation_validation_ok"].value == 0.0
    assert s["cb2514_distillation_missing_prerequisites_total"].value == 5.0

    present = sum(
        1
        for rec in _json("data/cb2514/source/checksums.json")["files"]
        if (ROOT / "data/cb2514/source" / rec["path"]).is_file()
    )
    assert s["connectome_dataset_checksum_files_present_total"].value == present


def test_no_edges_or_roi_synapses_are_invented():
    index = _json("src/main/resources/connectome/neuron_index.json")
    assert index["edges_included"] is False
    s = _by_name(ct.collect(ROOT))
    for name in STALE_BY_CONSTRUCTION:
        assert math.isnan(s[name].value), name
        assert s[name].is_stale


def test_every_documented_metric_is_emitted():
    assert set(_by_name(ct.collect(ROOT))) == set(ct.METRIC_HELP)


def test_missing_files_yield_stale_nan_not_zero(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    samples = ct.collect(empty)
    assert samples and all(math.isnan(x.value) for x in samples)


def test_missing_neuron_index_only_stales_dependent_series(tmp_path):
    repo = _copy_repo_subset(tmp_path / "r", skip=str(ct.NEURON_INDEX_REL))
    s = _by_name(ct.collect(repo))
    for name in (
        "connectome_neurons_total",
        "connectome_neurons_left_total",
        "connectome_neurons_right_total",
        "connectome_skeletons_present_total",
        "connectome_skeletons_missing_total",
        "cb2514_identity_ok",
    ):
        assert math.isnan(s[name].value), name
    assert s["connectome_dataset_checksum_ok"].value == 1.0
    assert s["connectome_annotation_rows_total"].value == 5.0


def test_tampered_annotation_fails_checksum_and_identity(tmp_path):
    repo = _copy_repo_subset(tmp_path / "r")
    csv_path = next((repo / "data/cb2514/source/annotations").glob("CB2514_from_*.csv"))
    csv_path.write_bytes(csv_path.read_bytes() + b"\n")
    s = _by_name(ct.collect(repo))
    assert s["connectome_dataset_checksum_ok"].value == 0.0
    assert s["cb2514_identity_ok"].value == 0.0


def test_publish_tsdb_keeps_nan_and_values():
    reg = tsdb_telemetry.TelemetryRegistry()
    before = reg.metric_names()
    published = ct.publish_tsdb(reg, ROOT, now=1000.0)
    assert reg.metric_names()[: len(before)] == before  # existing slots untouched
    assert reg.sample_metric("connectome_neurons_total", 1000.0) == 5.0
    assert reg.sample_metric("cb2514_identity_ok", 1000.0) == 1.0
    assert math.isnan(reg.sample_metric("connectome_edges_total", 1000.0))
    # lookback: a value older than the window is StaleNaN
    assert math.isnan(reg.sample_metric("connectome_neurons_total", 1000.0 + 301.0))
    assert "connectome_roi_synapses" not in published  # labelled series live on the server
    text = reg.render_prometheus_text()
    assert "connectome_edges_total nan" in text
    assert "entanglement 1.0" in text


def test_publish_tsdb_missing_data_is_nan(tmp_path):
    reg = tsdb_telemetry.TelemetryRegistry()
    ct.publish_tsdb(reg, tmp_path, now=5.0)
    assert math.isnan(reg.sample_metric("connectome_neurons_total", 5.0))


def test_metrics_server_exposes_finite_values_and_omits_stale():
    text = metrics_server.render_prometheus_text()
    lines = {ln.split(" ")[0]: ln.split(" ")[1] for ln in text.splitlines() if ln and not ln.startswith("#")}
    assert float(lines["connectome_neurons_total"]) == 5.0
    assert float(lines["cb2514_identity_ok"]) == 1.0
    assert float(lines['connectome_roi_membership_verified{roi="PVLP(R)"}']) == 0.0
    assert not any(k.startswith("connectome_edges_total") for k in lines)
    assert not any(k.startswith("connectome_roi_synapses") for k in lines)


def test_publish_metrics_server_removes_series_when_data_vanish(tmp_path):
    import threading

    reg: dict = {}
    lock = threading.Lock()
    ct.publish_metrics_server(reg, lock, ROOT)
    assert "connectome_neurons_total" in reg
    ct.publish_metrics_server(reg, lock, tmp_path)
    assert "connectome_neurons_total" not in reg and "cb2514_identity_ok" not in reg


def _panel_ids(rel: str) -> List[int]:
    data = _json_any(rel)
    panels = data if isinstance(data, list) else data["panels"]
    return [p["id"] for p in panels if "id" in p]


def _json_any(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_panel_ids_do_not_collide():
    root_ids = _panel_ids("grafana_panels_append.json")
    conn_ids = _panel_ids("grafana_panels_connectome_append.json")
    dash_ids = _panel_ids("monitoring/grafana-dashboard.json")
    mon_ids = _panel_ids("monitoring/grafana_panels_append.json")
    for ids in (root_ids, dash_ids, mon_ids):
        assert len(ids) == len(set(ids))
    # 106-111 are used by monitoring/grafana_panels_append.json; the connectome panels start at 112.
    assert set(mon_ids) >= {106, 107, 108, 109, 110, 111}
    assert conn_ids == NEW_PANEL_IDS
    assert set(NEW_PANEL_IDS) <= set(dash_ids)
    assert not set(NEW_PANEL_IDS) & set(mon_ids)
    assert not set(NEW_PANEL_IDS) & set(root_ids)
    assert root_ids == [100, 101, 102, 103, 104, 105]  # PR #207 file stays unchanged
    assert len(conn_ids) == len(set(conn_ids))


def test_connectome_panels_are_gap_preserving_and_bound_to_real_metrics():
    panels = {p["id"]: p for p in _json_any("grafana_panels_connectome_append.json")}
    dash = {
        p["id"]: p
        for p in _json_any("monitoring/grafana-dashboard.json")["panels"]
        if p.get("id") in NEW_PANEL_IDS
    }
    assert panels == dash
    assert sorted(panels) == NEW_PANEL_IDS
    for pid, panel in panels.items():
        assert panel["type"] in {"stat", "timeseries"}
        assert panel["options"]["connectNulls"] is False
        assert panel["fieldConfig"]["defaults"]["custom"]["connectNulls"] is False
        assert "DeepInfer model design is by Clarke Yoursa Tee" in panel["description"]
        for target in panel["targets"]:
            assert target["expr"] in ct.METRIC_HELP, (pid, target["expr"])
