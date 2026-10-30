# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Math-delimiter normalisation and thinking split for saved replies (pure, offline)."""
from __future__ import annotations

import pytest

from src import llm_markdown as md

N = md.normalize_math


@pytest.mark.parametrize("src,want", [
    (r"inline $a^2+b^2=c^2$ here", r"inline \(a^2+b^2=c^2\) here"),
    (r"inline \( x \) kept", r"inline \(x\) kept"),
    (r"display \[ \int_0^1 x\,dx \] done", r"display $$\int_0^1 x\,dx$$ done"),
    (r"display $$ e^{i\pi}+1=0 $$", r"display $$e^{i\pi}+1=0$$"),
    ("multi\n\\[\na=b\\\\\nc=d\n\\]\n", "multi\n$$a=b\\\\\nc=d$$\n"),
    ("two $x$ and $y$.", r"two \(x\) and \(y\)."),
])
def test_delimiters_normalised(src, want):
    assert N(src) == want
    assert N(want) == want  # fixed point


@pytest.mark.parametrize("text", [
    "costs $5 and $10 today",
    "range $1 to $2 million",
    "split $5/$10",
    r"escaped \$x\$ stays",
    "no math at all",
    "",
])
def test_non_math_dollars_untouched(text):
    assert N(text) == text


def test_code_spans_and_fences_never_touched():
    text = ("use `$x$` and ``\\(y\\)`` inline, but $z$ outside\n"
            "```latex\n$a$ \\[b\\] $$c$$\n```\n"
            "~~~~\n\\(d\\)\n~~~~\n"
            "after $w$")
    assert N(text) == ("use `$x$` and ``\\(y\\)`` inline, but \\(z\\) outside\n"
                       "```latex\n$a$ \\[b\\] $$c$$\n```\n"
                       "~~~~\n\\(d\\)\n~~~~\n"
                       "after \\(w\\)")


def test_unclosed_fence_stays_code():
    text = "ok $a$\n```\n$b$ never closed"
    assert N(text) == "ok \\(a\\)\n```\n$b$ never closed"


@pytest.mark.parametrize("reply,answer,thinking", [
    ("<think>plan</think>Answer", "Answer", "plan"),
    ("plan only</think>\nAnswer", "Answer", "plan only"),
    ("Answer <think>unclosed", "Answer", "unclosed"),
    ("No reasoning.", "No reasoning.", ""),
])
def test_split_thinking(reply, answer, thinking):
    assert md.split_thinking(reply) == (answer, thinking)


def test_markdown_entry_and_read_entry():
    e = md.markdown_entry("so $x$", "think $y$")
    assert e == {"content": "so \\(x\\)", "format": "markdown", "thinking": "think \\(y\\)"}
    assert md.markdown_entry("  ", "") == {"content": "(empty reply)", "format": "markdown"}
    assert md.read_entry({"role": "assistant", "content": "x"})["format"] == "plain"
    assert md.read_entry({"role": "assistant", "content": "x", "format": "html"})["format"] == "plain"
    v = md.read_entry({"role": "assistant", "content": "x", "format": "markdown", "thinking": "t"})
    assert v["format"] == "markdown" and v["thinking"] == "t"
