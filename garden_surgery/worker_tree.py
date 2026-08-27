"""Worker sub-agent tree — parent / sibling / children configuration.

This is a *config graph*, not 144,008 live processes.
Hyperion 0516 is a sibling node (preserved). Fusion parent remains 515.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

TREE_VERSION = "9027"
FUSION_CANONICAL = 515
HYPERION_PRESERVED = 516

PARENT = {
    "id": "commander",
    "role": "parent",
    "label": "Clarke Yoursa Tee",
    "ledger": [515, 9022, 9023, 9024, 9025, 9026, 9027],
}

SIBLINGS: List[Dict[str, Any]] = [
    {"id": "theorems", "module": "garden_surgery.theorems", "role": "sibling", "surface": "check_theorems()"},
    {"id": "environment", "module": "garden_surgery.environment", "role": "sibling", "surface": "probe_environment()"},
    {"id": "surfaces", "module": "garden_surgery.surfaces", "role": "sibling", "surface": "probe_surfaces()"},
    {"id": "trigger_excavate", "module": "garden_surgery.trigger_excavate", "role": "sibling", "surface": "excavate()"},
    {
        "id": "declaration_flag",
        "module": "garden_surgery.declaration_flag",
        "role": "sibling",
        "bind": "127.0.0.1:8024",
        "surface": ["/health", "/diagnostic", "/diagnostic/htmx", "/workers/tree", "/workers/{id}", "/anomaly", "/override"],
        "children": ["diagnostic_json", "diagnostic_htmx", "health", "workers_tree", "worker_node"],
    },
    {"id": "hyperion_0516", "module": "ledger/0516.yaml", "role": "sibling", "preserved": True, "note": "HYPERION-16807-001 — do not rewrite"},
    {"id": "clarke_yoursa_tee_worker", "module": "clarke_yoursa_tee_worker.py", "role": "sibling", "bind": "127.0.0.1:8000"},
    {"id": "anomaly_distance", "module": "garden_surgery.anomaly_distance", "role": "sibling", "surface": ["payload()", "GET /anomaly"], "narrative": 8356},
]

SUBAGENTS: Dict[str, Dict[str, Any]] = {
    "diagnostic_json": {"parent": "declaration_flag", "route": "GET /diagnostic", "role": "sub-agent"},
    "diagnostic_htmx": {"parent": "declaration_flag", "route": "GET /diagnostic/htmx", "role": "sub-agent"},
    "health": {"parent": "declaration_flag", "route": "GET /health", "role": "sub-agent"},
    "workers_tree": {"parent": "declaration_flag", "route": "GET /workers/tree", "role": "sub-agent"},
    "worker_node": {"parent": "declaration_flag", "route": "GET /workers/{id}", "role": "sub-agent"},
}


def contract_path() -> Path:
    here = Path(__file__).resolve()
    root = here.parent.parent / "contracts"
    for name in ("worker_tree_9027.yaml", "worker_tree_9026.yaml", "worker_tree.yaml"):
        candidate = root / name
        if candidate.is_file():
            return candidate
    return root / "worker_tree.yaml"


def load_contract() -> Dict[str, Any]:
    path = contract_path()
    report: Dict[str, Any] = {"path": str(path), "present": path.is_file(), "version": None, "extends": None}
    if not path.is_file():
        return report
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version:"):
            report["version"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("extends:"):
            report["extends"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
    return report


def node(worker_id: str) -> Optional[Dict[str, Any]]:
    if worker_id == PARENT["id"]:
        return dict(PARENT)
    for s in SIBLINGS:
        if s["id"] == worker_id:
            return dict(s)
    if worker_id in SUBAGENTS:
        return dict(SUBAGENTS[worker_id], id=worker_id)
    return None


def parent_of(worker_id: str) -> Optional[str]:
    if worker_id == PARENT["id"]:
        return None
    if worker_id in SUBAGENTS:
        return SUBAGENTS[worker_id]["parent"]
    if any(s["id"] == worker_id for s in SIBLINGS):
        return PARENT["id"]
    return None


def children_of(worker_id: str) -> List[str]:
    if worker_id == PARENT["id"]:
        return [s["id"] for s in SIBLINGS]
    for s in SIBLINGS:
        if s["id"] == worker_id:
            return list(s.get("children") or [])
    return []


def siblings_of(worker_id: str) -> List[str]:
    pid = parent_of(worker_id)
    if pid is None:
        return []
    kids = children_of(pid)
    return [k for k in kids if k != worker_id]


def lineage(worker_id: str) -> List[str]:
    if node(worker_id) is None:
        return []
    chain: List[str] = [worker_id]
    seen = {worker_id}
    cur = worker_id
    while True:
        pid = parent_of(cur)
        if pid is None or pid in seen:
            break
        chain.append(pid)
        seen.add(pid)
        cur = pid
    chain.reverse()
    return chain


def all_ids() -> List[str]:
    ids = [PARENT["id"]]
    ids.extend(s["id"] for s in SIBLINGS)
    ids.extend(SUBAGENTS.keys())
    return ids


def tree_payload() -> Dict[str, Any]:
    return {
        "version": TREE_VERSION,
        "parent": PARENT,
        "siblings": SIBLINGS,
        "subagents": SUBAGENTS,
        "edges": {
            "parent_of": {n: parent_of(n) for n in all_ids() if parent_of(n)},
            "children_of": {n: children_of(n) for n in all_ids() if children_of(n)},
        },
        "fusion_canonical": FUSION_CANONICAL,
        "hyperion_preserved": HYPERION_PRESERVED,
        "mcp": False,
        "instantiates_144008_processes": False,
        "contract": load_contract(),
    }
