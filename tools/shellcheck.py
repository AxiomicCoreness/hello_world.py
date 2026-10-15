#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────────────
# LABEL BLOCK
# ──────────────────────────────────────────────────────────────────────
# label:     garden.gate
# wire:      MCP call aggregate
# path:      tools/mcp_call_gate.py  (entry shim: tools/mcp_call_gate.sh)
# RENAMED:   from tools/shellcheck.py — name collision went red in CI on
#            2026-10-15: the singularity workflow invokes
#            `python3 tools/shellcheck.py ledger/0353.yaml` expecting the
#            YAML001/YAML002 linter, but the gate's argparse rejects the
#            positional argument (exit 2). The linter is restored at
#            tools/shellcheck.py from commit 20515417 (7,482 bytes, held
#            verbatim in the companion canvas); the gate moves here.
# TYPE:      gate
# STATUS:    open
# BLOCKER:   none
# QUEUE:     new
# ORIGIN:    commander request — aggregate MCP tool calls from the last
#            command run in /tmp/, write a Boolean custom result to /tools/
# LEDGER:    NO_GROWTH
# NOTE:      self-contained — stdlib only, no third-party dependency
# REVISION:  index served by FastAPI/mTLS backend (SQLite) — no JSON index
#            file in /tmp. Lookup path: mTLS GET to the backend; filesystem
#            scan remains as fallback AND as mtime cross-check for "latest"
#            (backend lag between a log write and its SQLite row would
#            otherwise serve the previous run — wrong-but-green class).
#            Carries forward the two earlier fixes: _rid_from strips all
#            extension pairs (.gz included) everywhere; "latest" is never
#            answered from a cache alone.
# ──────────────────────────────────────────────────────────────────────
#
# Usage (via shim, which preserves exit codes):
#   ./mcp_call_gate.sh [--run-id <id>] [--gate-name <name>] [--tmp DIR] [--tools DIR]
#
# Contract:
#   1. Locate the most recent MCP run log under /tmp/ (mtime-descending):
#        /tmp/mcp_run_<id>.jsonl        (preferred, one JSON object per line)
#        /tmp/mcp_run_<id>.json        (fallback, single JSON array/object)
#        .jsonl.gz / .json.gz           (transparent gzip support)
#      --run-id selects a specific run; otherwise the newest wins — and the
#      newest is ALWAYS determined by a live scan, never a cached index.
#   2. Aggregate per-tool call counts, successes, failures, and total
#      duration where the fields exist. Unknown shapes are counted, not
#      rejected — discovery, not gate, on the log format.
#   3. Boolean custom gate: PASS iff the run exists, contains at least one
#      tool call, and zero calls report failure. Result is written as
#      /tools/<gate-name>.json (default mcp_call_gate.json) with fields:
#        { "gate": <name>, "pass": true|false,
#          "reason": "...", "run_id": <id>, "aggregated": {...} }
#      Exit code mirrors the Boolean: 0 = pass, 1 = fail, 2 = usage error.
#      Committed content: full aggregates, no truncation of digests.

import argparse
import glob
import gzip
import json
import os
import ssl
import sys
import time
import urllib.request

DEFAULT_TMP = "/tmp"
DEFAULT_TOOLS = "/tools"
RUN_PREFIX = "mcp_run_"
# Index lives in the FastAPI/mTLS backend (SQLite) — no on-disk JSON index.
#   MCP_INDEX_URL      e.g. https://localhost:8443  (no trailing slash)
#   MCP_TLS_CA         CA bundle   (default /etc/mtls/ca.crt)
#   MCP_TLS_CERT       client cert (default /etc/mtls/client.crt)
#   MCP_TLS_KEY        client key  (default /etc/mtls/client.key)
# Endpoints (assumed shape, named as assumption):
#   GET /index/latest      -> {"run_id": ..., "path": ..., "mtime": ...} | 404
#   GET /index/runs/<id>   -> {"run_id": ..., "path": ..., "mtime": ...} | 404
# If the backend differs, adjust _BACKEND_ENDPOINTS below — one place.
_BACKEND_ENDPOINTS = {"latest": "/index/latest", "run": "/index/runs/"}
BACKEND_TIMEOUT = 3  # seconds


