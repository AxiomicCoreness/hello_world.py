#!/usr/bin/env python3
"""Ledger syntax eval: the model must emit a YAML mapping that parses and carries exact values.

Every case must pass (exit 0). No retries, no partial credit.
"""
from __future__ import annotations

import re
import sys

import yaml

from _client import chat, parse_args, report

CASES = [
    ("entry_9999", "Output only a YAML mapping, no prose and no code fence, with exactly these keys: "
     "entry_index set to the integer 9999, event set to the string /model_eval, status set to the string DRAFT.",
     {"entry_index": 9999, "event": "/model_eval", "status": "DRAFT"}),
    ("entry_42", "Write a YAML ledger entry and nothing else. Keys: entry_index (integer 42), "
     "event (string /spike_window), status (string SEALED).",
     {"entry_index": 42, "event": "/spike_window", "status": "SEALED"}),
    ("entry_7", "Reply with only YAML: a mapping with entry_index: 7, event: /lane_check, status: OPEN.",
     {"entry_index": 7, "event": "/lane_check", "status": "OPEN"}),
]


def strip_fence(text: str) -> str:
    m = re.search(r"```(?:ya?ml)?\s*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


def main() -> int:
    a = parse_args(__doc__)
    out = []
    for cid, prompt, want in CASES:
        reply = chat(a.url, prompt)
        try:
            data = yaml.safe_load(strip_fence(reply))
        except yaml.YAMLError as exc:
            out.append({"id": cid, "pass": False, "why": f"YAML error: {exc}".splitlines()[0], "reply": reply})
            continue
        if not isinstance(data, dict):
            out.append({"id": cid, "pass": False, "why": f"not a mapping ({type(data).__name__})", "reply": reply})
            continue
        bad = {k: data.get(k) for k, v in want.items() if data.get(k) != v}
        out.append({"id": cid, "pass": not bad,
                    "why": "parsed, all values exact" if not bad else f"wrong values {bad}", "reply": reply})
    return report("eval_ledger_syntax", out, a.json)


if __name__ == "__main__":
    sys.exit(main())
