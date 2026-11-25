# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Clarke Yoursa Tee (AxiomicCoreness)
# Zenodo DOI: 10.5281/zenodo.23378305 (https://doi.org/10.5281/zenodo.23378305)
# DeepInfer model design is by Clarke Yoursa Tee
"""Smoke-test validator for docs/KQUANT_1D_F32_MATH_2026-11-25.md."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DOC_DEFAULT = Path(__file__).resolve().parent.parent / "docs" / "KQUANT_1D_F32_MATH_2026-11-25.md"

EXPECTED_HEADER_LINES = [
    "<!-- SPDX-License-Identifier: MIT -->",
    "<!-- Copyright (c) 2026 Clarke Yoursa Tee (AxiomicCoreness) -->",
    "<!-- Zenodo DOI: 10.5281/zenodo.23378305 (https://doi.org/10.5281/zenodo.23378305) -->",
    "<!-- DeepInfer model design is by Clarke Yoursa Tee -->",
]

# Superblock byte footprint for QK_K = 256 weights -> exact bits per weight
QK_K = 256
KQUANT_BLOCKS = {
    "Q4_K": 144,
    "Q5_K": 176,
    "Q6_K": 210,
}

# Verified against llama.cpp include/llama.h (enum llama_ftype)
LLAMA_FTYPE_TABLE = {
    "Q4_K_S": 14,
    "Q4_K_M": 15,
    "Q5_K_S": 16,
    "Q5_K_M": 17,
    "Q6_K": 18,
    "BF16": 32,
    "MXFP4_MOE": 38,
    "GUESSED": 1024,
}

EXPECTED_SECTION5_BYTES = {
    "DeepInfer-66L-from198-Q4_K_S-f32norm.gguf": 2_081_222_304,
    "DI-66L-from198-ink-Q5_K_S-f32norm.gguf": 2_482_474_656,
    "DI-66L-from198-ink-Q6K-f32norm.gguf": 2_923_636_896,
    "deepseek-r2-1.5b-Q4_K_M.gguf": 1_117_320_640,
    "1-D F32 overhead": 678_912,
}


def check_header(lines: list[str]) -> None:
    if len(lines) < len(EXPECTED_HEADER_LINES):
        raise AssertionError("Document has fewer than 4 lines.")
    for idx, expected in enumerate(EXPECTED_HEADER_LINES):
        actual = lines[idx].strip()
        if actual != expected:
            raise AssertionError(f"Header line {idx + 1} mismatch: {actual!r} != {expected!r}")


def parse_fences(lines: list[str]) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    in_fence = False
    fence_lang = ""
    buf: list[str] = []
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_fence:
                in_fence = True
                fence_lang = stripped[3:].strip().lower()
                buf = []
            else:
                if stripped != "```":
                    raise AssertionError(f"Closing fence at line {lineno} has trailing text: {stripped!r}")
                blocks.append((fence_lang, "\n".join(buf)))
                in_fence = False
                fence_lang = ""
                buf = []
        elif in_fence:
            buf.append(line)
    if in_fence:
        raise AssertionError("Unbalanced code fence: reached EOF inside an open fence.")
    return blocks


def check_mermaid_blocks(blocks: list[tuple[str, str]], run_mmdc: bool) -> int:
    mermaid_blocks = [body for lang, body in blocks if lang == "mermaid"]
    if not mermaid_blocks:
        raise AssertionError("Expected at least one ```mermaid block.")

    valid_headers = ("flowchart ", "graph ", "sequenceDiagram", "classDiagram", "stateDiagram")
    for idx, body in enumerate(mermaid_blocks, start=1):
        non_empty = [ln.strip() for ln in body.splitlines() if ln.strip()]
        if not non_empty:
            raise AssertionError(f"Mermaid block #{idx} is empty.")
        if not non_empty[0].startswith(valid_headers):
            raise AssertionError(f"Mermaid block #{idx} has unexpected header: {non_empty[0]!r}")
        if not any("-->" in ln or "---" in ln for ln in non_empty[1:]):
            raise AssertionError(f"Mermaid block #{idx} has no edges.")
        for ln in non_empty:
            if ln.count('"') % 2 != 0:
                raise AssertionError(f"Mermaid block #{idx} has unbalanced quotes in line: {ln!r}")

        if run_mmdc:
            npx_bin = shutil.which("npx")
            if not npx_bin:
                raise AssertionError("npx not found on PATH; cannot run mmdc.")
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp = Path(tmpdir)
                mmd_path = tmp / f"diagram_{idx}.mmd"
                svg_path = tmp / f"diagram_{idx}.svg"
                pup_path = tmp / "puppeteer.json"
                mmd_path.write_text(body + "\n", encoding="utf-8")
                pup_path.write_text(
                    json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}),
                    encoding="utf-8",
                )
                proc = subprocess.run(
                    [
                        npx_bin,
                        "-y",
                        "@mermaid-js/mermaid-cli",
                        "-p",
                        str(pup_path),
                        "-i",
                        str(mmd_path),
                        "-o",
                        str(svg_path),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode != 0 or not svg_path.exists():
                    raise AssertionError(
                        f"mmdc failed on mermaid block #{idx} (rc={proc.returncode}):\n"
                        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
                    )
                svg_text = svg_path.read_text(encoding="utf-8", errors="replace")
                if "<svg" not in svg_text:
                    raise AssertionError(f"mmdc output for block #{idx} is not valid SVG.")

    return len(mermaid_blocks)


def check_bpw_arithmetic(text: str) -> dict[str, float]:
    computed: dict[str, float] = {}
    for qname, nbytes in KQUANT_BLOCKS.items():
        bpw = (nbytes * 8) / QK_K
        bpw_str = f"{bpw:g}"
        computed[qname] = bpw
        # Verify both exact byte footprint and exact bpw appear in the doc
        if str(nbytes) not in text:
            raise AssertionError(f"Missing superblock byte count {nbytes} for {qname}.")
        if not re.search(rf"\b{re.escape(bpw_str)}\s*bpw\b|\b{re.escape(bpw_str)}\b", text):
            raise AssertionError(f"Missing recomputed bpw {bpw_str} for {qname} ({nbytes}*8/{QK_K}).")
    return computed


def check_file_types(text: str) -> None:
    # Check every pair in LLAMA_FTYPE_TABLE appears with matching name and id
    for name, ftype_id in LLAMA_FTYPE_TABLE.items():
        if name not in text:
            raise AssertionError(f"Missing file_type name {name} in doc.")
        if not re.search(
            rf"(?:{re.escape(name)}\s*=\s*{ftype_id}\b|{ftype_id}\s*:\s*{re.escape(name)}\b|`{ftype_id}`\s*\(`{re.escape(name)}`\))",
            text,
        ):
            raise AssertionError(f"Doc does not pair {name} with expected file_type id {ftype_id}.")

    # Also verify no conflicting NAME=ID pairs exist anywhere in the doc
    for m in re.finditer(r"\b(Q4_K_S|Q4_K_M|Q5_K_S|Q5_K_M|Q6_K|BF16|MXFP4_MOE|GUESSED)\s*=\s*(\d+)\b", text):
        name, val = m.group(1), int(m.group(2))
        if LLAMA_FTYPE_TABLE[name] != val:
            raise AssertionError(f"Conflicting file_type mapping {name}={val}; expected {LLAMA_FTYPE_TABLE[name]}.")
    for m in re.finditer(r"\bfile_type\s*=\s*(\d+)\s*:\s*(Q4_K_S|Q4_K_M|Q5_K_S|Q5_K_M|Q6_K|BF16|MXFP4_MOE|GUESSED)\b", text):
        val, name = int(m.group(1)), m.group(2)
        if LLAMA_FTYPE_TABLE[name] != val:
            raise AssertionError(f"Conflicting flowchart file_type {val}:{name}; expected {LLAMA_FTYPE_TABLE[name]}.")


def check_section5_bytes(text: str) -> None:
    m = re.search(r"^##\s+§5\b.*$", text, flags=re.MULTILINE)
    if not m:
        raise AssertionError("Missing '## §5' section.")
    sec5 = text[m.start():]

    # Every 4+ digit integer representing a byte count in §5 must be comma-grouped (e.g. 2,923,636,896)
    # Exclude hex digests, scientific notation exponents, filenames, and markdown headings/section numbers.
    cleaned = re.sub(r"`[^`\n]+\.gguf`", "", sec5)
    cleaned = re.sub(r"`[0-9a-f]{32,}`", "", cleaned)
    cleaned = re.sub(r"\b\d+(?:\.\d+)?e[+-]?\d+\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:DEEPINFER_8090_RUNBOOK\.md|1\.5b|Q4_K_M|Q4_K_S|Q5_K_S|Q6_K|Q5_K|Q6K|66L)\b", "", cleaned)

    unformatted = re.findall(r"(?<![,\d.])\d{4,}(?![,\d])", cleaned)
    if unformatted:
        raise AssertionError(f"Unformatted 4+ digit integer(s) in §5 (expected comma grouping): {unformatted}")

    for label, expected_val in EXPECTED_SECTION5_BYTES.items():
        formatted = f"{expected_val:,}"
        if formatted not in sec5:
            raise AssertionError(f"Missing consistently formatted byte anchor {formatted} for {label} in §5.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", type=Path, default=DOC_DEFAULT, help="Path to markdown document")
    parser.add_argument("--no-mmdc", action="store_true", help="Skip mmdc rendering check")
    args = parser.parse_args()

    text = args.doc.read_text(encoding="utf-8")
    lines = text.splitlines()

    check_header(lines)
    blocks = parse_fences(lines)
    n_mermaid = check_mermaid_blocks(blocks, run_mmdc=not args.no_mmdc)
    bpw_map = check_bpw_arithmetic(text)
    check_file_types(text)
    check_section5_bytes(text)

    print(
        f"KQUANT_DOC_SMOKE_OK: header=4/4 fences={len(blocks)} mermaid={n_mermaid} "
        f"bpw={bpw_map} ftypes={len(LLAMA_FTYPE_TABLE)} bytes={len(EXPECTED_SECTION5_BYTES)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
