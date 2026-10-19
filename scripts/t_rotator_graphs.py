#!/usr/bin/env python3
"""scripts/t_rotator_graphs.py — read-only graphs of the ledger.v2 chain.

Signitorial: Clarke Yoursa Tee

Replaces the old idea of appending graph code to t_rotator.py (that file
was the `less` help screen, now t_rotator.txt).

Outputs (all under --out-dir, never under --ledger-dir):
  chain.mmd          mermaid flowchart of the hash chain: one node per entry,
                     an edge per prev_hash link; broken links and seals that
                     do not recompute are marked.
  drift.png          per-entry timestamp offset from "high noon" (12:00:00Z of
                     the same UTC day), in seconds, coloured by whether the
                     timestamp is strict ISO-8601 (%Y-%m-%dT%H:%M:%SZ).
  timeline.png       entry index against timestamp.
  entries.json       the per-entry table the graphs were drawn from.

Seal rule (Regime B, entry_index >= 9281):
  SHA3-256(b"GARDEN.EVENT.v1.LEDGER" + b"\\x00" +
           f"{n}|{event}|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462")
Older entries get prev_hash links only; their seals are not judged here.

entry_index and timestamp are read from the raw YAML text, not the parsed
value: unquoted 0010 parses as octal 8, and unquoted timestamps become
datetime objects.

No ledger writes. seaborn is optional; matplotlib is the fallback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml

DOMAIN_LEDGER = b"GARDEN.EVENT.v1.LEDGER"
SEAL_FROM = 9281
PHI2 = "2.618033988749895"
DELTA = "b^2-4ac"
THETA = "2.5416018462"
STRICT_FMT = "%Y-%m-%dT%H:%M:%SZ"

INDEX_RE = re.compile(r"^entry_index:\s*['\"]?(\d+)['\"]?\s*(?:#.*)?$", re.M)
TS_RE = re.compile(r"^timestamp:\s*(.+?)\s*(?:#.*)?$", re.M)
STRICT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
HEX_RE = re.compile(r"[0-9a-fA-F]{64}")


def raw_hex(raw: str, key: str) -> Optional[str]:
    """Top-level 64-hex scalar read from the raw text. An all-digit digest
    left unquoted parses as an int, so the parsed value cannot be trusted."""
    m = re.search(rf"^{re.escape(key)}:\s*['\"]?([0-9a-fA-F]{{64}})['\"]?\s*(?:#.*)?$", raw, re.M)
    return m.group(1).lower() if m else None


@dataclass
class Entry:
    file: str
    index: Optional[int]
    event: Optional[str]
    timestamp_raw: Optional[str]
    timestamp_strict: bool = False
    timestamp_kind: str = "unparsed"       # strict | lenient | date_only | unparsed
    timestamp_iso: Optional[str] = None
    noon_offset_s: Optional[float] = None  # seconds from 12:00:00Z same UTC day
    prev_hash: Optional[str] = None
    declared_hex: Optional[str] = None
    digests: List[str] = field(default_factory=list)  # every 64-hex digest the entry declares
    computed_seal: Optional[str] = None
    seal_status: str = "not_judged"        # ok | mismatch | missing | not_judged
    link_status: str = "none"              # ok | broken | none | first
    notes: List[str] = field(default_factory=list)


def regime_b_seal(n: int, event: str) -> str:
    payload = f"{n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}".encode("ascii")
    return hashlib.sha3_256(DOMAIN_LEDGER + b"\x00" + payload).hexdigest()


def declared_digest(data: dict) -> Optional[str]:
    """Digest the seal is judged on: last 64-hex run in `seal`, else
    terminal_hex / witness_prefix / verification_hash (same precedence as
    .github/scripts/verify_ledger.py declared_hex)."""
    hits = HEX_RE.findall(str(data.get("seal", "")))
    if hits:
        return hits[-1].lower()
    for key in ("terminal_hex", "witness_prefix", "verification_hash"):
        v = data.get(key)
        if isinstance(v, str) and HEX_RE.fullmatch(v.strip()):
            return v.strip().lower()
    return None


DIGEST_KEYS = ("seal_sha3_256", "terminal_hex", "witness_prefix", "verification_hash")


def all_digests(data: dict, raw: str = "") -> List[str]:
    """Every digest the entry declares for itself: hex runs in `seal` plus
    seal_sha3_256 (the 9249-9280 convention: prev_hash equals the prior
    entry's seal_sha3_256), terminal_hex, witness_prefix, verification_hash."""
    out = [h.lower() for h in HEX_RE.findall(str(data.get("seal", "")))]
    for key in DIGEST_KEYS:
        v = data.get(key)
        if isinstance(v, str) and HEX_RE.fullmatch(v.strip()):
            out.append(v.strip().lower())
        elif raw and raw_hex(raw, key):
            out.append(raw_hex(raw, key))
    return list(dict.fromkeys(out))


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    return s


def parse_timestamp(raw: Optional[str]) -> Dict[str, object]:
    """Classify a raw timestamp and compute its offset from 12:00:00Z."""
    out: Dict[str, object] = {"strict": False, "kind": "unparsed", "iso": None, "offset": None}
    if not raw:
        return out
    s = _unquote(raw)
    dt: Optional[datetime] = None
    if STRICT_RE.match(s):
        dt = datetime.strptime(s, STRICT_FMT).replace(tzinfo=timezone.utc)
        out.update(strict=True, kind="strict")
    else:
        try:
            cand = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if "T" in s or " " in s:
                dt = cand if cand.tzinfo else cand.replace(tzinfo=timezone.utc)
                dt = dt.astimezone(timezone.utc)
                out.update(kind="lenient")
        except ValueError:
            dt = None
        if dt is None:
            m = DATE_RE.search(s)
            if m:
                # Date only: no time of day is declared, so no noon offset.
                d = datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                out.update(kind="date_only", iso=d.strftime("%Y-%m-%d"))
                return out
            return out
    noon = dt.replace(hour=12, minute=0, second=0, microsecond=0)
    out["iso"] = dt.strftime(STRICT_FMT)
    out["offset"] = (dt - noon).total_seconds()
    return out


def load_entries(ledger_dir: Path,
                 skipped: Optional[List[Dict[str, str]]] = None) -> List[Entry]:
    """Load every *.yml / *.yaml entry. Files that cannot be read or carry no
    top-level entry_index are not entries; each is appended to `skipped`
    (when given) as {"file", "reason"} instead of being dropped silently."""
    entries: List[Entry] = []
    for path in sorted(ledger_dir.glob("*.y*ml")):
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            if skipped is not None:
                skipped.append({"file": path.name, "reason": f"unreadable: {exc.__class__.__name__}"})
            continue
        m = INDEX_RE.search(raw)
        if not m:
            if skipped is not None:
                skipped.append({"file": path.name, "reason": "no top-level entry_index"})
            continue  # README-style or non-entry YAML
        idx = int(m.group(1))
        try:
            data = yaml.safe_load(raw) or {}
        except yaml.YAMLError as exc:
            data = {}
            note = f"yaml error: {exc.__class__.__name__}"
        else:
            note = None
        if not isinstance(data, dict):
            data = {}
        tsm = TS_RE.search(raw)
        ts_raw = tsm.group(1) if tsm else None
        ts = parse_timestamp(ts_raw)
        ev = data.get("event")
        prev = data.get("prev_hash")
        e = Entry(
            file=path.name,
            index=idx,
            event=ev if isinstance(ev, str) else None,
            timestamp_raw=_unquote(ts_raw) if ts_raw else None,
            timestamp_strict=bool(ts["strict"]),
            timestamp_kind=str(ts["kind"]),
            timestamp_iso=ts["iso"],  # type: ignore[arg-type]
            noon_offset_s=ts["offset"],  # type: ignore[arg-type]
            prev_hash=raw_hex(raw, "prev_hash"),
            declared_hex=declared_digest(data),
            digests=all_digests(data, raw),
        )
        if note:
            e.notes.append(note)
        if prev is not None and e.prev_hash is None:
            e.notes.append(f"prev_hash not 64-hex: {str(prev)[:24]!r}")
        if idx >= SEAL_FROM:
            if e.event is None:
                e.seal_status = "missing"
                e.notes.append("no event string")
            else:
                e.computed_seal = regime_b_seal(idx, e.event)
                if e.declared_hex is None:
                    e.seal_status = "missing"
                elif e.declared_hex == e.computed_seal:
                    e.seal_status = "ok"
                else:
                    e.seal_status = "mismatch"
        entries.append(e)
    entries.sort(key=lambda x: x.index if x.index is not None else -1)
    link_entries(entries)
    return entries


def link_entries(entries: List[Entry]) -> None:
    """prev_hash of entry i should equal a digest declared by entry i-1
    (seal hex, seal_sha3_256, ...) or, for n >= 9281, its recomputed seal.
    The first entry links outside the directory (weld) and is not judged."""
    for i, e in enumerate(entries):
        if i == 0:
            e.link_status = "first" if e.prev_hash else "none"
            continue
        if e.prev_hash is None:
            e.link_status = "none"
            continue
        p = entries[i - 1]
        targets = set(p.digests) | {h for h in (p.declared_hex, p.computed_seal) if h}
        e.link_status = "ok" if e.prev_hash in targets else "broken"
        if e.link_status == "broken":
            owner = next((x.index for x in entries
                          if e.prev_hash in set(x.digests) | {x.computed_seal}), None)
            if owner is not None:
                e.notes.append(f"prev_hash matches entry {owner}, not {p.index}")


def _mm_label(text: str) -> str:
    return (text.replace("&", "#amp;").replace('"', "#quot;")
                .replace("<", "#lt;").replace(">", "#gt;"))


def mermaid(entries: List[Entry]) -> str:
    lines = ["%% ledger.v2 hash chain — generated by scripts/t_rotator_graphs.py (read-only)",
             "flowchart LR"]
    for e in entries:
        tag = {"ok": "seal ok", "mismatch": "SEAL BREAK", "missing": "no seal hex",
               "not_judged": "pre-9281"}[e.seal_status]
        label = "<br/>".join([str(e.index), _mm_label(e.event or "?"), tag])
        lines.append(f'  E{e.index}["{label}"]')
    for i, e in enumerate(entries):
        if i == 0:
            continue
        p = entries[i - 1]
        if e.link_status == "ok":
            lines.append(f"  E{p.index} -->|prev_hash| E{e.index}")
        elif e.link_status == "broken":
            lines.append(f"  E{p.index} -.-x|prev_hash break| E{e.index}")
        else:
            lines.append(f"  E{p.index} -.->|no prev_hash| E{e.index}")
    lines += ["  classDef ok fill:#d4f7d4,stroke:#2a7a2a",
              "  classDef brk fill:#f7d4d4,stroke:#a02020,stroke-width:2px",
              "  classDef old fill:#eeeeee,stroke:#777777"]
    groups = {"ok": [], "brk": [], "old": []}
    for e in entries:
        key = {"ok": "ok", "mismatch": "brk", "missing": "brk"}.get(e.seal_status, "old")
        groups[key].append(f"E{e.index}")
    for cls, ids in groups.items():
        if ids:
            lines.append(f"  class {','.join(ids)} {cls}")
    return "\n".join(lines) + "\n"


def _plotting():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    try:
        import seaborn as sns  # optional
        sns.set_theme(style="whitegrid")
    except ImportError:
        sns = None
    return plt, sns


def plot_drift(entries: List[Entry], out: Path) -> Path:
    plt, sns = _plotting()
    xs = [e.index for e in entries if e.noon_offset_s is not None]
    ys = [e.noon_offset_s / 3600.0 for e in entries if e.noon_offset_s is not None]
    kinds = [e.timestamp_kind for e in entries if e.noon_offset_s is not None]
    fig, ax = plt.subplots(figsize=(11, 4.5))
    palette = {"strict": "#1f77b4", "lenient": "#ff7f0e"}
    if sns is not None and xs:
        sns.scatterplot(x=xs, y=ys, hue=kinds, palette=palette, ax=ax, s=55)
    else:
        for k, c in palette.items():
            px = [x for x, kk in zip(xs, kinds) if kk == k]
            py = [y for y, kk in zip(ys, kinds) if kk == k]
            if px:
                ax.scatter(px, py, c=c, label=k, s=30)
        if xs:
            ax.legend()
    ax.axhline(0, color="black", lw=1)
    skipped = [e.index for e in entries if e.noon_offset_s is None]
    ax.set_xlabel("entry_index")
    ax.set_ylabel("offset from 12:00:00Z (hours)")
    ax.set_title("Timestamp drift from high noon (same UTC day)")
    if skipped:
        shown = ", ".join(str(i) for i in skipped[:12]) + (" ..." if len(skipped) > 12 else "")
        ax.text(0.01, 0.02, f"not plotted, no time of day ({len(skipped)}): {shown}",
                transform=ax.transAxes, fontsize=8, color="#555555")
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def plot_timeline(entries: List[Entry], out: Path) -> Path:
    plt, _ = _plotting()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    full = [(datetime.strptime(e.timestamp_iso, STRICT_FMT), e.index)
            for e in entries if e.noon_offset_s is not None and e.timestamp_iso]
    dated = [(datetime.strptime(e.timestamp_iso, "%Y-%m-%d"), e.index)
             for e in entries if e.timestamp_kind == "date_only" and e.timestamp_iso]
    if full:
        ax.plot([t for t, _ in full], [i for _, i in full], "o-", ms=4, label="time of day declared")
    if dated:
        ax.scatter([t for t, _ in dated], [i for _, i in dated], facecolors="none",
                   edgecolors="#d62728", s=40, label="date only (plotted at 00:00Z)")
    ax.set_xlabel("timestamp (UTC)")
    ax.set_ylabel("entry_index")
    ax.set_title("ledger.v2 entry index timeline")
    if full or dated:
        ax.legend(loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def run(ledger_dir: Path, out_dir: Path, plots: bool = True) -> Dict[str, object]:
    ledger_dir = ledger_dir.resolve()
    out_dir = out_dir.resolve()
    if out_dir == ledger_dir or ledger_dir in out_dir.parents:
        raise SystemExit("refusing: --out-dir is inside --ledger-dir (no ledger writes)")
    skipped: List[Dict[str, str]] = []
    entries = load_entries(ledger_dir, skipped)
    for sk in skipped:
        print(f"skipped {sk['file']}: {sk['reason']}", file=sys.stderr)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    p = out_dir / "chain.mmd"
    p.write_text(mermaid(entries), encoding="utf-8")
    written.append(p)
    p = out_dir / "entries.json"
    p.write_text(json.dumps([asdict(e) for e in entries], indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    written.append(p)
    if plots:
        written.append(plot_drift(entries, out_dir / "drift.png"))
        written.append(plot_timeline(entries, out_dir / "timeline.png"))
    summary = {
        "entries": len(entries),
        "range": [entries[0].index, entries[-1].index] if entries else None,
        "seal_ok": sum(e.seal_status == "ok" for e in entries),
        "seal_breaks": [e.index for e in entries if e.seal_status in ("mismatch", "missing")],
        "link_breaks": [e.index for e in entries if e.link_status == "broken"],
        "no_prev_hash": [e.index for e in entries if e.link_status == "none"],
        "strict_timestamps": sum(e.timestamp_strict for e in entries),
        "date_only_timestamps": [e.index for e in entries if e.timestamp_kind == "date_only"],
        "unparsed_timestamps": [e.index for e in entries if e.timestamp_kind == "unparsed"],
        "skipped_files": skipped,
        "written": [str(w) for w in written],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ledger-dir", default="ledger.v2", type=Path)
    ap.add_argument("--out-dir", default="t_rotator_out", type=Path)
    ap.add_argument("--no-plots", action="store_true", help="mermaid + JSON only")
    args = ap.parse_args(argv)
    if not args.ledger_dir.is_dir():
        print(f"no such ledger dir: {args.ledger_dir}", file=sys.stderr)
        return 2
    summary = run(args.ledger_dir, args.out_dir, plots=not args.no_plots)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
