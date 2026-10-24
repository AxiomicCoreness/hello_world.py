#!/usr/bin/env python3
"""Print (and optionally record) the SHA3-256 and sha256 of a GGUF.

    python seal_model_hash.py MODEL.gguf [--base BASE.gguf --template T.jinja
                                          --system-prompt P.txt --fewshot F.json --manifest MANIFEST.json]
    python seal_model_hash.py MODEL.gguf --check MANIFEST.json   # exit 1 on mismatch

Only hashes are written. This script never edits ledger/ or ledger.v2/; putting a
model hash in a ledger entry is a separate, owner-approved step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys


def digests(path: str) -> dict:
    s2, s3 = hashlib.sha256(), hashlib.sha3_256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 24), b""):
            s2.update(chunk)
            s3.update(chunk)
    return {"file": os.path.basename(path), "bytes": os.path.getsize(path),
            "sha256": s2.hexdigest(), "sha3_256": s3.hexdigest()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("model")
    ap.add_argument("--base")
    ap.add_argument("--template")
    ap.add_argument("--system-prompt")
    ap.add_argument("--fewshot")
    ap.add_argument("--manifest", help="write the manifest JSON here")
    ap.add_argument("--check", help="compare against this manifest; exit 1 on mismatch")
    a = ap.parse_args(argv)
    model = digests(a.model)
    print(f"sha3_256 {model['sha3_256']}  {model['file']}")
    print(f"sha256   {model['sha256']}  {model['file']}")
    if a.check:
        want = json.load(open(a.check, encoding="utf-8"))["model"]
        ok = all(want[k] == model[k] for k in ("file", "bytes", "sha256", "sha3_256"))
        print("manifest check:", "OK" if ok else "MISMATCH")
        return 0 if ok else 1
    if a.manifest:
        man = {"name": "ClarkeYoursaTee", "model": model,
               "base": digests(a.base) if a.base else None,
               "base_provenance": {
                   "gguf_repo": "mradermacher/Qwen2.5-1.5B-Instruct-abliterated-GGUF",
                   "weights": "huihui-ai/Qwen2.5-1.5B-Instruct-abliterated",
                   "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
                   "license": "apache-2.0"},
               "chat_template_sha256": digests(a.template)["sha256"] if a.template else None,
               "system_prompt_sha256": digests(a.system_prompt)["sha256"] if a.system_prompt else None,
               "fewshot_sha256": digests(a.fewshot)["sha256"] if a.fewshot else None,
               "change": "metadata only (general.name, general.description, default system prompt and few-shot turns); "
                         "tensors byte-identical to base; not fine-tuned"}
        with open(a.manifest, "w", encoding="utf-8") as fh:
            json.dump(man, fh, indent=2)
            fh.write("\n")
        print(f"manifest written: {a.manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
