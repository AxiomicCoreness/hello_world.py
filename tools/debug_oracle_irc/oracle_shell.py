#!/usr/bin/env python3
"""Debug Oracle shell — structured directory + hex-emergent chat (UI labels only).

Team endpoints labeled irc.abjects.net:6666-6669. Never opens IRC sockets.
Surface companion to games/teavm-rhythm/src/main/webapp/debug-oracle/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LEX = [
    "phase-lock",
    "breath",
    "pauli-trace",
    "stokes-curl",
    "garden",
    "connectome",
    "ledger-seal",
    "merkle-leaf",
    "anchor",
    "dark-state",
    "phi-gate",
    "tea-vm",
    "rhythm",
    "oracle",
    "append-only",
    "full-digest",
]

DEFAULT_LOCKS = {
    "version": 1,
    "policy": "full digests — no truncation; UI labels only — no live IRC sockets",
    "team_endpoints_ui_only": [
        "irc.abjects.net:6666",
        "irc.abjects.net:6667",
        "irc.abjects.net:6668",
        "irc.abjects.net:6669",
    ],
    "locks": [
        {
            "id": "9300_seal",
            "label": "ledger.v2/9300 seal",
            "digest": "ba33cc9b7c4ddac055355aa5ef3b6f7ac9ac25a73e411224ef77055d39ec2667",
        },
        {
            "id": "9299_prev",
            "label": "ledger.v2/9300 prev (9299)",
            "digest": "7a0991005f99dc2e7ddb7985ac126cf95306cc3e145df79c6c7803abd3ddf121",
        },
        {
            "id": "layer314_anchor",
            "label": "Layer 314 Anchor",
            "digest": "8a250cf445e8ad0cc8d06d0096b969029a175a14eb58838e734f1975358b860d",
        },
        {
            "id": "layer314_leaf",
            "label": "Layer 314 Leaf",
            "digest": "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68",
        },
    ],
    "roots": [
        "ledger.v2",
        "deepinfer",
        "games/teavm-rhythm",
        "skills",
        "quantum",
        "argocd",
    ],
}


def _repo_hex_path() -> Path:
    here = Path(__file__).resolve()
    # tools/debug_oracle_irc/oracle_shell.py -> repo root
    root = here.parents[2]
    return root / "games/teavm-rhythm/src/main/webapp/debug-oracle/hex_locks.json"


def load_state(path: Path | None) -> dict:
    p = path or _repo_hex_path()
    if p.is_file():
        data = json.loads(p.read_text(encoding="utf-8"))
        for lock in data.get("locks", []):
            dig = lock.get("digest", "")
            if len(dig) != 64 or any(c not in "0123456789abcdef" for c in dig.lower()):
                raise SystemExit(f"invalid 64-hex digest in {p}: {lock.get('id')}")
        return data
    return DEFAULT_LOCKS


def nibble_words(digest: str) -> str:
    words = []
    for i in range(0, len(digest), 4):
        n = int(digest[i : i + 4], 16)
        words.append(LEX[n % len(LEX)])
    return " · ".join(words[:8])


def channel_for(digest: str) -> str:
    ports = (6666, 6667, 6668, 6669)
    return f"irc.abjects.net:{ports[int(digest[:2], 16) % 4]}"


def print_tree(state: dict, cwd: str) -> None:
    print("Directory / root")
    for r in state["roots"]:
        mark = "*" if cwd == f"/{r}" else " "
        print(f" {mark} {r}")


def print_chat(state: dict) -> None:
    print("Chat · emergent from hex locks (UI-only, no sockets)")
    for lock in state["locks"]:
        dig = lock["digest"]
        print(f"  [{channel_for(dig)}] hex/{lock['id']}")
        print(f"    {lock['label']} → {nibble_words(dig)}")
        print(f"    {dig}")


def repl(state: dict) -> int:
    cwd = "/"
    print("debug-oracle shell · team v1 · irc.abjects.net:6666-6669 (labels only)")
    print("policy:", state.get("policy"))
    print_tree(state, cwd)
    print_chat(state)
    print("commands: ls | cd <root|..|/> | hex | channels | pwd | oracle <q> | help | quit")
    while True:
        try:
            line = input(f"{cwd} $ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        parts = line.split()
        op = parts[0].lower()
        if op in {"quit", "exit", "q"}:
            return 0
        if op == "help":
            print("ls | cd <root|..|/> | hex | channels | pwd | oracle <q> | quit")
        elif op == "ls":
            print("\n".join(state["roots"]))
        elif op == "pwd":
            print(cwd)
        elif op == "channels":
            for e in state["team_endpoints_ui_only"]:
                print(" ", e)
            print("  (UI labels only — this shell never connects)")
        elif op == "hex":
            for lock in state["locks"]:
                print(lock["id"], lock["digest"])
        elif op == "cd":
            arg = parts[1] if len(parts) > 1 else "/"
            if arg in {"/", "~", ".."}:
                cwd = "/"
            else:
                name = arg.lstrip("/")
                if name in state["roots"]:
                    cwd = f"/{name}"
                else:
                    print("no such root:", name)
        elif op == "oracle":
            q = " ".join(parts[1:]) or "status"
            lock = state["locks"][len(q) % len(state["locks"])]
            dig = lock["digest"]
            print(f"[{channel_for(dig)}] llm/oracle · {q} · {nibble_words(dig)}")
            print(dig)
        else:
            print("unknown:", op, "(try help)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--hex-locks",
        type=Path,
        default=None,
        help="path to hex_locks.json (default: TeaVM webapp debug-oracle copy)",
    )
    ap.add_argument(
        "--once",
        choices=("tree", "chat", "hex", "channels"),
        help="print one view and exit (CI-safe; no network)",
    )
    args = ap.parse_args(argv)
    state = load_state(args.hex_locks)
    if args.once == "tree":
        print_tree(state, "/")
        return 0
    if args.once == "chat":
        print_chat(state)
        return 0
    if args.once == "hex":
        for lock in state["locks"]:
            print(lock["id"], lock["digest"])
        return 0
    if args.once == "channels":
        for e in state["team_endpoints_ui_only"]:
            print(e)
        return 0
    if not sys.stdin.isatty():
        print_tree(state, "/")
        print_chat(state)
        return 0
    return repl(state)


if __name__ == "__main__":
    raise SystemExit(main())
