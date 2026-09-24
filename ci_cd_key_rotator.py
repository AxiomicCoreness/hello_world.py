"""Minimal state carrier for the CI/CD key rotation lane.

Replaces the prior version of this file, which carried asserted class
attributes (witness_continuity "1 -> 711 - UNBROKEN", a ceremonial seal
string) with nothing backing them. Those asserted constants are removed
rather than renamed. This version makes no witness or seal claims.

Contract (the workflow instantiates CI_CD_KeyRotator() bare):
  __init__()      - no arguments
  load_state()    - True if a state file existed and was loaded
  save_state()    - persists the state file
  rotation_count  - int, set by load_state (0 on fresh run)

No AWS calls - the AWS half is ci_cd_key_rotator_aws.py. Pure stdlib.
This module can fail: missing or corrupt state file -> load_state() False.
"""
import json
from pathlib import Path

STATE_PATH = Path("ci_cd_key_rotator_state.json")


class CI_CD_KeyRotator:
    def __init__(self) -> None:
        self.rotation_count: int = 0

    def load_state(self) -> bool:
        if not STATE_PATH.is_file():
            return False
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        if not isinstance(data, dict):
            return False
        count = data.get("rotation_count", 0)
        if not isinstance(count, int) or count < 0:
            return False
        self.rotation_count = count
        return True

    def save_state(self) -> None:
        STATE_PATH.write_text(
            json.dumps(
                {"rotation_count": self.rotation_count},
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
