#!/usr/bin/env python3
"""Validate an XML file against com.fruitfly.brain.ConnectomeLoader's rules.

Rules (mirrors ConnectomeLoader.load): root <hemibrain>; no DOCTYPE; every
<neuron> has a non-empty, unique id; every <connection> has from/to naming a
declared neuron and a finite weight; optional delayMs finite and > 0
(default 1.0); no repeated (from, to) pair. Self-loops are allowed.
Ids and attributes are whitespace-trimmed like the loader does.

Prints counts. Exit 0 valid, 1 invalid or unreadable.
"""
from __future__ import annotations

import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _finite(raw: str) -> float:
    v = float(raw)  # ValueError on garbage
    if not math.isfinite(v):
        raise ValueError(f"not finite: {raw!r}")
    return v


def check(path: Path) -> tuple[list[str], dict]:
    errs: list[str] = []
    stats = {"neurons": 0, "connections": 0, "self_loops": 0,
             "negative_weights": 0, "default_delay": 0, "total_weight": 0.0}
    try:
        data = path.read_bytes()
    except OSError as e:
        return [f"cannot read: {e}"], stats
    if b"<!DOCTYPE" in data.upper():
        return ["DOCTYPE declarations are refused by the loader"], stats
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        return [f"invalid XML: {e}"], stats
    if root.tag != "hemibrain":
        errs.append(f"root element must be <hemibrain>, found <{root.tag}>")
        return errs, stats
    ids: set[str] = set()
    for i, el in enumerate(root.iter("neuron")):
        nid = (el.get("id") or "").strip()
        if not nid:
            errs.append(f"neuron #{i} is missing required attribute 'id'")
        elif nid in ids:
            errs.append(f"duplicate neuron id '{nid}'")
        else:
            ids.add(nid)
    stats["neurons"] = len(ids)
    pairs: set[tuple[str, str]] = set()
    for k, el in enumerate(root.iter("connection")):
        where = f"connection #{k}"
        a = {n: (el.get(n) or "").strip() for n in ("from", "to", "weight")}
        missing = [n for n, v in a.items() if not v]
        if missing:
            errs.append(f"{where} is missing required attribute(s) {missing}")
            continue
        for end in ("from", "to"):
            if a[end] not in ids:
                errs.append(f"{where} references unknown {'source' if end == 'from' else 'target'} neuron '{a[end]}'")
        try:
            w = _finite(a["weight"])
        except ValueError as e:
            errs.append(f"{where} weight invalid: {e}")
            continue
        if el.get("delayMs") is not None:
            try:
                d = _finite(el.get("delayMs").strip())
                if d <= 0:
                    errs.append(f"{where} delayMs must be > 0, got {d}")
            except ValueError as e:
                errs.append(f"{where} delayMs invalid: {e}")
        else:
            stats["default_delay"] += 1
        pair = (a["from"], a["to"])
        if pair in pairs:
            errs.append(f"duplicate connection {pair[0]} -> {pair[1]}")
            continue
        pairs.add(pair)
        stats["self_loops"] += pair[0] == pair[1]
        stats["negative_weights"] += w < 0
        stats["total_weight"] += w
    stats["connections"] = len(pairs)
    return errs, stats


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        print("usage: check_hhmi.py FILE.xml", file=sys.stderr)
        return 1
    path = Path(argv[0])
    errs, s = check(path)
    for e in errs[:50]:
        print(f"[!] {e}")
    if len(errs) > 50:
        print(f"[!] ... {len(errs) - 50} more")
    tw = s["total_weight"]
    print(f"{path}: neurons={s['neurons']} connections={s['connections']} "
          f"self_loops={s['self_loops']} negative_weights={s['negative_weights']} "
          f"default_delay={s['default_delay']} total_weight={int(tw) if tw == int(tw) else tw}")
    print("[+] OK" if not errs else f"[!] INVALID ({len(errs)} error(s))")
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main())
