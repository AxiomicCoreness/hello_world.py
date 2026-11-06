# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""CB2514 metadata wiring and fail-closed distillation-input checks.

Synthetic probability fixtures are labeled synthetic_test_only. They are not
biological connectivity and not model-quality measurements.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

import cb2514_opd as opd

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "cb2514_synthetic_opd_payload.json"


def _payload() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_included_source_checksums_match_preserved_records():
    assert opd.verify_included_checksums(REPO) == []
    omitted = opd.omitted_source_records(REPO)
    assert len(omitted) == 8
    for rec in omitted:
        assert rec["checksum_recomputed"] is False
        assert not (opd.source_root(REPO) / rec["path"]).exists()
        assert rec["sha256"]
        assert rec["url"]


def test_neuron_index_resource_matches_csv_and_has_no_edges():
    index = opd.build_neuron_index(REPO)
    resource = json.loads(
        (REPO / "src/main/resources/connectome/neuron_index.json").read_text(encoding="utf-8")
    )
    assert resource == index
    assert index["bodyIds"] == [60536, 64328, 124180, 125402, 167164]
    assert index["laterality"] == {"L": 3, "R": 2}
    assert index["edges_included"] is False
    assert index["missing_skeletons"] == index["bodyIds"]
    assert all(neuron["skeleton_present"] is False for neuron in index["neurons"])
    roi = json.loads(
        (REPO / "src/main/resources/connectome/roi_context_PVLP_R.json").read_text(encoding="utf-8")
    )
    assert roi["display"] == "PVLP(R)"
    assert roi["chart_membership_unverified"] is True
    assert roi["edges_inferred_from_charts"] is False
    schema = json.loads(
        (REPO / "src/main/resources/connectome/connectivity_edge_schema.json").read_text(encoding="utf-8")
    )
    assert schema["edges_in_tree"] is False
    assert (REPO / "docs/hhmi_jenalia.yaml").is_file()
    assert not (REPO / "docs/hhmi_jenalia.pom").exists()


def test_configured_model_path_is_not_opened():
    components = opd.repository_components(REPO)
    assert components["configured_gguf_path"] == opd.CONFIGURED_GGUF_PATH
    assert components["configured_gguf_accessible"] is False
    assert components["model_file_opened"] is False
    assert components["model_download_attempted"] is False
    assert components["kaggle_interaction"] is False
    assert components["training_launched"] is False
    assert components["satisfied_prerequisites"] == []
    for record in components["components"].values():
        assert record["present"] is True
        assert record["satisfies_distillation_prerequisite"] is False


def test_missing_payload_lists_the_five_prerequisites():
    report = opd.validate_distillation_input(None, REPO)
    assert report["ok"] is False
    assert report["exit_code"] == opd.EXIT_BLOCKED_DISTILLATION
    assert report["missing_prerequisites"] == list(opd.REQUIRED_DISTILL_FIELDS)
    assert report["training_executed"] is False
    assert report["on_policy_accepted"] is False
    assert "numeric" not in report


@pytest.mark.parametrize("field", opd.REQUIRED_DISTILL_FIELDS)
def test_each_required_field_is_named_when_absent(field):
    payload = _payload()
    del payload[field]
    report = opd.validate_distillation_input(payload, REPO)
    assert report["ok"] is False
    assert field in report["missing_prerequisites"]
    assert report["training_executed"] is False


