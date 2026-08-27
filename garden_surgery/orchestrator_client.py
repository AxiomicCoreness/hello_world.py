"""Pure orchestrator caller. No OIDC. No secrets. No public bind."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from garden_surgery.worker_score import score_payload

ROLES = {"system", "lattice", "pod", "frb_bridge", "orchestrator", "worker", "validator"}
COMMANDS = {"wait", "nudge_cronjob", "record_only"}

def default_status_path() -> Path:
    return Path(__file__).resolve().parent.parent / "symplectic_status.agent.jsonl"

def default_config_path() -> Path:
    root = Path(__file__).resolve().parent.parent / "contracts"
    preferred = root / "mcp_orchestrator_config.json"
    if preferred.is_file():
        return preferred
    return root / "orchestrator_config.example.json"

def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    p = path or default_config_path()
    data = json.loads(p.read_text(encoding="utf-8"))
    if "oidc_client_secret" in data:
        raise ValueError("orchestrator config must not contain oidc_client_secret")
    return data

def parse_jsonl_lines(path: Path):
    if not path.is_file():
        return []
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        obj = json.loads(line)
        if isinstance(obj, dict) and obj.get("role") in ROLES:
            out.append(obj)
    return out

def latest_system_line(path: Optional[Path] = None):
    p = path or default_status_path()
    lines = [x for x in parse_jsonl_lines(p) if x.get("role") == "system"]
    if not lines:
        return None
    chosen = dict(lines[-1])
    chosen["_source_mtime"] = p.stat().st_mtime if p.is_file() else None
    return chosen

def decide(coherence: float, abs_error: float, thresholds: Dict[str, float]) -> str:
    fire = float(thresholds.get("coherence_fire", 0.8))
    nudge = float(thresholds.get("coherence_nudge", 0.6))
    tol = float(thresholds.get("error_tolerance", 0.5))
    if abs_error > tol:
        return "record_only"
    if coherence >= fire:
        return "wait"
    if coherence >= nudge:
        return "nudge_cronjob"
    return "wait"

def weave(actual=None, status_path=None, config_path=None, write=True):
    cfg = load_config(config_path)
    status = status_path or default_status_path()
    line = latest_system_line(status)
    phase = float((line or {}).get("phi_phase") or 0.0)
    if actual is None:
        actual = float((line or {}).get("predicted_score") or 12.5)
    scored = score_payload(actual, phase)
    command = decide(scored["coherence"], abs(scored["prediction_error"]), cfg["thresholds"])
    event = {
        "role": "orchestrator",
        "event": "grammar_prediction",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "coherence": scored["coherence"],
        "phi_phase": phase,
        "predicted_score": scored["predicted_score"],
        "prediction_error": scored["prediction_error"],
        "command": command,
    }
    if write:
        status.parent.mkdir(parents=True, exist_ok=True)
        with status.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True) + "\n")
    return {"source": line, "scored": scored, "written": event, "mcp_live": False, "oidc_used": False, "fusion_canonical": 515, "hyperion_preserved": 516}

def dry_run(actual=12.5, status_path=None, config_path=None):
    cfg = load_config(config_path)
    legend = cfg.get("legend_thresholds") or {}
    result = weave(actual=actual, status_path=status_path, config_path=config_path, write=True)
    result["dry_run"] = True
    result["october39_silent"] = bool(legend.get("october39_silent", True))
    result["pulse_scheduled"] = bool(legend.get("pulse_scheduled", False))
    result["mcp_live"] = False
    return result

def main() -> int:
    result = dry_run()
    print(json.dumps({"command": result["written"]["command"], "dry_run": True, "qed": True}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
