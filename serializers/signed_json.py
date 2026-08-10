import json
import hmac
import hashlib
from typing import Any


class SignedJSON:
    """
    JSON serializer with HMAC signature verification for tamper detection.
    """

    def __init__(self, key: bytes):
        self.key = key

    def save(self, obj: Any, path: str) -> None:
        payload_bytes = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        sig = hmac.new(self.key, payload_bytes, hashlib.sha256).hexdigest()
        wrapper = {"__signature": sig, "payload": json.loads(payload_bytes)}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(wrapper, f, indent=2, ensure_ascii=False)

    def load(self, path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        sig = data.get("__signature")
        payload = data.get("payload")
        if sig is None or payload is None:
            raise ValueError("Signed JSON invalid format")
        payload_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        expected = hmac.new(self.key, payload_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            raise ValueError("Signature mismatch: file may have been tampered")
        return payload

    def dumps(self, obj: Any) -> str:
        """Return signed wrapper as a JSON string (in-memory; no path)."""
        payload_bytes = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        sig = hmac.new(self.key, payload_bytes, hashlib.sha256).hexdigest()
        wrapper = {"__signature": sig, "payload": json.loads(payload_bytes)}
        return json.dumps(wrapper, ensure_ascii=False)

    def loads(self, text: str) -> Any:
        """Verify and return payload from a signed JSON string."""
        data = json.loads(text)
        sig = data.get("__signature")
        payload = data.get("payload")
        if sig is None or payload is None:
            raise ValueError("Signed JSON invalid format")
        payload_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        expected = hmac.new(self.key, payload_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            raise ValueError("Signature mismatch: file may have been tampered")
        return payload
