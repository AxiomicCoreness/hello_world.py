# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Clarke Yoursa Tee (AxiomicCoreness)
# Zenodo DOI: 10.5281/zenodo.23378305 (https://doi.org/10.5281/zenodo.23378305)
# DeepInfer model design is by Clarke Yoursa Tee
"""
prometheus/connectome_telemetry.py — CB2514 connectome prototype gauges.

Append-only addition to the telemetry work (PR #207). Every value is read from
files that are in the repository; nothing is estimated or defaulted:

  src/main/resources/connectome/neuron_index.json
  src/main/resources/connectome/roi_context_PVLP_R.json
  data/cb2514/dataset.json
  data/cb2514/source/checksums.json (+ the source files it lists that are present)
  data/cb2514/source/annotations/CB2514_from_*.csv
  cb2514_opd.validate_distillation_input(None) (fail-closed; no weights, no I/O
  beyond the repository metadata, no training)

Absent or inconsistent data yields StaleNaN (float('nan')), never 0. On the
metrics server a NaN sample is not exposed at all (absent series), which
Grafana draws as a gap (connectNulls false).

PVLP(R) is chart-observed ROI context only. The repository contains no edge
export and no per-ROI synapse counts, so connectome_edges_total and
connectome_roi_synapses are StaleNaN by construction until authentic data exist.
"""
import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

DESIGN_CREDIT: str = "DeepInfer model design is by Clarke Yoursa Tee"
REPO_ROOT: Path = Path(__file__).resolve().parents[1]
NAN: float = float("nan")

NEURON_INDEX_REL = Path("src/main/resources/connectome/neuron_index.json")
ROI_CONTEXT_REL = Path("src/main/resources/connectome/roi_context_PVLP_R.json")
DATASET_REL = Path("data/cb2514/dataset.json")
CHECKSUMS_REL = Path("data/cb2514/source/checksums.json")

#: (name, type, help) for every gauge; labelled gauges share one name.
METRIC_HELP: Dict[str, str] = {
    "connectome_neurons_total": "CB2514 neurons listed in neuron_index.json",
    "connectome_neurons_left_total": "CB2514 neurons with somaSide L (neuron_index.json)",
    "connectome_neurons_right_total": "CB2514 neurons with somaSide R (neuron_index.json)",
    "connectome_edges_total": "Edges in the repository edge export; StaleNaN when none is packaged",
    "connectome_roi_synapses": "Synapse count for the ROI context; StaleNaN, chart context carries no counts",
    "connectome_roi_context_present": "1 when the ROI chart-context file parses with its declared role",
    "connectome_roi_membership_verified": "0 while ROI membership is chart-observed only, 1 when verified",
    "connectome_skeletons_present_total": "Skeleton files present in the tree (neuron_index.json)",
    "connectome_skeletons_missing_total": "Skeleton files recorded as missing (neuron_index.json)",
    "connectome_annotation_rows_total": "Body rows in the packaged CB2514 annotation CSV",
    "connectome_dataset_checksum_ok": "1 when every packaged source checksum verifies, else 0",
    "connectome_dataset_checksum_files_present_total": "Files listed in checksums.json that are present and hashed",
    "cb2514_identity_ok": "1 when checksums, dataset body ids, index and annotation CSV agree, else 0",
    "cb2514_distillation_validation_ok": "validate_distillation_input(None).ok (0 = fail-closed, inputs absent)",
    "cb2514_distillation_missing_prerequisites_total": "Prerequisites reported missing by validate_distillation_input(None)",
}


@dataclass(frozen=True)
class Sample:
    name: str
    value: float
    help_text: str
    labels: Optional[Dict[str, str]] = None

    @property
    def is_stale(self) -> bool:
        return not math.isfinite(self.value)

    @property
    def key(self) -> str:
        """Stable identity: name plus sorted label pairs."""
        if not self.labels:
            return self.name
        inner = ",".join(f'{k}="{v}"' for k, v in sorted(self.labels.items()))
        return f"{self.name}{{{inner}}}"


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _annotation_body_ids(root: Path) -> Optional[List[int]]:
    ann_dir = root / "data" / "cb2514" / "source" / "annotations"
    csvs = sorted(ann_dir.glob("CB2514_from_*.csv")) if ann_dir.is_dir() else []
    if not csvs:
        return None
    try:
        with csvs[0].open("r", encoding="utf-8", newline="") as handle:
            return [int(row["bodyId"]) for row in csv.DictReader(handle)]
    except (OSError, KeyError, ValueError):
        return None


def _opd() -> Any:
    """Import cb2514_opd (repo root module), adding the repo root to sys.path if needed."""
    try:
        import cb2514_opd
    except ImportError:
        import sys

        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        import cb2514_opd
    return cb2514_opd


def _checksum_state(root: Path) -> "tuple[float, float]":
    """(checksum_ok, files_present). NaN pair when the evidence cannot be read."""
    try:
        cb2514_opd = _opd()
        problems = cb2514_opd.verify_included_checksums(root)
        records = cb2514_opd.load_checksum_records(root)
        present = sum(
            1 for rec in records if (cb2514_opd.source_root(root) / str(rec["path"])).is_file()
        )
    except Exception:
        return NAN, NAN
    return (1.0 if not problems else 0.0), float(present)


