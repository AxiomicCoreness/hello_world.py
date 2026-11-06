#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Static DeepInfer teacher-distribution capability probe.

DeepInfer is not asked to run. This module does not download weights, open a
GGUF, softmax a top-k list, or rename Qwen2Tokenizer to a DeepSeek class.

The vendored sampler returns the sampled token's logprob and a top-k table
(at most 1000 entries). SamplingParams.logprobs is deleted. That is not a
normalized distribution over a full aligned vocabulary.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent
TOKENIZER_METADATA = Path("data/cb2514/qwen2_tokenizer_config_metadata.json")

# Facts read from the tree. Each needle must stay present in the cited file.
SOURCE_FACTS = (
    {
        "path": "core/sampling_params.py",
        "needle": "del logprobs",
        "fact": "SamplingParams deletes the logprobs argument. It is not returned.",
    },
    {
        "path": "core/sampling_params.py",
        "needle": "top_logprobs must be in [0, 1000]",
        "fact": "top_logprobs is capped at 1000 tokens, not the model vocabulary.",
    },
    {
        "path": "deepinfer/sequence.py",
        "needle": "PromptLogprobs = list[float]",
        "fact": "PromptLogprobs is a list of floats, not a per-position vocabulary vector.",
    },
    {
        "path": "deepinfer/sequence.py",
        "needle": "shape: [num_token, topk]",
        "fact": "Sampler top-k tables are [num_token, topk] logps and token ids.",
    },
    {
        "path": "deepinfer/sequence.py",
        "needle": "sum_smaller_probs",
        "fact": "sum_smaller_probs is the mass outside the top-k, not the omitted logits.",
    },
    {
        "path": "deepinfer/hugging_face/tokenizer.py",
        "needle": "expected <｜begin▁of▁sentence｜> at id 0",
        "fact": "DeepInfer's HF tokenizer fixup requires DeepSeek BOS id 0, EOS id 1, and PAD id 2.",
    },
    {
        "path": "engine/deepinfer_accelerator.py",
        "needle": "needs_runtime",
        "fact": "engine.deepinfer_accelerator.complete returns text or a readiness probe, not logits.",
    },
    {
        "path": "docs/DEEPINFER_8090_RUNBOOK.md",
        "needle": "no GGUF loader",
        "fact": "DeepInfer builds DeepSeek-V4.1 from a Hugging Face checkpoint. It has no GGUF loader.",
    },
)

TRUNCATED_KINDS = frozenset(
    {"generated_text", "top_k_logprobs", "top_logprobs", "token_logprobs", "prompt_logprobs"}
)

EXIT_BLOCKED = 30


