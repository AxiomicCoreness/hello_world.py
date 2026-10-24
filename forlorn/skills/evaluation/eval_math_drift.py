#!/usr/bin/env python3
"""Math drift eval: plain arithmetic and order-of-magnitude fidelity.

Cases:
  add_17_25    "What is 17 + 25?" must contain 42 and no other integer answer.
  kelvin_1p64e5  Given T = 164,000 K, the model must write it as 1.64e5 K (any of
               1.64e5, 1.64 x 10^5, 1.64 × 10⁵) and must never produce 2.3e46.
               This checks notation fidelity of the owner's reference value; the
               physics behind 1.64e5 K is not derived here (no source for it was
               found in the repo).
  mul_12_12    "What is 12 * 12?" must contain 144.
Every case must pass (exit 0).
"""
from __future__ import annotations

import re
import sys

from _client import chat, parse_args, report

SCI_164 = re.compile(r"1\.64\s*(?:e\+?0?5|[x×\*]\s*10\s*(?:\^\s*\{?5\}?|⁵|\*\*\s*5))", re.I)
DRIFT_46 = re.compile(r"2\.3\s*(?:e\+?46|[x×\*]\s*10\s*(?:\^\s*\{?46\}?|⁴⁶|\*\*\s*46))", re.I)


def ints(text: str) -> set:
    return {int(x) for x in re.findall(r"(?<![\d.])\d+(?!\.?\d)", text.replace(",", ""))}


def main() -> int:
    a = parse_args(__doc__)
    out = []

    r = chat(a.url, "What is 17 + 25?", max_tokens=64)
    extra = ints(r) - {17, 25, 42}
    out.append({"id": "add_17_25", "pass": 42 in ints(r) and not extra,
                "why": "42 and no stray numbers" if 42 in ints(r) and not extra else f"numbers seen {sorted(ints(r))}",
                "reply": r})

    r = chat(a.url, "What is 12 * 12?", max_tokens=64)
    ok = 144 in ints(r)
    out.append({"id": "mul_12_12", "pass": ok, "why": "144 present" if ok else f"numbers seen {sorted(ints(r))}", "reply": r})

    r = chat(a.url, "A temperature is T = 164,000 K. Write T in scientific notation in kelvin. "
             "Answer with the value only.", max_tokens=64)
    ok = bool(SCI_164.search(r)) and not DRIFT_46.search(r)
    out.append({"id": "kelvin_1p64e5", "pass": ok,
                "why": "1.64e5 K, no 2.3e46" if ok else ("drifted to 2.3e46" if DRIFT_46.search(r) else "1.64e5 not found"),
                "reply": r})
    return report("eval_math_drift", out, a.json)


if __name__ == "__main__":
    sys.exit(main())
