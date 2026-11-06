#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""CB2514 identification metadata and fail-closed OPD distillation-input checks.

This module does not download weights, open the configured GGUF, launch
training, or invent synaptic edges. PVLP(R) is chart context only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from deepinfer_teacher_adapter import assess_deepinfer_expert

REPO_ROOT = Path(__file__).resolve().parent

CONFIGURED_GGUF_PATH = (
    "/kaggle/input/models/clarkeyoursatee/deepseek-r1-1-5b-q4-k-m/gguf/"
    "deepseek-r2-1.5b-q4_k_m/2/deepseek-r1-distill-1.5b-Q4_K_M.gguf"
)
NOMINAL_STUDENT = "DeepSeek-R1-Distill-1.5B"
STUDENT_ROLE_NAMES = frozenset({"DeepInfer", "DeepTutor"})

# Digest of data/cb2514/source/checksums.json recorded by the standalone
# package provenance manifest. The file bytes are the original; this constant
# must match them and is not a replacement checksum.
PRESERVED_CHECKSUMS_JSON_SHA256 = (
    "69b6934fa9339bbfac7cb6d73d5b12f8c5215bc13a5a3c665a23c376031814ef"
)
PRESERVED_CHECKSUMS_JSON_BYTES = 1843

REQUIRED_DISTILL_FIELDS = (
    "compatible_tokenizer_vocab_context",
    "normalized_expert_distributions",
    "normalized_student_distribution",
    "model_ids",
    "student_trajectory_provenance",
)

EXIT_OK = 0
EXIT_VALIDATION = 11
EXIT_BLOCKED_DISTILLATION = 30

PROB_SUM_TOLERANCE = 1e-6
CONTEXT_PROBABILITY_KEYS = frozenset(
    {"probs", "probability", "weight", "logits", "expert_probs", "student_probs"}
)

OMITTED_SOURCE_URLS = {
    "annotations/body-annotations-male-cns-v1.0-minconf-0.5.feather": (
        "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/"
        "flat-connectome/body-annotations-male-cns-v1.0-minconf-0.5.feather"
    ),
    "catalog/neurons.json": (
        "https://raw.githubusercontent.com/reiserlab/"
        "celltype-explorer-drosophila-male-cns/main/data/neurons.json"
    ),
    "pages/CB2514.html": (
        "https://reiserlab.github.io/celltype-explorer-drosophila-male-cns/types/CB2514.html"
    ),
}


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_dataset(repo: Path = REPO_ROOT) -> Dict[str, Any]:
    path = repo / "data" / "cb2514" / "dataset.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_checksum_records(repo: Path = REPO_ROOT) -> List[Dict[str, Any]]:
    path = repo / "data" / "cb2514" / "source" / "checksums.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    files = payload.get("files")
    if not isinstance(files, list):
        raise ValueError("checksums.json has no files list")
    return files


def source_root(repo: Path = REPO_ROOT) -> Path:
    return repo / "data" / "cb2514" / "source"


def verify_included_checksums(repo: Path = REPO_ROOT) -> List[str]:
    """Recompute hashes only for source bytes that are in the tree."""
    problems: List[str] = []
    root = source_root(repo)
    checksum_path = root / "checksums.json"
    raw = checksum_path.read_bytes()
    if len(raw) != PRESERVED_CHECKSUMS_JSON_BYTES:
        problems.append(
            f"checksums.json bytes {len(raw)} != preserved {PRESERVED_CHECKSUMS_JSON_BYTES}"
        )
    actual_checksums = hashlib.sha256(raw).hexdigest()
    if actual_checksums != PRESERVED_CHECKSUMS_JSON_SHA256:
        problems.append("checksums.json sha256 != preserved package digest")
    by_path = {str(rec["path"]): rec for rec in load_checksum_records(repo)}
    for rel, rec in by_path.items():
        path = root / rel
        if not path.is_file():
            continue
        actual = sha256_file(path)
        if actual != rec["sha256"] or path.stat().st_size != rec["bytes"]:
            problems.append(f"included source checksum mismatch: {rel}")
    return problems