def test_synthetic_fixture_evaluates_reverse_kl_without_training():
    report = opd.validate_distillation_input(_payload(), REPO)
    assert report["ok"] is True
    assert report["exit_code"] == 0
    assert report["synthetic_test_only"] is True
    assert report["training_executed"] is False
    assert report["weights_loaded"] is False
    assert report["on_policy_accepted"] is False
    assert report["quality_claim"] is False
    assert report["production_model_used"] is False
    numeric = report["numeric"]
    assert numeric["formula"] == "sum_i w_i KL(student||expert_i)"
    assert numeric["weights_normalized_by_evaluator"] is False
    assert numeric["weight_sum"] == pytest.approx(1.5)
    student = [0.5, 0.5]
    expert_b = [0.9, 0.1]
    expected = 0.5 * opd.kl_student_expert(student, expert_b)
    assert numeric["loss"] == pytest.approx(expected)
    kinds = [record["kind"] for record in report["aligned_records"]]
    assert kinds[:2] == ["context", "context"]
    assert kinds[2:] == ["probability", "probability"]
    assert report["alignment"]["context_record_count"] == 2
    assert report["alignment"]["probability_axis_length"] == 2
    assert all(record.get("token_id") != record.get("student_probability") for record in report["aligned_records"])


def test_weights_are_not_silently_normalized_and_must_be_finite():
    payload = _payload()
    payload["normalize_weights"] = True
    refused = opd.validate_distillation_input(payload, REPO)
    assert "weights_silently_normalized_refused" in refused["missing_prerequisites"]
    payload = _payload()
    payload["normalized_expert_distributions"][0]["weight"] = -1
    negative = opd.validate_distillation_input(payload, REPO)
    assert negative["ok"] is False
    assert "nonnegative_finite_weights" in negative["missing_prerequisites"]


def test_unnormalized_student_is_rejected():
    payload = _payload()
    payload["normalized_student_distribution"]["probs"] = [0.2, 0.2]
    payload["compatible_tokenizer_vocab_context"]["vocab_size"] = 2
    report = opd.validate_distillation_input(payload, REPO)
    assert report["ok"] is False
    assert "normalized_student_distribution" in report["missing_prerequisites"]


def test_context_is_not_treated_as_teacher_probabilities():
    payload = _payload()
    payload["compatible_tokenizer_vocab_context"]["probs"] = [0.5, 0.5]
    report = opd.validate_distillation_input(payload, REPO)
    assert "context_used_as_teacher_probabilities" in report["missing_prerequisites"]
    assert "numeric" not in report


def test_expert_vocab_axis_is_not_appended():
    payload = _payload()
    payload["normalized_expert_distributions"][0]["probs"] = [0.25, 0.25, 0.25, 0.25]
    report = opd.validate_distillation_input(payload, REPO)
    assert "expert_vocab_axis_appended" in report["missing_prerequisites"]
    payload = _payload()
    payload["append_expert_vocab"] = True
    flagged = opd.validate_distillation_input(payload, REPO)
    assert "expert_vocab_axis_appended" in flagged["missing_prerequisites"]


def test_mask_must_align_and_must_not_hide_mass():
    payload = _payload()
    payload["normalized_student_distribution"]["mask"] = [True]
    short = opd.validate_distillation_input(payload, REPO)
    assert "mask_misaligned" in short["missing_prerequisites"]
    payload = _payload()
    payload["normalized_student_distribution"]["probs"] = [0.4, 0.6]
    payload["normalized_student_distribution"]["mask"] = [True, False]
    hidden = opd.validate_distillation_input(payload, REPO)
    assert "mask_hides_probability_mass" in hidden["missing_prerequisites"]


def test_zero_support_is_infinite_kl_not_a_renormalized_number():
    student = [1.0, 0.0]
    expert = [0.0, 1.0]
    assert math.isinf(opd.kl_student_expert(student, expert))
    assert opd.kl_student_expert([0.25, 0.75], [0.25, 0.75]) == pytest.approx(0.0)
    left = opd.kl_student_expert([0.7, 0.2, 0.1], [0.2, 0.5, 0.3])
    right = opd.kl_student_expert([0.2, 0.5, 0.3], [0.7, 0.2, 0.1])
    assert left != pytest.approx(right)


