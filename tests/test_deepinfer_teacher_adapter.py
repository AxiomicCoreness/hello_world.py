# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""DeepInfer does not supply a full-vocabulary teacher distribution.

Synthetic captures are labeled and are not treated as sampler output.
"""
from __future__ import annotations

import json
from pathlib import Path

import deepinfer_teacher_adapter as adapter
import cb2514_opd as opd

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "cb2514_synthetic_opd_payload.json"


def _payload() -> dict:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["normalized_expert_distributions"] = [
        {"expert_id": "DeepInfer", "weight": 1.0, "probs": [0.5, 0.5]}
    ]
    return data


def test_probe_reads_real_sources_and_does_not_run_inference():
    report = adapter.capability_report(REPO)
    assert report["inference_launched"] is False
    assert report["model_download_attempted"] is False
    assert report["supplies_full_vocab_normalized_distribution"] is False
    assert report["softmax_of_truncated_candidates"] is False
    assert report["logprobs_argument_ignored"] is True
    assert all(item["needle_present"] for item in report["sources"])
    missing = report["missing_prerequisites"]
    assert "deepinfer_full_vocab_logits" in missing
    assert "deepinfer_normalized_next_token_distribution" in missing
    assert "tokenizer_vocab_and_merges" in missing
    assert "aligned_full_vocabulary" in missing


def test_qwen2_metadata_is_not_renamed_or_used_as_vocab():
    meta = adapter.tokenizer_metadata_report(REPO)
    assert meta["tokenizer_class"] == "Qwen2Tokenizer"
    assert meta["eos_token"] == "<|im_end|>"
    assert meta["pad_token"] == "<|endoftext|>"
    assert meta["bos_token"] is None
    assert meta["added_token_id_min"] == 151643
    assert meta["added_token_id_max"] == 151664
    assert meta["has_vocab"] is False
    assert meta["has_merges"] is False
    assert meta["has_chat_template"] is False
    assert meta["class_renamed_to_deepseek"] is False
    assert meta["exact_gguf_match_assumed"] is False
    assert meta["compatible_with_deepinfer_release_fixups"] is False
    assert meta["fills_compatible_tokenizer_vocab_context"] is False


def test_topk_and_generated_text_are_not_softmaxed_into_a_distribution():
    payload = _payload()
    payload["frozen_reference_checkpoint"] = "/tmp/frozen-deepinfer-hf"
    payload["normalized_expert_distributions"][0]["deepinfer_capture"] = {
        "kind": "top_k_logprobs",
        "top_logprobs": [{"id": 1, "logprob": -0.1}, {"id": 2, "logprob": -2.0}],
    }
    report = opd.validate_distillation_input(payload, REPO)
    assert report["ok"] is False
    assert "truncated_logprobs_are_not_full_distribution" in report["missing_prerequisites"]
    assert "deepinfer_alias_requires_frozen_reference" not in report["missing_prerequisites"]
    assert "numeric" not in report
    text = _payload()
    text["frozen_reference_checkpoint"] = "/tmp/frozen-deepinfer-hf"
    text["normalized_expert_distributions"][0]["deepinfer_capture"] = {
        "kind": "generated_text",
        "text": "hello",
    }
    text_report = opd.validate_distillation_input(text, REPO)
    assert "truncated_logprobs_are_not_full_distribution" in text_report["missing_prerequisites"]


def test_specified_frozen_reference_does_not_reject_the_alias():
    payload = _payload()
    payload["student_model_id"] = "DeepInfer"
    payload["model_ids"]["student_model_id"] = "DeepInfer"
    payload["frozen_reference_checkpoint"] = "/checkpoints/DeepSeek-V4.1-Flash-frozen"
    payload["self_distillation"] = True
    report = opd.validate_distillation_input(payload, REPO)
    assert "deepinfer_alias_requires_frozen_reference" not in report["missing_prerequisites"]
    assert "deeptutor_is_student_role_not_a_teacher" not in report["missing_prerequisites"]
    assert "frozen_reference_checkpoint_not_the_configured_model" not in report["missing_prerequisites"]
    assert "deepinfer_full_vocab_logits" in report["missing_prerequisites"]
    assert "frozen_reference_checkpoint_not_accessible" in report["missing_prerequisites"]
    teacher = report["details"]["deepinfer_teacher"]
    assert teacher["alias_unconditionally_rejected"] is False
    assert teacher["frozen_reference_specified"] is True
    assert teacher["teacher_probabilities_returned"] is False


def test_gguf_path_is_not_a_deepinfer_loader_even_when_named():
    payload = _payload()
    payload["frozen_reference_checkpoint"] = opd.CONFIGURED_GGUF_PATH
    report = opd.validate_distillation_input(payload, REPO)
    assert "deepinfer_has_no_gguf_loader" in report["missing_prerequisites"]
    assert "deepinfer_alias_requires_frozen_reference" not in report["missing_prerequisites"]
    assert report["details"]["deepinfer_teacher"]["gguf_loader"] is False


def test_synthetic_full_vector_is_not_actual_deepinfer_output():
    payload = _payload()
    payload["frozen_reference_checkpoint"] = "/checkpoints/DeepSeek-V4.1-Flash-frozen"
    payload["normalized_expert_distributions"][0]["deepinfer_capture"] = {
        "kind": "full_vocab_normalized",
        "synthetic_test_only": True,
        "probs": [0.5, 0.5],
    }
    report = opd.validate_distillation_input(payload, REPO)
    assert "synthetic_capture_is_not_actual_deepinfer_output" in report["missing_prerequisites"]
    assert report["ok"] is False
    assert "numeric" not in report