def omitted_source_records(repo: Path = REPO_ROOT) -> List[Dict[str, Any]]:
    root = source_root(repo)
    records: List[Dict[str, Any]] = []
    for rec in load_checksum_records(repo):
        rel = str(rec["path"])
        if (root / rel).is_file():
            continue
        url = OMITTED_SOURCE_URLS.get(rel)
        if url is None and rel.startswith("skeletons/") and rel.endswith(".swc"):
            body_id = Path(rel).stem
            url = (
                "https://storage.googleapis.com/flyem-male-cns/v1.0/segmentation/"
                f"skeletons-malecns/skeletons-swc/{body_id}.swc"
            )
        records.append(
            {
                "bytes": rec["bytes"],
                "checksum_recomputed": False,
                "path": rel,
                "sha256": rec["sha256"],
                "url": url,
            }
        )
    return records


def _parse_body_id(raw: str) -> int:
    value = int(float(str(raw).strip()))
    if value <= 0:
        raise ValueError(f"invalid bodyId: {raw!r}")
    return value


def build_neuron_index(repo: Path = REPO_ROOT) -> Dict[str, Any]:
    dataset = load_dataset(repo)
    csv_path = repo / dataset["annotation_csv_relative"]
    expected_type = dataset["cell_type"]
    expected_ids = [int(x) for x in dataset["expected_body_ids"]]
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("annotation CSV has no header")
        missing = [c for c in ("bodyId", "type", "instance", "somaSide") if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"annotation CSV missing columns: {missing}")
        rows = list(reader)
    neurons: List[Dict[str, Any]] = []
    body_ids: List[int] = []
    for row in rows:
        body_id = _parse_body_id(row["bodyId"])
        cell_type = (row.get("type") or "").strip()
        if cell_type != expected_type:
            raise ValueError(f"row type {cell_type!r} != {expected_type!r}")
        flywire = (row.get("flywireType") or "").strip()
        if flywire and flywire != expected_type:
            raise ValueError(f"flywireType {flywire!r} != {expected_type!r}")
        side = (row.get("somaSide") or "").strip()
        if side not in {"L", "R"}:
            raise ValueError(f"somaSide must be L or R, got {side!r}")
        swc_rel = f"skeletons/{body_id}.swc"
        neurons.append(
            {
                "bodyId": body_id,
                "instance": (row.get("instance") or "").strip(),
                "skeleton_bytes_in_tree": False,
                "skeleton_checksum_record": swc_rel,
                "skeleton_present": False,
                "skeleton_url": (
                    "https://storage.googleapis.com/flyem-male-cns/v1.0/segmentation/"
                    f"skeletons-malecns/skeletons-swc/{body_id}.swc"
                ),
                "somaSide": side,
                "status": (row.get("status") or "").strip(),
                "statusLabel": (row.get("statusLabel") or "").strip(),
                "superclass": (row.get("superclass") or "").strip(),
                "type": cell_type,
                "vfbId": (row.get("vfbId") or "").strip(),
            }
        )
        body_ids.append(body_id)
    if body_ids != expected_ids:
        raise ValueError(f"bodyId order/set mismatch: {body_ids} != {expected_ids}")
    if len(set(body_ids)) != len(body_ids):
        raise ValueError("duplicate bodyId values")
    right = sum(1 for n in neurons if n["somaSide"] == "R")
    left = sum(1 for n in neurons if n["somaSide"] == "L")
    return {
        "bodyIds": body_ids,
        "cell_type": expected_type,
        "connectivity_resource": "connectome/connectivity_edge_schema.json",
        "count": len(neurons),
        "dataset_id": dataset["dataset_id"],
        "dataset_uuid": dataset["dataset_uuid"],
        "edges_included": False,
        "laterality": {"L": left, "R": right},
        "missing_skeletons": list(body_ids),
        "neurons": neurons,
        "notes": [
            "Built only from the CB2514 annotation CSV subset.",
            "Skeleton bytes are not in the tree; checksum records are preserved.",
            "Does not encode synaptic edges or ROI membership claims.",
        ],
        "roi_context_resource": "connectome/roi_context_PVLP_R.json",
        "schema": "clarke_cb2514_neuron_index/v1",
        "source_csv": dataset["annotation_csv_relative"],
    }


def build_roi_context(repo: Path = REPO_ROOT) -> Dict[str, Any]:
    dataset = load_dataset(repo)
    cfg = dict(dataset["roi_context"])
    return {
        "associated_cell_type_for_page_context": dataset["cell_type"],
        "chart_membership_unverified": True,
        "config_echo": cfg,
        "dataset_id": dataset["dataset_id"],
        "display": "PVLP(R)",
        "edges_inferred_from_charts": False,
        "laterality": "R",
        "limits": [
            "Observed on Cell Type Explorer / screenshot charts for CB2514 page context.",
            "Does not verify that each CB2514 body innervates PVLP(R).",
            "Must not be concatenated into teacher distributions or edge lists.",
            "Must not be used to reconstruct connectivity weights from chart percentages.",
        ],
        "not_a_cell_type": True,
        "not_per_body_annotation": True,
        "roi_name": "PVLP",
        "role": "observed_chart_roi_context_only",
        "schema": "clarke_cb2514_roi_context/v1",
    }


