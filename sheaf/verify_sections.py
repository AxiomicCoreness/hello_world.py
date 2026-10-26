#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Verify sheaf reference sections against the ledger files they point at.

A sheaf section (sheaf/sections/*.yaml) brings ledger entries into the sheaf
fold BY REFERENCE ONLY (sheaf/PLAN.md, ledger 9204): the ledger files stay in
ledger/ and are never moved or rewritten. This script only reads.

For every section it checks:
  - kind is "reference" and measured_at_main is a full 40-hex commit SHA;
  - every listed entry path is under ledger/ and exists;
  - SHA3-256 of the raw file bytes equals the recorded current_sha3_256;
  - the entry's top-level entry_index / event / status match the section;
  - a sealed_digest_mismatch note (if present) is internally consistent and
    still matches merge/manifest.yaml (sealed digest recorded there, current
    digest differs from it);
  - every declared link line is still present, verbatim, at its dotted key
    path in the declaring ledger file.

Stdlib only. Sections are parsed with a strict subset parser (block mappings
and lists, quoted/plain strings, plain integers); anything outside the subset
is a parse error, not a skip. Ledger files are checked as raw text, not
YAML-loaded (e.g. YAML 1.1 loaders read "0515" as octal 333).

Exit codes:
  0 — every section verifies
  1 — any mismatch, missing file, or missing link
  2 — usage error, unreadable or malformed section, or no sections found
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?: (.*))?$")
INT_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)$")
RAW_KEY_RE = re.compile(r"^([^\s:#\-][^:]*):(?:\s|$)")


class SectionParseError(ValueError):
    pass


# --------------------------------------------------------------------------
# Strict subset YAML parser for section files
# --------------------------------------------------------------------------

def _scalar(text: str, lineno: int):
    if text.startswith('"'):
        if len(text) < 2 or not text.endswith('"'):
            raise SectionParseError(f"line {lineno}: unterminated double-quoted string")
        try:
            value = json.loads(text)
        except json.JSONDecodeError as e:
            raise SectionParseError(f"line {lineno}: bad double-quoted string: {e}") from None
        if not isinstance(value, str):
            raise SectionParseError(f"line {lineno}: not a string")
        return value
    if text.startswith("'"):
        if len(text) < 2 or not text.endswith("'"):
            raise SectionParseError(f"line {lineno}: unterminated single-quoted string")
        inner = text[1:-1]
        if re.search(r"(?<!')'(?!')", inner.replace("''", "")):
            raise SectionParseError(f"line {lineno}: stray quote in single-quoted string")
        return inner.replace("''", "'")
    if INT_RE.match(text):
        return int(text)
    if re.match(r"^-?0[0-9]+$", text):
        raise SectionParseError(f"line {lineno}: leading-zero number {text!r} is ambiguous; quote it")
    if text[0] in "[]{}&*!|>%@`#,?" or ": " in text or " #" in text:
        raise SectionParseError(f"line {lineno}: unsupported plain scalar {text!r}; quote it")
    if text in ("true", "false", "null", "~", "yes", "no", "on", "off"):
        raise SectionParseError(f"line {lineno}: ambiguous plain scalar {text!r}; quote it")
    return text


def _tokenize(text: str):
    out = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lead = raw[: len(raw) - len(raw.lstrip())]
        if "\t" in lead:
            raise SectionParseError(f"line {lineno}: tab indentation")
        out.append([len(lead), raw.rstrip()[len(lead):], lineno])
    return out


def _parse_block(lines, i, indent):
    if lines[i][1].startswith("- ") or lines[i][1] == "-":
        return _parse_list(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_map(lines, i, indent):
    result: dict = {}
    while i < len(lines):
        ind, content, lineno = lines[i]
        if ind < indent:
            break
        if ind > indent:
            raise SectionParseError(f"line {lineno}: unexpected indentation")
        if content.startswith("- "):
            break
        m = KEY_RE.match(content)
        if not m:
            raise SectionParseError(f"line {lineno}: expected 'key: value'")
        key, rest = m.group(1), m.group(2)
        if key in result:
            raise SectionParseError(f"line {lineno}: duplicate key {key!r}")
        if rest is None or rest == "":
            if i + 1 >= len(lines) or lines[i + 1][0] <= indent:
                raise SectionParseError(f"line {lineno}: key {key!r} has no value")
            result[key], i = _parse_block(lines, i + 1, lines[i + 1][0])
        else:
            result[key] = _scalar(rest, lineno)
            i += 1
    return result, i


def _parse_list(lines, i, indent):
    result: list = []
    while i < len(lines):
        ind, content, lineno = lines[i]
        if ind < indent:
            break
        if ind > indent:
            raise SectionParseError(f"line {lineno}: unexpected indentation")
        if not content.startswith("- "):
            raise SectionParseError(f"line {lineno}: expected list item")
        item = content[2:].lstrip()
        if KEY_RE.match(item):
            # Mapping item: re-home the first key at the item's indentation.
            lines[i] = [indent + (len(content) - len(item)), item, lineno]
            value, i = _parse_map(lines, i, lines[i][0])
        else:
            value = _scalar(item, lineno)
            i += 1
        result.append(value)
    return result, i


def parse_section_text(text: str):
    lines = _tokenize(text)
    if not lines:
        raise SectionParseError("empty section")
    if lines[0][0] != 0:
        raise SectionParseError(f"line {lines[0][2]}: top level must not be indented")
    data, i = _parse_map(lines, 0, 0)
    if i != len(lines):
        raise SectionParseError(f"line {lines[i][2]}: trailing content")
    return data


# --------------------------------------------------------------------------
# Raw-text helpers for ledger files and the manifest
# --------------------------------------------------------------------------

def sha3_file(path: Path) -> str:
    return hashlib.sha3_256(path.read_bytes()).hexdigest()


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def top_level_scalars(text: str) -> dict:
    out = {}
    for raw in text.splitlines():
        if not raw or raw[0] in " \t#-":
            continue
        m = re.match(r"^([^\s:]+):\s*(.*)$", raw.rstrip())
        if m and m.group(1) not in out:
            out[m.group(1)] = _unquote(m.group(2))
    return out


def lines_at_keypath(text: str, keypath: str) -> list[str]:
    """Stripped lines whose mapping-key path (by indentation) equals keypath."""
    target = keypath.split(".")
    stack: list[tuple[int, str]] = []
    found = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        while stack and stack[-1][0] >= indent:
            stack.pop()
        m = RAW_KEY_RE.match(stripped)
        if not m:
            continue
        key = m.group(1).strip()
        if [k for _, k in stack] + [key] == target:
            found.append(stripped)
        stack.append((indent, key))
    return found


def manifest_expected_digest(text: str, rel: str):
    """expected_sha3_256 for `rel` in merge/manifest.yaml (flow or block item)."""
    lines = text.splitlines()
    pat = re.compile(r"(?:^|[\s{,])path:\s*" + re.escape(rel) + r"\s*(?:[,}]|$)")
    for idx, line in enumerate(lines):
        if not pat.search(line):
            continue
        block = [line]
        item_indent = len(line) - len(line.lstrip())
        for nxt in lines[idx + 1:]:
            s = nxt.strip()
            if not s or s.startswith("#"):
                break
            if len(nxt) - len(nxt.lstrip()) <= item_indent or s.startswith("- "):
                break
            block.append(nxt)
        m = re.search(r'expected_sha3_256:\s*"?([0-9a-f]{64})"?', "\n".join(block))
        return m.group(1) if m else None
    return None


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------

def _safe_ledger_path(root: Path, rel) -> Path | None:
    if not isinstance(rel, str) or not rel.startswith("ledger/") or ".." in Path(rel).parts:
        return None
    return root / rel


def verify_section(root: Path, section_path: Path) -> dict:
    report = {"section": str(section_path.relative_to(root)) if section_path.is_relative_to(root) else str(section_path),
              "ok": False, "entries": [], "links": [], "errors": []}
    errors = report["errors"]
    try:
        data = parse_section_text(section_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SectionParseError) as e:
        report["fatal"] = f"MALFORMED: {e}"
        return report

    if data.get("kind") != "reference":
        errors.append("MALFORMED: kind must be 'reference'")
    if data.get("algorithm") != "SHA3-256" or data.get("digest_of") != "file_bytes":
        errors.append("MALFORMED: algorithm must be SHA3-256 over file_bytes")
    if not isinstance(data.get("measured_at_main"), str) or not HEX40.match(data["measured_at_main"]):
        errors.append("MALFORMED: measured_at_main must be a full 40-hex SHA")
    entries = data.get("entries")
    links = data.get("links")
    if not isinstance(entries, list) or not entries:
        errors.append("MALFORMED: entries must be a non-empty list")
        entries = []
    if not isinstance(links, list):
        errors.append("MALFORMED: links must be a list")
        links = []

    manifest_text = None
    for e in entries:
        if not isinstance(e, dict):
            errors.append(f"MALFORMED entry: {e!r}")
            continue
        rel = e.get("path")
        er = {"path": rel, "recorded_sha3_256": e.get("current_sha3_256"), "actual_sha3_256": None, "ok": False}
        report["entries"].append(er)
        p = _safe_ledger_path(root, rel)
        if p is None:
            errors.append(f"MALFORMED: entry path {rel!r} must be under ledger/")
            continue
        rec = e.get("current_sha3_256")
        if not isinstance(rec, str) or not HEX64.match(rec):
            errors.append(f"MALFORMED: {rel}: current_sha3_256 must be 64 lowercase hex")
            continue
        if not p.is_file():
            errors.append(f"MISSING: {rel}")
            continue
        actual = sha3_file(p)
        er["actual_sha3_256"] = actual
        ok = True
        if actual != rec:
            errors.append(f"MISMATCH: {rel}: sha3_256 {actual} != recorded {rec}")
            ok = False
        top = top_level_scalars(p.read_text(encoding="utf-8"))
        for key in ("entry_index", "event", "status"):
            if str(e.get(key)) != top.get(key):
                errors.append(f"MISMATCH: {rel}: {key} is {top.get(key)!r}, section says {e.get(key)!r}")
                ok = False
        sdm = e.get("sealed_digest_mismatch")
        if sdm is not None:
            if not isinstance(sdm, dict):
                errors.append(f"MALFORMED: {rel}: sealed_digest_mismatch must be a mapping")
                ok = False
            else:
                sealed = sdm.get("manifest_sealed_sha3_256")
                for k, rx in (("manifest_sealed_sha3_256", HEX64), ("current_sha3_256", HEX64),
                              ("manifest_recorded_at", HEX40), ("changed_by_commit", HEX40)):
                    if not isinstance(sdm.get(k), str) or not rx.match(sdm[k]):
                        errors.append(f"MALFORMED: {rel}: sealed_digest_mismatch.{k}")
                        ok = False
                if not sdm.get("field_changed"):
                    errors.append(f"MALFORMED: {rel}: sealed_digest_mismatch.field_changed missing")
                    ok = False
                if sdm.get("current_sha3_256") != rec:
                    errors.append(f"MISMATCH: {rel}: sealed_digest_mismatch.current_sha3_256 != entry current_sha3_256")
                    ok = False
                if sealed == rec:
                    errors.append(f"MISMATCH: {rel}: sealed digest equals current digest; mismatch note is stale")
                    ok = False
                mrel = sdm.get("manifest", "merge/manifest.yaml")
                mpath = root / mrel if isinstance(mrel, str) and ".." not in Path(mrel).parts else None
                if mpath is None or not mpath.is_file():
                    errors.append(f"MISSING: manifest {mrel!r}")
                    ok = False
                else:
                    if manifest_text is None or manifest_text[0] != mpath:
                        manifest_text = (mpath, mpath.read_text(encoding="utf-8"))
                    got = manifest_expected_digest(manifest_text[1], rel)
                    if got != sealed:
                        errors.append(f"MISMATCH: {rel}: {mrel} expected_sha3_256 is {got!r}, section says {sealed!r}")
                        ok = False
        er["ok"] = ok

    for ln in links:
        if not isinstance(ln, dict):
            errors.append(f"MALFORMED link: {ln!r}")
            continue
        rel, field, line = ln.get("declared_in"), ln.get("field"), ln.get("line")
        lr = {"from": ln.get("from"), "to": ln.get("to"), "declared_in": rel, "field": field, "ok": False}
        report["links"].append(lr)
        p = _safe_ledger_path(root, rel)
        if p is None or not isinstance(field, str) or not isinstance(line, str):
            errors.append(f"MALFORMED link: {ln!r}")
            continue
        if not line.startswith(field.split(".")[-1] + ":"):
            errors.append(f"MALFORMED link: line {line!r} does not start with key of field {field!r}")
            continue
        if not p.is_file():
            errors.append(f"MISSING: {rel} (link {field})")
            continue
        if line not in lines_at_keypath(p.read_text(encoding="utf-8"), field):
            errors.append(f"MISSING LINK: {rel}: {field}: {line!r} not found")
            continue
        lr["ok"] = True

    report["ok"] = not errors and "fatal" not in report
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify sheaf reference sections (read-only).")
    ap.add_argument("sections", nargs="*", type=Path,
                    help="section files (default: <root>/sheaf/sections/*.yaml)")
    ap.add_argument("--root", type=Path, default=None, help="repo root (default: parent of sheaf/)")
    ap.add_argument("--json", action="store_true", help="emit a JSON report on stdout")
    args = ap.parse_args(argv)

    root = (args.root or Path(__file__).resolve().parents[1]).resolve()
    sections = [s if s.is_absolute() else root / s for s in args.sections] or \
        sorted((root / "sheaf" / "sections").glob("*.yaml"))
    if not sections:
        msg = f"NO SECTIONS under {root / 'sheaf' / 'sections'}"
        if args.json:
            print(json.dumps({"ok": False, "fatal": msg, "sections": []}, indent=2))
        else:
            print(msg, file=sys.stderr)
        return 2

    reports = []
    for s in sections:
        if not s.is_file():
            reports.append({"section": str(s), "ok": False, "fatal": f"MISSING section {s}",
                            "entries": [], "links": [], "errors": []})
            continue
        reports.append(verify_section(root, s.resolve()))

    fatal = any("fatal" in r for r in reports)
    ok = all(r["ok"] for r in reports)
    if args.json:
        print(json.dumps({"ok": ok, "root": str(root), "sections": reports}, indent=2, ensure_ascii=False))
    else:
        for r in reports:
            if "fatal" in r:
                print(f"FAIL: {r['section']}: {r['fatal']}", file=sys.stderr)
                continue
            for e in r["errors"]:
                print(f"FAIL: {r['section']}: {e}", file=sys.stderr)
            if r["ok"]:
                print(f"OK: {r['section']}: {len(r['entries'])} entries, {len(r['links'])} links verified")
    if fatal:
        return 2
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