def _rid_from(base: str) -> str:
    """Extract run id from a filename, stripping any known extension pair.
    A single rsplit(".", 1) is WRONG for .gz variants — it leaves '.jsonl'
    attached to the id, so --run-id could never match a gz log."""
    stem = base[len(RUN_PREFIX):]
    for ext in (".jsonl.gz", ".json.gz", ".jsonl", ".json"):
        if stem.endswith(ext):
            return stem[: -len(ext)]
    return stem


def _scan_runs(tmp_dir: str):
    """Scan filesystem for matching run files and return list of (mtime, path)."""
    patterns = [
        os.path.join(tmp_dir, f"{RUN_PREFIX}*.jsonl"),
        os.path.join(tmp_dir, f"{RUN_PREFIX}*.json"),
        os.path.join(tmp_dir, f"{RUN_PREFIX}*.jsonl.gz"),
        os.path.join(tmp_dir, f"{RUN_PREFIX}*.json.gz"),
    ]
    candidates = []
    for pat in patterns:
        for p in glob.glob(pat):
            try:
                candidates.append((os.path.getmtime(p), p))
            except OSError:
                continue
    return candidates


def _mtls_context():
    """Build an mTLS SSLContext from env-configured cert material, or None."""
    ca = os.environ.get("MCP_TLS_CA", "/etc/mtls/ca.crt")
    cert = os.environ.get("MCP_TLS_CERT", "/etc/mtls/client.crt")
    key = os.environ.get("MCP_TLS_KEY", "/etc/mtls/client.key")
    try:
        ctx = ssl.create_default_context(cafile=ca if os.path.exists(ca) else None)
        ctx.check_hostname = False
        if os.path.exists(cert) and os.path.exists(key):
            ctx.load_cert_chain(cert, key)
        return ctx
    except (ssl.SSLError, OSError):
        return None


def _backend_get(endpoint: str):
    """GET <MCP_INDEX_URL><endpoint> over mTLS. Return parsed dict or None.
    Never raises — backend unavailability degrades to filesystem fallback."""
    base = os.environ.get("MCP_INDEX_URL")
    if not base:
        return None
    ctx = _mtls_context()
    if ctx is None:
        return None
    url = base.rstrip("/") + endpoint
    try:
        with urllib.request.urlopen(url, context=ctx, timeout=BACKEND_TIMEOUT) as resp:
            doc = json.loads(resp.read().decode("utf-8"))
            return doc if isinstance(doc, dict) else None
    except Exception:
        return None


def _entry_ok(entry):
    """A backend index row is usable iff its file exists on disk."""
    return (isinstance(entry, dict)
            and isinstance(entry.get("path"), str)
            and os.path.exists(entry["path"]))


def find_latest_run(tmp_dir: str, run_id: str | None):
    """Return (run_id, path) of the newest matching run log, else (None, None).

    Index authority: the FastAPI/mTLS backend (SQLite). Filesystem scan is
    both fallback and cross-check.

    --run-id: backend lookup first; on miss or unusable row, live scan.

    no run-id ("latest"): backend answer is accepted ONLY if it is not
    older than the newest filesystem log (mtime compared). The backend
    indexes asynchronously — a log written after the last indexer pass
    would otherwise have the gate serve the previous run (wrong-but-green
    class). Backend lag loses to the filesystem; backend hit confirms.
    """
    if run_id:
        entry = _backend_get(_BACKEND_ENDPOINTS["run"] + run_id)
        if _entry_ok(entry):
            return run_id, entry["path"]
        # fallback: live scan
        candidates = _scan_runs(tmp_dir)
        for _, p in sorted(candidates, reverse=True):
            if _rid_from(os.path.basename(p)) == run_id:
                return run_id, p
        return None, None

    # "latest" — backend first, filesystem cross-check
    candidates = _scan_runs(tmp_dir)
    fs_best = max(candidates, default=None)  # (mtime, path) | None
    entry = _backend_get(_BACKEND_ENDPOINTS["latest"])
    if _entry_ok(entry):
        try:
            be_mtime = float(entry.get("mtime", 0))
        except (TypeError, ValueError):
            be_mtime = 0.0
        if fs_best is None or be_mtime >= fs_best[0] - 1e-9:
            rid = entry.get("run_id") or _rid_from(os.path.basename(entry["path"]))
            return rid, entry["path"]
        # backend is behind the filesystem — newest log not indexed yet
        pass
    if fs_best is None:
        return None, None
    return _rid_from(os.path.basename(fs_best[1])), fs_best[1]