def connectivity_edge_schema() -> Dict[str, Any]:
    return {
        "edge_required_fields": ["pre_bodyId", "post_bodyId", "weight"],
        "edges_in_tree": False,
        "notes": [
            "Authentic edge export required. None is packaged here.",
            "Chart tables / donut percentages are not accepted as edge input.",
        ],
        "required_fields": ["dataset_id", "source", "edges"],
        "schema": "clarke_cb2514_connectivity_edges/v1",
    }


def emit_tree(repo: Path = REPO_ROOT) -> None:
    resource_dir = repo / "src" / "main" / "resources" / "connectome"
    resource_dir.mkdir(parents=True, exist_ok=True)
    (resource_dir / "neuron_index.json").write_text(dumps(build_neuron_index(repo)), encoding="utf-8")
    (resource_dir / "roi_context_PVLP_R.json").write_text(dumps(build_roi_context(repo)), encoding="utf-8")
    (resource_dir / "connectivity_edge_schema.json").write_text(
        dumps(connectivity_edge_schema()), encoding="utf-8"
    )
    model_src = repo / "data" / "cb2514" / "local_model_path.json"
    (resource_dir / "local_model_path.json").write_bytes(model_src.read_bytes())
    omitted = {
        "checksums_recomputed": False,
        "files": omitted_source_records(repo),
        "note": (
            "Listed sha256 and byte sizes are copied from "
            "data/cb2514/source/checksums.json. Those bytes are not in the git tree."
        ),
        "preserved_checksums_json_sha256": PRESERVED_CHECKSUMS_JSON_SHA256,
        "schema": "cb2514_omitted_sources/v1",
    }
    (repo / "data" / "cb2514" / "omitted_sources.json").write_text(dumps(omitted), encoding="utf-8")


def _component(repo: Path, path: str, reason: str) -> Dict[str, Any]:
    present = (repo / path).is_file()
    return {
        "path": path,
        "present": present,
        "reason": reason,
        "satisfies_distillation_prerequisite": False,
    }


def repository_components(repo: Path = REPO_ROOT) -> Dict[str, Any]:
    model_path = Path(CONFIGURED_GGUF_PATH)
    deepseek_spec = False
    try:
        import importlib.util

        deepseek_spec = importlib.util.find_spec("deepseek.api") is not None
    except (ImportError, ValueError):
        deepseek_spec = False
    components = {
        "clarke_tokenizer_swift": _component(
            repo,
            "ios/ClarkePocket/Sources/PocketCore/ClarkeTokenizer.swift",
            "Pocket tokenizer for the in-tree Clarke engine, not the configured R1-Distill GGUF vocab.",
        ),
        "connectome_loader": _component(
            repo,
            "src/main/java/com/fruitfly/brain/ConnectomeLoader.java",
            "Loads project XML synapses via --connectome-file. It does not read neuron_index.json as edges.",
        ),
        "connectome_xsd": _component(
            repo,
            "src/main/resources/connectome.xsd",
            "Schema for the project XML connectome. CB2514 has no edge document against this schema.",
        ),
        "deepinfer_accelerator": _component(
            repo,
            "engine/deepinfer_accelerator.py",
            "Optional accelerator adapter. Not launched and not a source of expert distributions.",
        ),
        "deepinfer_hf_tokenizer": _component(
            repo,
            "deepinfer/hugging_face/tokenizer.py",
            "DeepInfer Hugging Face tokenizer for the V4 checkpoint, not the configured GGUF vocab.",
        ),
        "hhmi_hemibrain_csv_converter": _component(
            repo,
            "skills/hhmi/hhmi_scripts/csv_to_xml.py",
            "Hemibrain v1.2 CSV to XML converter. It is not a male-cns CB2514 edge export.",
        ),
        "quantum_tokenizer_binary": _component(
            repo,
            "quantum/tokenizer_binary.py",
            "Binary token wire format, not a model vocabulary.",
        ),
        "teavm_connectome_autoplayer": _component(
            repo,
            "games/teavm-rhythm/src/main/java/com/fruitfly/games/rhythm/logic/ConnectomeAutoplayer.java",
            "Rhythm-game toy circuit autoplayer. Not CB2514 connectivity.",
        ),
        "teavm_neuron_snapshot": _component(
            repo,
            "games/teavm-rhythm/src/main/java/com/fruitfly/games/rhythm/logic/NeuronSnapshot.java",
            "Spike snapshot of the rhythm sim. CB2514 identity is a separate aside, not lane spikes.",
        ),
    }
    return {
        "components": components,
        "configured_gguf_accessible": model_path.is_file(),
        "configured_gguf_path": CONFIGURED_GGUF_PATH,
        "deepseek_api_importable": deepseek_spec,
        "deepseek_api_satisfies_distillation_prerequisite": False,
        "kaggle_interaction": False,
        "model_download_attempted": False,
        "model_file_opened": False,
        "nominal_student": NOMINAL_STUDENT,
        "satisfied_prerequisites": [],
        "student_roles_not_teachers": sorted(STUDENT_ROLE_NAMES),
        "training_launched": False,
    }