def _distillation_state(root: Path) -> "tuple[float, float]":
    # The check is only meaningful against a repository that carries the CB2514 dataset.
    if _read_json(root / DATASET_REL) is None:
        return NAN, NAN
    try:
        report = _opd().validate_distillation_input(None, root)
        return (1.0 if report.get("ok") is True else 0.0), float(len(report["missing_prerequisites"]))
    except Exception:
        return NAN, NAN


def collect(repo_root: Optional[Path] = None) -> List[Sample]:
    """Read the repository files and return one Sample per series."""
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    out: List[Sample] = []

    def add(name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        out.append(Sample(name, float(value), METRIC_HELP[name], labels))

    index = _read_json(root / NEURON_INDEX_REL)
    neurons = index.get("neurons") if index else None
    if isinstance(neurons, list) and index.get("count") == len(neurons):
        add("connectome_neurons_total", len(neurons))
        for side, name in (("L", "connectome_neurons_left_total"), ("R", "connectome_neurons_right_total")):
            add(name, sum(1 for n in neurons if isinstance(n, dict) and n.get("somaSide") == side))
        add(
            "connectome_skeletons_present_total",
            sum(1 for n in neurons if isinstance(n, dict) and n.get("skeleton_present") is True),
        )
        missing = index.get("missing_skeletons")
        add("connectome_skeletons_missing_total", len(missing) if isinstance(missing, list) else NAN)
        edges = index.get("edges")
        edges_value = (
            float(len(edges)) if index.get("edges_included") is True and isinstance(edges, list) else NAN
        )
        add("connectome_edges_total", edges_value)
    else:
        for name in (
            "connectome_neurons_total",
            "connectome_skeletons_present_total",
            "connectome_skeletons_missing_total",
            "connectome_edges_total",
        ):
            add(name, NAN)
        add("connectome_neurons_left_total", NAN)
        add("connectome_neurons_right_total", NAN)

    roi = _read_json(root / ROI_CONTEXT_REL)
    roi_label = str(roi.get("display")) if roi and roi.get("display") else "PVLP(R)"
    roi_ok = bool(roi) and roi.get("role") == "observed_chart_roi_context_only"
    add("connectome_roi_context_present", 1.0 if roi_ok else NAN, {"roi": roi_label})
    if roi_ok and isinstance(roi.get("chart_membership_unverified"), bool):
        add("connectome_roi_membership_verified", 0.0 if roi["chart_membership_unverified"] else 1.0, {"roi": roi_label})
    else:
        add("connectome_roi_membership_verified", NAN, {"roi": roi_label})
    synapses = roi.get("synapse_count") if roi_ok else None
    add(
        "connectome_roi_synapses",
        float(synapses) if isinstance(synapses, (int, float)) and not isinstance(synapses, bool) else NAN,
        {"roi": roi_label},
    )

    body_ids = _annotation_body_ids(root)
    add("connectome_annotation_rows_total", float(len(body_ids)) if body_ids is not None else NAN)

    checksum_ok, files_present = _checksum_state(root)
    add("connectome_dataset_checksum_ok", checksum_ok)
    add("connectome_dataset_checksum_files_present_total", files_present)

    dataset = _read_json(root / DATASET_REL)
    identity = NAN
    if (
        math.isfinite(checksum_ok)
        and index
        and dataset
        and isinstance(neurons, list)
        and body_ids is not None
        and isinstance(dataset.get("expected_body_ids"), list)
    ):
        expected = dataset["expected_body_ids"]
        agree = (
            checksum_ok == 1.0
            and index.get("bodyIds") == expected
            and sorted(body_ids) == sorted(expected)
            and len(neurons) == dataset.get("expected_body_count")
            and index.get("cell_type") == dataset.get("cell_type")
            and index.get("dataset_uuid") == dataset.get("dataset_uuid")
        )
        identity = 1.0 if agree else 0.0
    add("cb2514_identity_ok", identity)

    distill_ok, distill_missing = _distillation_state(root)
    add("cb2514_distillation_validation_ok", distill_ok)
    add("cb2514_distillation_missing_prerequisites_total", distill_missing)
    return out


def publish_tsdb(registry: Any = None, repo_root: Optional[Path] = None, now: Optional[float] = None) -> Dict[str, float]:
    """Register label-free samples in the TSDB registry (NaN stays NaN).

    Labelled series are carried by the metrics server (publish_metrics_server).
    """
    from prometheus import tsdb_telemetry

    reg = registry if registry is not None else tsdb_telemetry.TELEMETRY_REGISTRY
    ts = time.time() if now is None else float(now)
    published: Dict[str, float] = {}
    for sample in collect(repo_root):
        if sample.labels:
            continue
        tsdb_telemetry.register_gauge(reg, sample.name, sample.help_text)
        reg.set_gauge(sample.name, sample.value, ts)
        published[sample.name] = sample.value
    return published


def publish_metrics_server(registry: Dict[str, Any], lock: Any, repo_root: Optional[Path] = None) -> Dict[str, float]:
    """Write finite samples into a metrics_server-style _REGISTRY (name -> (value, help, type, labels)); one series per name.

    StaleNaN samples are removed so the series is absent rather than exposed as 0.
    """
    published: Dict[str, float] = {}
    samples = collect(repo_root)
    with lock:
        for sample in samples:
            # metrics_server renders by registry key, so each name carries one series.
            reg_key = sample.name
            if sample.is_stale:
                registry.pop(reg_key, None)
                continue
            registry[reg_key] = (sample.value, sample.help_text, "gauge", sample.labels)
            published[sample.key] = sample.value
    return published
