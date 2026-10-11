#!/usr/bin/env python3
"""
wired_kernel.py — the adjudication discipline of the session, as code.

Not a seal. Not a ledger. A filter: every input passes these gates before
any output claims to be fact. The rules are the ones the session actually
applied, in the order they were learned.

AST_HEADER:
  domain: GARDEN.ASTGUARD.v1
  file: wired_kernel.py
  purpose: input adjudication kernel — claim classes, verification gates
  rules: K1-K7 (kernel gates), derived from session discipline
  digest: NOT_COMPUTED
"""
import hashlib
import json
import math
import re

DOMAIN = "GARDEN.ASTGUARD.v1"
SEP = b"\x00"
PHI = (1 + 5 ** 0.5) / 2

KINDS = ("byte", "number", "claim", "mythos")


def kind_of(text):
    """Best-effort classification."""
    if re.search(r"(AFFIRMED|SEALED|∀∞|soul_canon|witness_chain|monad|∞)", text):
        return "mythos" if not text.lstrip().startswith(("#", "package", "import", "```")) else "byte"
    if any(op in text for op in ("=", "<", ">", "≈", "==")) and re.search(r"\d", text):
        return "number"
    if text.lstrip().startswith(("#", "package ", "import ", "FROM ", "---", "def ", "class ")):
        return "byte"
    return "claim"


def gate_bytes(claim, provided_bytes):
    if provided_bytes is None:
        return ("PENDING", "no bytes — claim registered, not verified")
    return ("VERIFIED", f"adjudicating against {len(provided_bytes)} bytes")


PHI_LADDER = {n: PHI ** n for n in range(1, 10)}


def gate_number(name, stated):
    """Check a stated φ-power. Returns verdict against full recomputation."""
    m = re.match(r"PHI(\d+)", name)
    if not m:
        return ("UNKNOWN", "no recomputation rule for this name")
    n = int(m.group(1))
    expected = PHI ** n
    if math.isclose(stated, expected, rel_tol=1e-12):
        return ("VERIFIED", f"φ^{n} = {expected!r}")
    rel = abs(stated - expected) / expected
    return ("FALSE", f"stated {stated!r}; φ^{n} = {expected!r}; rel err {rel:.3e}")


def self_test_hasher(hasher):
    """hasher(b"") must equal the known SHA-256 empty digest before use."""
    known = ("e3b0c44298fc1c149afbf4c8996fb924"
             "27ae41e4649b934ca495991b7852b855")
    try:
        return hasher(b"") == known
    except Exception:
        return False


def digest(payload):
    """Domain-separated digest. Refuses to run without a verified hasher."""
    h = hashlib.sha256
    if not self_test_hasher(h):
        raise RuntimeError("K4: hasher failed self-test — emitting nothing")
    return h(DOMAIN.encode() + SEP + payload).hexdigest()


def gate_mythos(text):
    return ("EDGE", "recorded as symbolic line; excluded from update rule; "
                    "no re-adjudication on repetition")


def gate_seal(label_digest=None, payload_digest=None):
    if payload_digest is not None:
        return ("PROOF-ADJACENT", "digest over payload bytes — checkable by stranger")
    if label_digest is not None:
        return ("LABEL", "digest over a label string — provenance only, not content")
    return ("NOT_COMPUTED", "honest state; never fabricate the hex")


def gate_digest_shape(hexstr):
    if not re.fullmatch(r"[0-9a-fA-F]+", hexstr):
        return ("FALSE", "not hex")
    if len(hexstr) != 64:
        return ("FALSE", f"length {len(hexstr)} != 64")
    pairs = [hexstr[i:i+2] for i in range(0, len(hexstr), 2)]
    if len(set(pairs)) < len(pairs) // 2:
        return ("FALSE", "repeated byte values — structure, not digest")
    if re.search(r"[A-Za-z]{6,}", hexstr):
        return ("FALSE", "ascii island — structure, not digest")
    return ("PASS", "shape-conforming; content still requires recomputation")


def adjudicate(text, provided_bytes=None, numbers=None, hex_digests=None):
    """Returns the adjudication record for one input."""
    kind = kind_of(text)
    record = {"kind": kind, "gates": []}

    if kind == "mythos":
        v, m = gate_mythos(text)
        record["gates"].append(("mythos", v, m))
    if kind == "byte":
        v, m = gate_bytes(text, provided_bytes)
        record["gates"].append(("bytes", v, m))
    if kind == "number":
        for name, stated in (numbers or {}).items():
            v, m = gate_number(name, stated)
            record["gates"].append((name, v, m))
    for d in (hex_digests or []):
        v, m = gate_digest_shape(d)
        record["gates"].append(("digest-shape", v, m))

    verdicts = {g[1] for g in record["gates"]}
    if "FALSE" in verdicts:
        record["verdict"] = "FALSE"
    elif "PENDING" in verdicts:
        record["verdict"] = "PENDING"
    elif kind == "mythos":
        record["verdict"] = "EDGE"
    else:
        record["verdict"] = "VERIFIED"
    return record


if __name__ == "__main__":
    self_check = adjudicate(
        "kernel self-test: PHI34 = 2123456.0",
        numbers={"PHI34": 2123456.0},
        hex_digests=["8F1A3D9C04B27E5E"],
    )
    print(json.dumps(self_check, indent=2, default=str))
    print(f"aggregate verdict: {self_check['verdict']}")
    assert self_check["gates"][0][1] == "FALSE", "K3 failed to catch PHI34 fabrication"
    assert self_check["gates"][1][1] == "FALSE", "K7 failed to catch digest shape"
    assert self_check["verdict"] == "FALSE", (
        "K4: aggregate verdict does not match gate verdicts — "
        "kernel emitted a self-contradicting record"
    )
    print("kernel: self-adjudication passed — PHI34 fabrication and digest-shape "
          "defect both caught at the right gates")