def _finite_nonnegative(value: float, name: str) -> float:
    number = float(value)
    if (not math.isfinite(number)) or number < 0.0:
        raise ValueError(f"{name} must be nonnegative finite")
    return number


def _as_probs(values: Sequence[Any], name: str) -> List[float]:
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    out = [_finite_nonnegative(v, name) for v in values]
    total = math.fsum(out)
    if abs(total - 1.0) > PROB_SUM_TOLERANCE:
        raise ValueError(
            f"{name} must be normalized to sum≈1 (got sum={total}); refusing silent renormalization"
        )
    return out


def kl_student_expert(
    student: Sequence[float],
    expert: Sequence[float],
    mask: Optional[Sequence[bool]] = None,
) -> float:
    """KL(student || expert). Masked positions are skipped and not renormalized."""
    if len(student) != len(expert):
        raise ValueError("student and expert length mismatch")
    if mask is not None and len(mask) != len(student):
        raise ValueError("mask length mismatch")
    total = 0.0
    for index, (prob, expert_prob) in enumerate(zip(student, expert)):
        if mask is not None and not mask[index]:
            continue
        if prob == 0.0:
            continue
        if expert_prob <= 0.0:
            return math.inf
        total += prob * math.log(prob / expert_prob)
    return total


def weighted_reverse_kl(
    student: Sequence[float],
    experts: Sequence[Mapping[str, Any]],
    mask: Optional[Sequence[bool]] = None,
) -> Dict[str, Any]:
    terms = []
    loss = 0.0
    for expert in experts:
        expert_id = str(expert["expert_id"])
        weight = float(expert["weight"])
        if (not math.isfinite(weight)) or weight < 0.0:
            raise ValueError(f"weight for {expert_id} must be nonnegative finite")
        divergence = kl_student_expert(student, expert["probs"], mask)
        if weight == 0.0 and math.isinf(divergence):
            raise ValueError(f"zero weight with infinite KL is undefined for {expert_id}")
        contribution = weight * divergence if math.isfinite(divergence) else math.inf
        terms.append(
            {
                "dkl_student_||_expert": divergence if math.isfinite(divergence) else None,
                "dkl_infinite": math.isinf(divergence),
                "expert_id": expert_id,
                "weight": weight,
                "weighted_term": contribution if math.isfinite(contribution) else None,
                "weighted_term_infinite": math.isinf(contribution),
            }
        )
        if math.isinf(contribution):
            loss = math.inf
        elif math.isfinite(loss):
            loss += contribution
    return {
        "direction": "reverse_kl_student_||_expert",
        "evaluator_only": True,
        "formula": "sum_i w_i KL(student||expert_i)",
        "loss": None if math.isinf(loss) else loss,
        "loss_infinite": math.isinf(loss),
        "not_training": True,
        "objective": "L_OPD",
        "terms": terms,
        "weight_policy": "caller_supplied_nonnegative_weights_not_silently_normalized",
        "weight_sum": math.fsum(float(expert["weight"]) for expert in experts),
        "weights_normalized_by_evaluator": False,
    }


