# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""training/lessons/*.jsonl must match the deepseek-r2 tutor's chat format.

Stdlib json only; runs under `python -I -m pytest`. The tutor's train.jsonl
lives outside the repo, so its line-1 system prompt is pinned by sha256 here and
also compared directly when the file is present ($TUTOR_TRAIN_JSONL, default
/workspace/llama/deepseek-r2/train.jsonl).
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LESSON_FILES = [
    ROOT / "training" / "lessons" / "2026-10-30-ci-lessons.jsonl",
    ROOT / "training" / "lessons" / "2026-10-30-ledger-dynamics.jsonl",
]
SYSTEM_SHA256 = "fd9bc622da1f799f62d483422c83a35de9a102a754f46e3b6151a4febb528fbe"
TRAIN = Path(os.environ.get("TUTOR_TRAIN_JSONL", "/workspace/llama/deepseek-r2/train.jsonl"))


def _rows(lessons):
    lines = lessons.read_text(encoding="utf-8").splitlines()
    assert lines, "lesson file is empty"
    return [json.loads(line) for line in lines]


@pytest.mark.parametrize("lessons", LESSON_FILES, ids=lambda p: p.name)
def test_every_line_is_system_user_assistant(lessons):
    rows = _rows(lessons)
    assert 20 <= len(rows) <= 30
    for i, row in enumerate(rows, 1):
        msgs = row["messages"]
        assert [m["role"] for m in msgs] == ["system", "user", "assistant"], i
        assert all(isinstance(m["content"], str) and m["content"].strip() for m in msgs), i


@pytest.mark.parametrize("lessons", LESSON_FILES, ids=lambda p: p.name)
def test_system_prompt_is_the_tutors_line_1_prompt(lessons):
    for row in _rows(lessons):
        got = hashlib.sha256(row["messages"][0]["content"].encode("utf-8")).hexdigest()
        assert got == SYSTEM_SHA256


@pytest.mark.parametrize("lessons", LESSON_FILES, ids=lambda p: p.name)
def test_system_prompt_matches_train_jsonl_when_present(lessons):
    if not TRAIN.is_file():
        pytest.skip(f"{TRAIN} not on this machine; sha256 pin above still checked")
    with TRAIN.open(encoding="utf-8") as fh:
        want = json.loads(fh.readline())["messages"][0]["content"]
    assert {r["messages"][0]["content"] for r in _rows(lessons)} == {want}


def test_ledger_lessons_cite_existing_sources_on_main():
    rows = _rows(LESSON_FILES[1])
    for i, row in enumerate(rows, 1):
        meta = row["meta"]
        assert meta["example_type"] == "ledger_lesson", i
        assert len(meta["commit"]) == 40, i
        for rel in meta["path"].split(","):
            assert (ROOT / rel).exists(), (i, rel)
