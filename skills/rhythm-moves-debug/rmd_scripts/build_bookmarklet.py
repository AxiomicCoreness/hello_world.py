#!/usr/bin/env python3
"""Build the rhythm-moves-debug bookmarklet (read-only moves overlay).

Reads rmd_scripts/rhythm_moves_debug.js, strips comments and whitespace with a
small string-aware tokenizer, percent-encodes the result and prefixes
``javascript:``. Standard library only.

The tokenizer is deliberately strict: it refuses template literals and any
``/`` that is not a comment (regex literals and division), because telling
those apart needs a full JS parser. Newlines are dropped, so every statement
in the source must end with a semicolon; evals/ runs the built bookmarklet in
jsdom to prove it still works.

Usage:
  python -P rmd_scripts/build_bookmarklet.py              # print URL
  python -P rmd_scripts/build_bookmarklet.py -o out.txt   # write URL
  python -P rmd_scripts/build_bookmarklet.py --min-js out.js
Exit codes: 0 ok, 1 source rejected by the tokenizer or URL over MAX_URL_CHARS.

Adapted from skills/bms-display-mock/bms_scripts/build_bookmarklet.py (same
tokenizer); adds the MAX_URL_CHARS budget for mobile bookmark limits.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import quote, unquote

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "rhythm_moves_debug.js"
PREFIX = "javascript:"
# Characters left unencoded: safe inside a javascript: URL in every browser.
SAFE = "()';,=+:/?@&$!*-_.~[]{}|^<>"
# Keep the URL small enough for mobile bookmark fields.
MAX_URL_CHARS = 5000


class MinifyError(ValueError):
    pass


def _is_word(ch: str) -> bool:
    return ch.isalnum() or ch in "_$" or ord(ch) > 127


def minify(src: str) -> str:
    out: list[str] = []
    i, n = 0, len(src)
    pending_space = False
    line = 1

    def emit(s: str) -> None:
        nonlocal pending_space
        if pending_space and out:
            prev = out[-1][-1]
            nxt = s[0]
            if (_is_word(prev) and _is_word(nxt)) or (prev == nxt and prev in "+-"):
                out.append(" ")
        pending_space = False
        out.append(s)

    while i < n:
        ch = src[i]
        if ch == "\n":
            line += 1
            pending_space = True
            i += 1
        elif ch in " \t\r":
            pending_space = True
            i += 1
        elif src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            pending_space = True
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0:
                raise MinifyError(f"line {line}: unterminated block comment")
            line += src.count("\n", i, j)
            i = j + 2
            pending_space = True
        elif ch in "'\"":
            j = i + 1
            while j < n and src[j] != ch:
                if src[j] == "\\":
                    j += 1
                elif src[j] == "\n":
                    raise MinifyError(f"line {line}: newline inside string")
                j += 1
            if j >= n:
                raise MinifyError(f"line {line}: unterminated string")
            emit(src[i : j + 1])
            i = j + 1
        elif ch == "`":
            raise MinifyError(f"line {line}: template literals are not supported")
        elif ch == "/":
            raise MinifyError(f"line {line}: '/' outside a comment (regex or division) is not supported")
        else:
            emit(ch)
            i += 1
    return "".join(out)


def to_bookmarklet(min_js: str) -> str:
    return PREFIX + quote(min_js, safe=SAFE)


def from_bookmarklet(url: str) -> str:
    if not url.startswith(PREFIX):
        raise ValueError("not a javascript: URL")
    return unquote(url[len(PREFIX) :])


def build(source: Path = SOURCE) -> tuple[str, str]:
    min_js = minify(source.read_text(encoding="utf-8"))
    return min_js, to_bookmarklet(min_js)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", type=Path, default=SOURCE)
    ap.add_argument("-o", "--out", type=Path, help="write the javascript: URL here")
    ap.add_argument("--min-js", type=Path, help="also write the minified JS here")
    args = ap.parse_args(argv)
    try:
        min_js, url = build(args.source)
    except MinifyError as e:
        print(f"[!] {e}", file=sys.stderr)
        return 1
    if from_bookmarklet(url) != min_js:  # self-check: URL must decode to the minified JS
        print("[!] round-trip mismatch", file=sys.stderr)
        return 1
    if len(url) > MAX_URL_CHARS:
        print(f"[!] bookmarklet is {len(url)} chars, over MAX_URL_CHARS={MAX_URL_CHARS}", file=sys.stderr)
        return 1
    if args.min_js:
        args.min_js.write_text(min_js, encoding="utf-8")
    if args.out:
        args.out.write_text(url + "\n", encoding="utf-8")
        print(f"[+] wrote {args.out} ({len(url)} chars; minified JS {len(min_js)} chars)", file=sys.stderr)
    else:
        print(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