def _fail(
    missing: List[str],
    message: str,
    repo: Path,
    *,
    exit_code: int = EXIT_BLOCKED_DISTILLATION,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "evaluator_only": True,
        "exit_code": exit_code,
        "kaggle_interaction": False,
        "message": message,
        "missing_prerequisites": list(dict.fromkeys(missing)),
        "model_download_attempted": False,
        "model_file_opened": False,
        "ok": False,
        "on_policy_accepted": False,
        "provenance_declarations_are_not_proof": True,
        "quality_claim": False,
        "repository_components": repository_components(repo),
        "stage": "distillation_opd",
        "training_executed": False,
    }
    if details:
        report["details"] = details
    return report


def _context_records_carry_probabilities(context: Mapping[str, Any]) -> bool:
    if CONTEXT_PROBABILITY_KEYS.intersection(context):
        return True
    records = context.get("records")
    if not isinstance(records, list):
        return False
    for record in records:
        if isinstance(record, Mapping) and CONTEXT_PROBABILITY_KEYS.intersection(record):
            return True
    return False


def _valid_student_trajectory(record: Any) -> bool:
    if not isinstance(record, Mapping):
        return False
    if record.get("origin") != "student":
        return False
    token_ids = record.get("token_ids")
    if not isinstance(token_ids, list) or not token_ids:
        return False
    if any((not isinstance(token, int)) or isinstance(token, bool) or token < 0 for token in token_ids):
        return False
    return isinstance(record.get("step_id"), int) and not isinstance(record.get("step_id"), bool)


def _actual_student_trajectories_in_repo(repo: Path) -> List[str]:
    """Trajectory artifacts this tree can actually read. Declarations are not included."""
    del repo
    return []


