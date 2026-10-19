#!/usr/bin/env python3
"""Convert the FlyEM hemibrain v1.2 bulk CSV export to ConnectomeLoader XML.

Input (from exported-traced-adjacencies-v1.2.tar.gz):
  traced-neurons.csv            bodyId,type,instance            (21,739 rows)
  traced-total-connections.csv  bodyId_pre,bodyId_post,weight   (~3.55M rows)
weight is a synapse count (no sign, no delay).

Output: <hemibrain><neuron id=".."/>...<connection from to weight/>...</hemibrain>
in the project-local format read by com.fruitfly.brain.ConnectomeLoader.
No delayMs is written, so the loader's 1.0 ms default applies; weights stay
positive (all excitatory) because the export carries no sign.

  --min-weight W  drop connections with weight < W (applied first)
  --limit N       keep the N neurons with the largest total synapse weight
                  (in + out, after --min-weight), and only edges among them

Neuron order: by total weight descending, then bodyId (stable, deterministic).
Without --limit, order follows traced-neurons.csv. Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import quoteattr

NEURONS_CSV = "traced-neurons.csv"
EDGES_CSV = "traced-total-connections.csv"


def _num(raw: str, where: str) -> float:
    v = float(raw)
    if v != v or v in (float("inf"), float("-inf")):
        raise ValueError(f"{where}: non-finite weight {raw!r}")
    return v


def _fmt(w: float) -> str:
    return str(int(w)) if w == int(w) else repr(w)


def read_neurons(path: Path) -> list[str]:
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames is None or "bodyId" not in rd.fieldnames:
            raise ValueError(f"{path}: missing bodyId column")
        ids, seen = [], set()
        for i, row in enumerate(rd, start=2):
            bid = (row["bodyId"] or "").strip()
            if not bid:
                raise ValueError(f"{path}:{i}: empty bodyId")
            if bid in seen:
                raise ValueError(f"{path}:{i}: duplicate bodyId {bid}")
            seen.add(bid)
            ids.append(bid)
    return ids


def read_edges(path: Path, known: set[str], min_weight: float):
    """Return ({(pre, post): weight}, n_rows, n_unknown, n_below)."""
    need = {"bodyId_pre", "bodyId_post", "weight"}
    edges: dict[tuple[str, str], float] = {}
    rows = unknown = below = 0
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames is None or not need <= set(rd.fieldnames):
            raise ValueError(f"{path}: need columns {sorted(need)}")
        for i, row in enumerate(rd, start=2):
            rows += 1
            pre, post = row["bodyId_pre"].strip(), row["bodyId_post"].strip()
            if pre not in known or post not in known:
                unknown += 1
                continue
            w = _num(row["weight"], f"{path}:{i}")
            if w < min_weight:
                below += 1
                continue
            # a repeated pair would be rejected by the loader; sum it instead
            edges[(pre, post)] = edges.get((pre, post), 0.0) + w
    return edges, rows, unknown, below


def select(ids: list[str], edges: dict, limit: int | None):
    if limit is None:
        return ids, edges
    total: dict[str, float] = defaultdict(float)
    for (pre, post), w in edges.items():
        total[pre] += w
        total[post] += w
    def bid_key(b: str):
        return (0, int(b), b) if b.isdigit() else (1, 0, b)
    ranked = sorted(ids, key=lambda b: (-total.get(b, 0.0), bid_key(b)))
    keep = ranked[:limit]
    ks = set(keep)
    sub = {k: w for k, w in edges.items() if k[0] in ks and k[1] in ks}
    return keep, sub


def write_xml(out, ids: list[str], edges: dict, note: str) -> None:
    order = {b: i for i, b in enumerate(ids)}
    out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    out.write("<!-- " + note.replace("--", "- -") + " -->\n<hemibrain>\n")
    for b in ids:
        out.write(f"    <neuron id={quoteattr(b)}/>\n")
    for (pre, post), w in sorted(edges.items(), key=lambda kv: (order[kv[0][0]], order[kv[0][1]])):
        out.write(f"    <connection from={quoteattr(pre)} to={quoteattr(post)} weight=\"{_fmt(w)}\"/>\n")
    out.write("</hemibrain>\n")


def convert(src: Path, out_path: Path | None, min_weight: float = 0.0,
            limit: int | None = None, neurons_csv: Path | None = None,
            edges_csv: Path | None = None) -> dict:
    ncsv = neurons_csv or src / NEURONS_CSV
    ecsv = edges_csv or src / EDGES_CSV
    ids = read_neurons(ncsv)
    edges, rows, unknown, below = read_edges(ecsv, set(ids), min_weight)
    keep, sub = select(ids, edges, limit)
    note = (f"Converted from FlyEM hemibrain CSV ({ncsv.name}, {ecsv.name}); "
            f"min_weight={_fmt(min_weight)} limit={limit}; weight = synapse count")
    if out_path is None:
        write_xml(sys.stdout, keep, sub, note)
    else:
        with open(out_path, "w", encoding="utf-8") as fh:
            write_xml(fh, keep, sub, note)
    return {"neurons_in": len(ids), "edge_rows_in": rows, "edges_unknown": unknown,
            "edges_below_min": below, "neurons_out": len(keep), "edges_out": len(sub),
            "synapses_out": sum(sub.values())}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", type=Path, help=f"directory holding {NEURONS_CSV} and {EDGES_CSV}")
    ap.add_argument("-o", "--out", type=Path, help="output XML (default stdout)")
    ap.add_argument("--min-weight", type=float, default=0.0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--neurons", type=Path, help="override neurons CSV path")
    ap.add_argument("--connections", type=Path, help="override connections CSV path")
    a = ap.parse_args(argv)
    if a.limit is not None and a.limit < 1:
        ap.error("--limit must be >= 1")
    try:
        s = convert(a.src, a.out, a.min_weight, a.limit, a.neurons, a.connections)
    except (OSError, ValueError, KeyError) as e:
        print(f"[!] {e}", file=sys.stderr)
        return 1
    print("[+] " + " ".join(f"{k}={_fmt(v) if isinstance(v, float) else v}"
                            for k, v in s.items()), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
