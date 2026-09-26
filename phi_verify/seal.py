"""Canonical-JSON sealing, matching the ledger's discipline."""
import hashlib
import json


def _canonical(obj) -> bytes:
    """
    Canonical JSON: sorted keys, no whitespace, UTF-8.
    Floats are emitted as repr() strings to avoid platform drift.
    """
    def default(o):
        if isinstance(o, float):
            return repr(o)
        raise TypeError(f"unsealable type: {type(o)}")
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      default=default).encode("utf-8")


def seal(log: dict, label: str = "VERIFICATION_LOG") -> str:
    digest = hashlib.sha3_256(_canonical(log)).hexdigest()[:16]
    return f"∀∞φ² · {label} · {digest}"