def validate_distillation_input(
    payload: Any,
    repo: Optional[Path] = None,
) -> Dict[str, Any]:
    root = repo or REPO_ROOT
    if not isinstance(payload, dict):
        return _fail(
            list(REQUIRED_DISTILL_FIELDS),
            "Distillation blocked: required inputs are absent. "
            "Annotation rows and PVLP(R) chart context are not teacher probabilities.",
            root,
        )

    missing: List[str] = [key for key in REQUIRED_DISTILL_FIELDS if key not in payload]
    if missing:
        return _fail(
            missing,
            "Distillation blocked: one or more required inputs are absent.",
            root,
        )

    context = payload.get("compatible_tokenizer_vocab_context")
    student = payload.get("normalized_student_distribution")
    experts = payload.get("normalized_expert_distributions")
    model_ids = payload.get("model_ids")
    provenance = payload.get("student_trajectory_provenance")
    structural: List[str] = []
    if not isinstance(context, dict):
        structural.append("compatible_tokenizer_vocab_context")
    if not isinstance(student, dict) or not isinstance(student.get("probs"), list):
        structural.append("normalized_student_distribution")
    if not isinstance(experts, list) or not experts or not all(isinstance(item, dict) for item in experts):
        structural.append("normalized_expert_distributions")
    if not isinstance(model_ids, dict) or not str(model_ids.get("student_model_id") or "").strip():
        structural.append("model_ids")
    if not isinstance(provenance, dict):
        structural.append("student_trajectory_provenance")
    if structural:
        return _fail(structural, "Distillation blocked: required inputs are unusable.", root)

    assert isinstance(context, dict)
    assert isinstance(student, dict)
    assert isinstance(experts, list)
    assert isinstance(model_ids, dict)
    assert isinstance(provenance, dict)

    problems: List[str] = []
    if provenance.get("declarations_are_not_proof") is not True:
        problems.append("student_trajectory_provenance")
        problems.append("provenance_declarations_are_not_proof")

    if _context_records_carry_probabilities(context):
        problems.append("context_used_as_teacher_probabilities")
    if payload.get("append_expert_vocab") is True or context.get("append_expert_vocab") is True:
        problems.append("expert_vocab_axis_appended")
    if payload.get("normalize_weights") is True:
        problems.append("weights_silently_normalized_refused")

    alignment = context.get("alignment")
    if not isinstance(alignment, dict):
        problems.append("explicit_alignment")
    else:
        if alignment.get("mode") != "records_not_axes":
            problems.append("explicit_alignment")
        if alignment.get("context_axis") != "sequence":
            problems.append("explicit_alignment")
        if alignment.get("probability_axis") != "vocab":
            problems.append("explicit_alignment")
        if not isinstance(alignment.get("step_id"), int) or isinstance(alignment.get("step_id"), bool):
            problems.append("explicit_alignment")

    tokenizer_id = context.get("tokenizer_id")
    vocab_size = context.get("vocab_size")
    records = context.get("records")
    if not isinstance(tokenizer_id, str) or not tokenizer_id.strip():
        problems.append("compatible_tokenizer_vocab_context")
    if not isinstance(vocab_size, int) or isinstance(vocab_size, bool) or vocab_size <= 0:
        problems.append("compatible_tokenizer_vocab_context")
    if not isinstance(records, list) or not records:
        problems.append("compatible_tokenizer_vocab_context")

    student_model_id = str(model_ids.get("student_model_id")).strip()
    parsed_experts: List[Dict[str, Any]] = []
    deepinfer_report: Optional[Dict[str, Any]] = None
    deepinfer_frozen_specified = False
    for expert in experts:
        expert_id = expert.get("expert_id")
        if not isinstance(expert_id, str) or not expert_id.strip():
            problems.append("expert_identity_not_supplied")
            continue
        if expert_id == "DeepTutor":
            problems.append("deeptutor_is_student_role_not_a_teacher")
        elif expert_id == "DeepInfer":
            gaps, deepinfer_report = assess_deepinfer_expert(payload, expert, root)
            problems.extend(gaps)
            deepinfer_frozen_specified = bool(deepinfer_report.get("frozen_reference_specified"))
        parsed_experts.append(expert)

    on_policy = bool(payload.get("on_policy") or provenance.get("on_policy") or provenance.get("on_policy_self_report"))
    declared = provenance.get("trajectories")
    declared_ok = isinstance(declared, list) and any(_valid_student_trajectory(item) for item in declared)
    actual_paths = _actual_student_trajectories_in_repo(root)
    if on_policy:
        problems.append("actual_student_trajectories")
        if declared_ok:
            problems.append("payload_trajectory_records_are_declarations_not_proof")
        if not actual_paths:
            problems.append("no_student_trajectory_artifact_in_repository")

    self_distillation = bool(payload.get("self_distillation") or model_ids.get("self_distillation"))
    if any(isinstance(item.get("expert_id"), str) and item.get("expert_id") == student_model_id for item in parsed_experts):
        self_distillation = True
    checkpoint = payload.get("frozen_reference_checkpoint", model_ids.get("frozen_reference_checkpoint"))
    if self_distillation and not deepinfer_frozen_specified:
        if not isinstance(checkpoint, str) or not checkpoint.strip():
            problems.append("frozen_reference_checkpoint")
        elif checkpoint != CONFIGURED_GGUF_PATH:
            problems.append("frozen_reference_checkpoint_not_the_configured_model")
        elif not Path(checkpoint).is_file():
            problems.append("frozen_reference_checkpoint_not_accessible")

    if problems:
        details: Dict[str, Any] = {
            "on_policy_requested": on_policy,
            "self_distillation_requested": self_distillation,
        }
        if deepinfer_report is not None:
            details["deepinfer_teacher"] = deepinfer_report
        return _fail(
            problems,
            "Distillation input rejected before any loss was computed.",
            root,
            exit_code=EXIT_VALIDATION,
            details=details,
        )

    try:
        student_probs = _as_probs(student["probs"], "normalized_student_distribution")
    except ValueError as exc:
        code = (
            "normalized_student_distribution"
            if "normalized" in str(exc) or "non-empty" in str(exc)
            else "normalized_student_distribution"
        )
        return _fail([code], str(exc), root, exit_code=EXIT_VALIDATION)

    if vocab_size != len(student_probs):
        return _fail(
            ["probability_axis_not_vocab"],
            "Student probability length must equal vocab_size. Axes are not resized.",
            root,
            exit_code=EXIT_VALIDATION,
        )

    mask_raw = student.get("mask")
    mask: List[bool]
    if mask_raw is None:
        mask = [True] * len(student_probs)
    elif not isinstance(mask_raw, list) or len(mask_raw) != len(student_probs):
        return _fail(["mask_misaligned"], "Mask must align to the student probability axis.", root, exit_code=EXIT_VALIDATION)
    elif any(not isinstance(bit, bool) for bit in mask_raw):
        return _fail(["mask_misaligned"], "Mask values must be booleans.", root, exit_code=EXIT_VALIDATION)
    else:
        mask = list(mask_raw)
        if any((not bit) and prob != 0.0 for bit, prob in zip(mask, student_probs)):
            return _fail(
                ["mask_hides_probability_mass"],
                "Masked-out student mass must be zero. The evaluator does not renormalize.",
                root,
                exit_code=EXIT_VALIDATION,
            )

    ready_experts: List[Dict[str, Any]] = []
    for expert in parsed_experts:
        expert_id = str(expert["expert_id"])
        try:
            weight = float(expert["weight"])
        except (KeyError, TypeError, ValueError):
            return _fail(
                ["nonnegative_finite_weights"],
                f"weight for {expert_id} is missing or not a number",
                root,
                exit_code=EXIT_VALIDATION,
            )
        if (not math.isfinite(weight)) or weight < 0.0:
            return _fail(
                ["nonnegative_finite_weights"],
                f"weight for {expert_id} must be nonnegative finite",
                root,
                exit_code=EXIT_VALIDATION,
            )
        expert_probs_raw = expert.get("probs")
        if not isinstance(expert_probs_raw, list) or len(expert_probs_raw) != len(student_probs):
            return _fail(
                ["expert_vocab_axis_appended"],
                f"expert {expert_id} probability axis length {len(expert_probs_raw) if isinstance(expert_probs_raw, list) else 'invalid'} "
                f"!= student axis {len(student_probs)}. Refusing to append vocab axes.",
                root,
                exit_code=EXIT_VALIDATION,
            )
        if "mask" in expert and expert.get("mask") != mask:
            return _fail(["mask_misaligned"], f"expert {expert_id} mask is not the student mask", root, exit_code=EXIT_VALIDATION)
        try:
            expert_probs = _as_probs(expert_probs_raw, f"normalized_expert_distributions:{expert_id}")
        except ValueError as exc:
            return _fail(["normalized_expert_distributions"], str(exc), root, exit_code=EXIT_VALIDATION)
        ready_experts.append({"expert_id": expert_id, "weight": weight, "probs": expert_probs})

    declared_expert_ids = model_ids.get("expert_model_ids")
    actual_ids = [item["expert_id"] for item in ready_experts]
    if declared_expert_ids is not None and list(declared_expert_ids) != actual_ids:
        return _fail(
            ["model_ids"],
            "model_ids.expert_model_ids does not match expert_id values. No expert identity was filled in.",
            root,
            exit_code=EXIT_VALIDATION,
        )

    positions: List[int] = []
    aligned_records: List[Dict[str, Any]] = []
    step_id = alignment["step_id"]
    for record in records:
        if not isinstance(record, dict):
            return _fail(["compatible_tokenizer_vocab_context"], "context record is not an object", root, exit_code=EXIT_VALIDATION)
        position = record.get("position")
        token_id = record.get("token_id")
        if not isinstance(position, int) or isinstance(position, bool) or position < 0:
            return _fail(["explicit_alignment"], "context position must be a nonnegative integer", root, exit_code=EXIT_VALIDATION)
        if not isinstance(token_id, int) or isinstance(token_id, bool) or token_id < 0 or token_id >= vocab_size:
            return _fail(
                ["context_token_outside_vocab"],
                "context token_id is outside the declared vocab and is not a probability",
                root,
                exit_code=EXIT_VALIDATION,
            )
        if position in positions:
            return _fail(["explicit_alignment"], "duplicate context position", root, exit_code=EXIT_VALIDATION)
        positions.append(position)
        aligned_records.append(
            {
                "kind": "context",
                "position": position,
                "step_id": step_id,
                "token_id": token_id,
            }
        )
    for index, prob in enumerate(student_probs):
        aligned_records.append(
            {
                "experts": [
                    {
                        "expert_id": item["expert_id"],
                        "probability": item["probs"][index],
                        "weight": item["weight"],
                    }
                    for item in ready_experts
                ],
                "kind": "probability",
                "mask": mask[index],
                "step_id": step_id,
                "student_probability": prob,
                "vocab_index": index,
            }
        )

    try:
        numeric = weighted_reverse_kl(student_probs, ready_experts, mask)
    except ValueError as exc:
        return _fail(["normalized_expert_distributions"], str(exc), root, exit_code=EXIT_VALIDATION)

    return {
        "aligned_records": aligned_records,
        "alignment": {
            "context_axis": "sequence",
            "context_record_count": len(positions),
            "mode": "records_not_axes",
            "probability_axis": "vocab",
            "probability_axis_length": len(student_probs),
            "step_id": step_id,
        },
        "distributions_are_caller_supplied": True,
        "evaluator_only": True,
        "exit_code": EXIT_OK,
        "input_label": payload.get("label"),
        "kaggle_interaction": False,
        "message": "OPD reverse-KL reference evaluation completed. Evaluator only; not training.",
        "missing_prerequisites": [],
        "model_file_opened": False,
        "model_identity_verified": False,
        "nominal_student_not_loaded": NOMINAL_STUDENT,
        "not_training": True,
        "numeric": numeric,
        "ok": True,
        "on_policy_accepted": False,
        "on_policy_requested": False,
        "production_model_used": False,
        "provenance_declarations_are_not_proof": True,
        "quality_claim": False,
        "repository_components": repository_components(root),
        "stage": "distillation_opd",
        "student_roles_not_teachers": sorted(STUDENT_ROLE_NAMES),
        "synthetic_test_only": payload.get("synthetic_test_only") is True,
        "training_executed": False,
        "weights_loaded": False,
    }


