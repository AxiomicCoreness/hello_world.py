"""Minimal state carrier for the CI/CD key rotation lane. Rev 3.

Offline-first, evolution-capable (the "federate works offline yet
evolves" rewire):

- State path is env-overridable (CI_CD_ROTATOR_STATE). CI points it at
  a repo-committed file, so rotation state evolves across runs with
  zero cloud dependency. Default remains the local file so bare use is
  unchanged.
- rotate() performs a REAL offline rotation: increments rotation_count,
  stamps the rotation time, persists atomically (tmp + replace).
- Federation (AWS Secrets Manager) is ci_cd_key_rotator_aws.py's lane.
  This module makes no network calls and requires none. When a cloud
  role is configured, the workflow runs the federated path and then
  persists the count to the same committed state file, so the state
  evolves continuously across mode switches.

Contract (unchanged from rev 2; the workflow instantiates bare):
  __init__()      - no arguments
  load_state()    - True if the state file existed and parsed
  save_state()    - persists the state file (atomic)
  rotation_count  - int, set by load_state (0 on fresh run)

No AWS calls. No seals. No witness claims. This module can fail:
missing or corrupt state -> load_state() returns False.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STATE_PATH = "ci_cd_key_rotator_state.json"


def state_path() -> Path:
    return Path(os.environ.get("CI_CD_ROTATOR_STATE", DEFAULT_STATE_PATH))


class CI_CD_KeyRotator:
    def __init__(self) -> None:
        self.rotation_count: int = 0
        self.last_rotation: str = ""
        self.mode: str = "OFFLINE"

    def load_state(self) -> bool:
        p = state_path()
        if not p.is_file():
            return False
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        if not isinstance(data, dict):
            return False
        count = data.get("rotation_count", 0)
        if not isinstance(count, int) or count < 0:
            return False
        self.rotation_count = count
        last = data.get("last_rotation", "")
        self.last_rotation = last if isinstance(last, str) else ""
        return True

    def rotate(self) -> dict:
        """Offline rotation: increment, stamp, persist. Can be verified."""
        self.rotation_count += 1
        self.last_rotation = datetime.now(timezone.utc).isoformat()
        self.save_state()
        return {
            "rotation_count": self.rotation_count,
            "mode": self.mode,
            "last_rotation": self.last_rotation,
            "key_fingerprint": "offline: no key material (local lane)",
        }

    def save_state(self) -> None:
        p = state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(
            json.dumps(
                {
                    "rotation_count": self.rotation_count,
                    "last_rotation": self.last_rotation,
                    "mode": self.mode,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        tmp.replace(p)