def _read(repo: Path, rel: str) -> str:
    path = repo / rel
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def tokenizer_metadata_report(repo: Path = REPO_ROOT) -> Dict[str, Any]:
    path = repo / TOKENIZER_METADATA
    if not path.is_file():
        return {
            "present": False,
            "path": TOKENIZER_METADATA.as_posix(),
            "fills_compatible_tokenizer_vocab_context": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    added = data.get("added_tokens_decoder") or {}
    ids = sorted(int(k) for k in added) if isinstance(added, dict) else []
    return {
        "present": True,
        "path": TOKENIZER_METADATA.as_posix(),
        "tokenizer_class": data.get("tokenizer_class"),
        "eos_token": data.get("eos_token"),
        "pad_token": data.get("pad_token"),
        "bos_token": data.get("bos_token"),
        "added_token_id_min": ids[0] if ids else None,
        "added_token_id_max": ids[-1] if ids else None,
        "added_token_count": len(ids),
        "has_vocab": "vocab" in data or "vocab_size" in data,
        "has_merges": "merges" in data,
        "has_chat_template": "chat_template" in data,
        "class_renamed_to_deepseek": False,
        "exact_gguf_match_assumed": False,
        "fills_compatible_tokenizer_vocab_context": False,
        "compatible_with_deepinfer_release_fixups": False,
        "why_not_adjusted_into_deepinfer_probabilities": (
            "This file is Qwen2Tokenizer metadata: EOS <|im_end|>, PAD <|endoftext|>, "
            "BOS null, added ids 151643-151664, and no vocab, merges, or chat template. "
            "DeepInfer's tokenizer fixup requires a different special-token layout "
            "(BOS id 0, EOS id 1, PAD id 2). The class is not renamed, and the metadata "
            "is not a next-token distribution."
        ),
    }


def capability_report(repo: Path = REPO_ROOT) -> Dict[str, Any]:
    sources: List[Dict[str, Any]] = []
    missing: List[str] = []
    for item in SOURCE_FACTS:
        text = _read(repo, item["path"])
        present = bool(text) and item["needle"] in text
        sources.append(
            {
                "path": item["path"],
                "fact": item["fact"],
                "needle_present": present,
            }
        )
        if not present:
            missing.append(f"source_fact_missing:{item['path']}")
    tokenizer = tokenizer_metadata_report(repo)
    if not tokenizer.get("fills_compatible_tokenizer_vocab_context"):
        missing.extend(
            [
                "tokenizer_vocab_and_merges",
                "aligned_full_vocabulary",
            ]
        )
    missing.extend(
        [
            "deepinfer_full_vocab_logits",
            "deepinfer_normalized_next_token_distribution",
            "context_token_mask_alignment_from_deepinfer",
            "deepinfer_frozen_hf_checkpoint_weights",
        ]
    )
    # Preserve order while dropping duplicates.
    missing = list(dict.fromkeys(missing))
    return {
        "provider": "deepinfer",
        "inference_launched": False,
        "model_download_attempted": False,
        "kaggle_interaction": False,
        "service_mutated": False,
        "supplies_full_vocab_normalized_distribution": False,
        "supplies_generated_text": True,
        "supplies_sampled_token_logprob": True,
        "supplies_top_k_logprobs_at_most_1000": True,
        "logprobs_argument_ignored": True,
        "softmax_of_truncated_candidates": False,
        "student_model_identity": "DeepSeek-R1-Distill-1.5B",
        "deepinfer_checkpoint_family": "DeepSeek-V4.1 Hugging Face",
        "gguf_loader": False,
        "tokenizer_metadata": tokenizer,
        "sources": sources,
        "missing_prerequisites": missing,
        "ok": False,
        "exit_code": EXIT_BLOCKED,
    }


def _frozen_reference(payload: Dict[str, Any]) -> Optional[str]:
    model_ids = payload.get("model_ids") if isinstance(payload.get("model_ids"), dict) else {}
    raw = payload.get("frozen_reference_checkpoint", model_ids.get("frozen_reference_checkpoint"))
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _capture_of(payload: Dict[str, Any], expert: Dict[str, Any]) -> Any:
    if "deepinfer_capture" in expert:
        return expert.get("deepinfer_capture")
    return payload.get("deepinfer_capture")


def assess_deepinfer_expert(
    payload: Dict[str, Any],
    expert: Dict[str, Any],
    repo: Path = REPO_ROOT,
) -> Tuple[List[str], Dict[str, Any]]:
    """Decide whether a DeepInfer expert alias may be used. Never emits logits."""
    report = capability_report(repo)
    missing: List[str] = []
    frozen = _frozen_reference(payload)
    report["frozen_reference_specified"] = frozen is not None
    report["frozen_reference_checkpoint"] = frozen
    report["alias_unconditionally_rejected"] = False
    if frozen is None:
        missing.append("frozen_reference_checkpoint")
        missing.append("deepinfer_alias_requires_frozen_reference")
    else:
        path = Path(frozen)
        report["frozen_reference_is_file"] = path.is_file()
        report["frozen_reference_is_dir"] = path.is_dir()
        if frozen.endswith(".gguf") or "gguf" in frozen.lower():
            missing.append("deepinfer_has_no_gguf_loader")
        if not path.exists():
            missing.append("frozen_reference_checkpoint_not_accessible")
    capture = _capture_of(payload, expert)
    report["capture_kind"] = None if not isinstance(capture, dict) else capture.get("kind")
    if not isinstance(capture, dict):
        missing.append("deepinfer_full_vocab_logits")
        missing.append("deepinfer_normalized_next_token_distribution")
    else:
        kind = capture.get("kind")
        if kind in TRUNCATED_KINDS or capture.get("truncated") is True:
            missing.append("truncated_logprobs_are_not_full_distribution")
        elif capture.get("synthetic_test_only") is True:
            missing.append("synthetic_capture_is_not_actual_deepinfer_output")
        elif kind == "full_vocab_normalized":
            missing.append("caller_vector_is_not_deepinfer_sampler_output")
        else:
            missing.append("deepinfer_full_vocab_logits")
            missing.append("deepinfer_normalized_next_token_distribution")
    # The static API never supplies the distribution, even when a checkpoint id is named.
    if "deepinfer_full_vocab_logits" not in missing and "truncated_logprobs_are_not_full_distribution" not in missing:
        missing.append("deepinfer_full_vocab_logits")
    report["missing_for_this_expert"] = list(dict.fromkeys(missing))
    report["teacher_probabilities_returned"] = False
    return report["missing_for_this_expert"], report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Probe DeepInfer teacher-distribution capability")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    report = capability_report(args.repo.resolve())
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
