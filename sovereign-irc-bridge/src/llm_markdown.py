# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Markdown + LaTeX shape for saved ``/llm`` assistant replies.

New assistant rows in ``llm_history.jsonl`` carry ``"format": "markdown"``:
``content`` is the answer as Markdown, with math normalised to the two
delimiter pairs the TeaVM page (KaTeX auto-render) and the iOS app render:

* inline  ``\\( … \\)``   (from ``\\( … \\)`` or ``$ … $``)
* display ``$$ … $$``     (from ``\\[ … \\]`` or ``$$ … $$``)

Math inside inline code spans and fenced code blocks is never touched.
Reasoning moves out of ``content`` into a separate ``thinking`` field (also
Markdown). Rows without ``format`` are legacy and read as ``plain``.

Pure functions, stdlib only, no I/O.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Final, List, Optional, Tuple

FORMAT_MARKDOWN: Final = "markdown"
FORMAT_PLAIN: Final = "plain"
KNOWN_FORMATS: Final = frozenset({FORMAT_MARKDOWN, FORMAT_PLAIN})

# Appended to both system prompts so the model writes math the renderers expect.
MATH_PROMPT: Final = (
    "Format your answer as Markdown. Write all math in LaTeX: inline math as \\( ... \\) "
    "and display math as $$ ... $$ on its own line. Do not put math in code blocks."
)

# A fence opener: up to 3 spaces, then >=3 backticks or >=3 tildes.
_FENCE_RE: Final = re.compile(r"^( {0,3})(`{3,}|~{3,})")

# Prose math, tried left to right at each position. Order matters: $$ before $.
_MATH_RE: Final = re.compile(
    r"(?P<esc>\\\$)"                                   # \$ is a literal dollar
    r"|\$\$(?P<dd>.+?)\$\$"                            # $$ display $$
    r"|\\\[(?P<bd>.+?)\\\]"                            # \[ display \]
    r"|\\\((?P<bi>.+?)\\\)"                            # \( inline \)
    r"|(?<![\\$\w])\$(?=[^\s$])(?P<di>[^$\n]*?[^\s\\$])\$(?![\w$])",  # $inline$ (not $5 or $5 and $10)
    re.DOTALL,
)


def _split_fences(text: str) -> List[Tuple[bool, str]]:
    """→ [(is_code, chunk)] for fenced code blocks vs. everything else (line based)."""
    out: List[Tuple[bool, str]] = []
    buf: List[str] = []
    fence: Optional[str] = None
    for line in text.splitlines(keepends=True):
        m = _FENCE_RE.match(line)
        if fence is None:
            if m:
                if buf:
                    out.append((False, "".join(buf)))
                buf = [line]
                fence = m.group(2)
            else:
                buf.append(line)
        else:
            buf.append(line)
            stripped = line.strip()
            if m and stripped and set(stripped) == {fence[0]} and len(stripped) >= len(fence):
                out.append((True, "".join(buf)))
                buf = []
                fence = None
    if buf:
        out.append((fence is not None, "".join(buf)))  # an unclosed fence stays code
    return out


def _split_code_spans(prose: str) -> List[Tuple[bool, str]]:
    """→ [(is_code, chunk)] for inline code spans (backtick run n closes on run n)."""
    out: List[Tuple[bool, str]] = []
    i, start, n = 0, 0, len(prose)
    while i < n:
        if prose[i] != "`":
            i += 1
            continue
        j = i
        while j < n and prose[j] == "`":
            j += 1
        run = prose[i:j]
        close = re.compile(r"(?<!`)" + re.escape(run) + r"(?!`)")
        m = close.search(prose, j)
        if not m:
            i = j  # no closer: the backticks are literal
            continue
        if i > start:
            out.append((False, prose[start:i]))
        out.append((True, prose[i:m.end()]))
        i = start = m.end()
    if start < n:
        out.append((False, prose[start:]))
    return out


def _norm_prose(s: str) -> str:
    def sub(m: "re.Match[str]") -> str:
        if m.group("esc"):
            return m.group(0)
        for g, (lo, hi) in (("dd", ("$$", "$$")), ("bd", ("$$", "$$")),
                            ("bi", ("\\(", "\\)")), ("di", ("\\(", "\\)"))):
            body = m.group(g)
            if body is not None:
                body = body.strip()
                return lo + body + hi if body else m.group(0)
        return m.group(0)
    return _MATH_RE.sub(sub, s)


def normalize_math(text: str) -> str:
    """Rewrite math delimiters in Markdown prose to ``\\( … \\)`` / ``$$ … $$``.

    Code spans and fenced code blocks are copied through byte for byte. The
    result is a fixed point: ``normalize_math(normalize_math(x)) == normalize_math(x)``.
    """
    if not text:
        return text or ""
    parts: List[str] = []
    for is_code, chunk in _split_fences(text):
        if is_code:
            parts.append(chunk)
            continue
        for span_code, piece in _split_code_spans(chunk):
            parts.append(piece if span_code else _norm_prose(piece))
    return "".join(parts)


_THINK_BLOCK_RE: Final = re.compile(r"<think>(.*?)</think>", re.DOTALL)


def split_thinking(text: str) -> Tuple[str, str]:
    """Pull ``<think>…</think>`` reasoning out of a reply → (answer, thinking).

    Also handles a reply whose template opened ``<think>`` in the prompt (text
    before a lone ``</think>`` is reasoning) and an unclosed ``<think>`` (the rest
    is reasoning).
    """
    text = text or ""
    thoughts: List[str] = []
    head, sep, tail = text.partition("</think>")
    if sep and "<think>" not in head:
        thoughts.append(head)
        text = tail
    text = _THINK_BLOCK_RE.sub(lambda m: thoughts.append(m.group(1)) or "", text)
    if "<think>" in text:
        text, _, rest = text.partition("<think>")
        thoughts.append(rest)
    thinking = "\n\n".join(t.strip() for t in thoughts if t.strip())
    return text.strip(), thinking


def markdown_entry(answer: str, thinking: str = "") -> Dict[str, Any]:
    """Saved-reply fields for a new assistant row: content (+ thinking when present)."""
    content = normalize_math((answer or "").strip()) or "(empty reply)"
    entry: Dict[str, Any] = {"content": content, "format": FORMAT_MARKDOWN}
    thinking = normalize_math((thinking or "").strip())
    if thinking:
        entry["thinking"] = thinking
    return entry


def read_entry(row: Dict[str, Any]) -> Dict[str, Any]:
    """Renderer view of one history row. No ``format`` (legacy) or unknown → ``plain``."""
    fmt = row.get("format")
    fmt = fmt if fmt in KNOWN_FORMATS else FORMAT_PLAIN
    thinking = row.get("thinking") if fmt == FORMAT_MARKDOWN else None
    return {
        "role": row.get("role"),
        "content": row.get("content") if isinstance(row.get("content"), str) else "",
        "format": fmt,
        "thinking": thinking if isinstance(thinking, str) and thinking.strip() else None,
        "session": row.get("session"),
        "ts": row.get("ts"),
    }