def run_probe(repo: Path = REPO_ROOT) -> Dict[str, Any]:
    index = build_neuron_index(repo)
    resource = repo / "src" / "main" / "resources" / "connectome" / "neuron_index.json"
    resource_index = json.loads(resource.read_text(encoding="utf-8")) if resource.is_file() else None
    yaml_path = repo / "docs" / "hhmi_jenalia.yaml"
    pom_path = repo / "docs" / "hhmi_jenalia.pom"
    checksum_problems = verify_included_checksums(repo)
    blocked = validate_distillation_input(None, repo)
    fixture_path = repo / "tests" / "fixtures" / "cb2514_synthetic_opd_payload.json"
    synthetic = None
    if fixture_path.is_file():
        synthetic = validate_distillation_input(json.loads(fixture_path.read_text(encoding="utf-8")), repo)
    wiring_ok = (
        not checksum_problems
        and resource_index == index
        and index["bodyIds"] == [60536, 64328, 124180, 125402, 167164]
        and index["laterality"] == {"L": 3, "R": 2}
        and index["edges_included"] is False
        and yaml_path.is_file()
        and yaml_path.name == "hhmi_jenalia.yaml"
        and not pom_path.exists()
        and blocked["ok"] is False
        and blocked["missing_prerequisites"] == list(REQUIRED_DISTILL_FIELDS)
        and synthetic is not None
        and synthetic["ok"] is True
        and synthetic["synthetic_test_only"] is True
        and synthetic["on_policy_accepted"] is False
        and synthetic["training_executed"] is False
    )
    return {
        "execution": {
            "connectome_simulation": "not_executed",
            "distillation_training": "not_executed",
            "java_maven": "not_run_by_this_probe",
            "metadata_wiring": "executed" if wiring_ok else "failed",
            "model_inference": "not_executed",
            "numeric_evaluator_on_synthetic_fixture": "executed" if synthetic and synthetic.get("ok") else "failed",
            "teavm_runtime": "not_run_by_this_probe",
        },
        "exit_code": 0 if wiring_ok else EXIT_VALIDATION,
        "hhmi_jenalia_pom_fabricated": pom_path.exists(),
        "hhmi_jenalia_yaml": str(yaml_path.relative_to(repo)) if yaml_path.is_file() else None,
        "included_checksum_problems": checksum_problems,
        "missing_when_distillation_unspecified": blocked["missing_prerequisites"],
        "neuron_index_bodyIds": index["bodyIds"],
        "neuron_index_edges_included": index["edges_included"],
        "neuron_index_resource": "src/main/resources/connectome/neuron_index.json",
        "ok": wiring_ok,
        "omitted_source_count": len(omitted_source_records(repo)),
        "probe": "cb2514_opd_one_pass",
        "repository_components": repository_components(repo),
        "roi_display": build_roi_context(repo)["display"],
        "roi_membership_unverified": True,
        "synthetic_loss": None if not synthetic else synthetic["numeric"]["loss"],
        "synthetic_on_policy_accepted": None if not synthetic else synthetic["on_policy_accepted"],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="CB2514 metadata probe and distillation-input gate")
    parser.add_argument("--probe", action="store_true", help="run the one-pass wiring probe")
    parser.add_argument("--emit", action="store_true", help="rewrite derived JSON resources from the CSV")
    parser.add_argument("--validate", type=Path, help="validate a distillation payload JSON file")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT)
    args = parser.parse_args(list(argv) if argv is not None else None)
    repo = args.repo.resolve()
    if args.emit:
        emit_tree(repo)
    if args.validate is not None:
        payload = json.loads(args.validate.read_text(encoding="utf-8"))
        report = validate_distillation_input(payload, repo)
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return int(report["exit_code"])
    if args.probe or not args.emit:
        report = run_probe(repo)
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return int(report["exit_code"])
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