def test_deepinfer_and_deeptutor_are_not_two_teachers():
    payload = _payload()
    payload["normalized_expert_distributions"] = [
        {"expert_id": "DeepInfer", "weight": 1.0, "probs": [0.5, 0.5]},
        {"expert_id": "DeepTutor", "weight": 1.0, "probs": [0.5, 0.5]},
    ]
    report = opd.validate_distillation_input(payload, REPO)
    assert "deeptutor_is_student_role_not_a_teacher" in report["missing_prerequisites"]
    assert "deepinfer_alias_requires_frozen_reference" in report["missing_prerequisites"]
    assert "deepinfer_deeptutor_are_student_roles_not_two_teachers" not in report["missing_prerequisites"]
    assert report["on_policy_accepted"] is False
    assert report["details"]["deepinfer_teacher"]["teacher_probabilities_returned"] is False


def test_on_policy_declaration_is_not_proof():
    payload = _payload()
    payload["on_policy"] = True
    payload["student_trajectory_provenance"]["trajectories"] = [
        {"origin": "student", "step_id": 0, "token_ids": [1, 0], "claim": "on_policy"}
    ]
    report = opd.validate_distillation_input(payload, REPO)
    assert report["ok"] is False
    assert "actual_student_trajectories" in report["missing_prerequisites"]
    assert "payload_trajectory_records_are_declarations_not_proof" in report["missing_prerequisites"]
    assert "no_student_trajectory_artifact_in_repository" in report["missing_prerequisites"]
    assert "numeric" not in report


def test_self_distillation_requires_the_inaccessible_configured_checkpoint():
    payload = _payload()
    payload["self_distillation"] = True
    missing = opd.validate_distillation_input(payload, REPO)
    assert "frozen_reference_checkpoint" in missing["missing_prerequisites"]
    payload["frozen_reference_checkpoint"] = str(REPO / "data/cb2514/dataset.json")
    other = opd.validate_distillation_input(payload, REPO)
    assert "frozen_reference_checkpoint_not_the_configured_model" in other["missing_prerequisites"]
    payload["frozen_reference_checkpoint"] = opd.CONFIGURED_GGUF_PATH
    configured = opd.validate_distillation_input(payload, REPO)
    assert "frozen_reference_checkpoint_not_accessible" in configured["missing_prerequisites"]
    assert configured["repository_components"]["model_file_opened"] is False


def test_blank_expert_id_is_not_invented():
    payload = _payload()
    payload["normalized_expert_distributions"][0]["expert_id"] = ""
    report = opd.validate_distillation_input(payload, REPO)
    assert "expert_identity_not_supplied" in report["missing_prerequisites"]


def test_explicit_alignment_is_required():
    payload = _payload()
    del payload["compatible_tokenizer_vocab_context"]["alignment"]
    report = opd.validate_distillation_input(payload, REPO)
    assert "explicit_alignment" in report["missing_prerequisites"]


def test_probe_distinguishes_wiring_from_training():
    report = opd.run_probe(REPO)
    assert report["ok"] is True
    assert report["execution"]["metadata_wiring"] == "executed"
    assert report["execution"]["distillation_training"] == "not_executed"
    assert report["execution"]["model_inference"] == "not_executed"
    assert report["execution"]["java_maven"] == "not_run_by_this_probe"
    assert report["execution"]["teavm_runtime"] == "not_run_by_this_probe"
    assert report["hhmi_jenalia_pom_fabricated"] is False


def test_hello_world_exposes_the_validator_without_loading_weights():
    fastapi = pytest.importorskip("fastapi")
    del fastapi
    from fastapi.testclient import TestClient
    import hello_world

    assert hello_world.validate_distillation_input is opd.validate_distillation_input
    client = TestClient(hello_world.app)
    response = client.post("/deepseek/distill/validate", json={"payload": None})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["missing_prerequisites"] == list(opd.REQUIRED_DISTILL_FIELDS)
    assert body["training_executed"] is False
    assert body["model_file_opened"] is False


def test_copy_does_not_alias_fixture_mutations():
    original = _payload()
    mutated = copy.deepcopy(original)
    mutated["normalized_student_distribution"]["probs"][0] = 0.0
    assert original["normalized_student_distribution"]["probs"][0] == 0.5