def read_log(path: str):
    """Yield tool-call dicts from a .jsonl or .json log. Tolerate junk lines.
    Supports .gz compressed files transparently.
    """
    records = []
    opener = open
    if path.endswith(".gz"):
        opener = gzip.open
    if path.endswith(".jsonl") or path.endswith(".jsonl.gz"):
        try:
            with opener(path, "rt", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # malformed line: skip
        except OSError:
            return []
    else:
        try:
            with opener(path, "rt", encoding="utf-8", errors="replace") as fh:
                try:
                    doc = json.load(fh)
                except json.JSONDecodeError:
                    return records
            if isinstance(doc, list):
                records = doc
            elif isinstance(doc, dict):
                records = doc.get("calls", [doc])
        except OSError:
            return []
    return [r for r in records if isinstance(r, dict)]


def aggregate(calls):
    """Aggregate per-tool counts / failures / durations from arbitrary shapes."""
    agg = {}
    for c in calls:
        # tool name: several common field conventions
        name = None
        for key in ("tool", "tool_name", "function", "name", "method"):
            v = c.get(key)
            if isinstance(v, str) and v:
                name = v
                break
        if name is None:
            name = "<unknown>"
        entry = agg.setdefault(name, {"calls": 0, "failures": 0, "ok": 0,
                                      "total_ms": 0.0})
        entry["calls"] += 1
        # failure: explicit status/error fields, never guessed from absence
        failed = False
        if "error" in c and c["error"] not in (None, "", False):
            failed = True
        status = c.get("status") or c.get("result_status")
        if isinstance(status, str) and status.lower() in ("error", "failed", "failure"):
            failed = True
        if failed:
            entry["failures"] += 1
        else:
            entry["ok"] += 1
        dur = c.get("duration_ms") or c.get("elapsed_ms")
        if isinstance(dur, (int, float)):
            entry["total_ms"] += float(dur)
    return agg


def write_gate(tools_dir: str, gate_name: str, passed: bool, reason: str,
               run_id, agg, source_path: str):
    doc = {
        "gate": gate_name,
        "pass": passed,
        "reason": reason,
        "run_id": run_id,
        "source": source_path,
        "aggregated": agg,
        "tool_kinds": len(agg),
        "total_calls": sum(e["calls"] for e in agg.values()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    os.makedirs(tools_dir, exist_ok=True)
    out = os.path.join(tools_dir, f"{gate_name}.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return out, doc


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Aggregate MCP tool calls from the last run in /tmp/; "
                    "write Boolean gate result to /tools/.")
    ap.add_argument("--tmp", default=DEFAULT_TMP, help="log directory (default /tmp)")
    ap.add_argument("--tools", default=DEFAULT_TOOLS, help="output directory (default /tools)")
    ap.add_argument("--run-id", default=None, help="specific run id; newest if omitted")
    ap.add_argument("--gate-name", default="mcp_call_gate",
                    help="gate file name without .json (default mcp_call_gate)")
    ap.add_argument("--require-total", type=int, default=1,
                    help="minimum total calls for PASS (default 1)")
    args = ap.parse_args()

    rid, path = find_latest_run(args.tmp, args.run_id)
    if path is None:
        out, doc = write_gate(args.tools, args.gate_name, False,
                              "no MCP run log found under " + args.tmp,
                              None, {}, "<none>")
        print(f"FAIL {out}: {doc['reason']}")
        return 1

    calls = read_log(path)
    agg = aggregate(calls)
    total = sum(e["calls"] for e in agg.values())
    failures = sum(e["failures"] for e in agg.values())

    passed = total >= args.require_total and failures == 0
    if total < args.require_total:
        reason = (f"only {total} call(s) aggregated "
                  f"(< required {args.require_total})")
    elif failures > 0:
        reason = f"{failures} failed tool call(s) in run {rid}"
    else:
        reason = f"{total} call(s) across {len(agg)} tool(s), zero failures"

    out, doc = write_gate(args.tools, args.gate_name, passed, reason,
                         rid, agg, path)
    verdict = "PASS" if passed else "FAIL"
    print(f"{verdict} {out}: run={rid} total={total} kinds={len(agg)} "
          f"failures={failures}")
    for name, e in sorted(agg.items()):
        print(f"  {name}: {e['calls']} call(s), {e['failures']} failed")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
