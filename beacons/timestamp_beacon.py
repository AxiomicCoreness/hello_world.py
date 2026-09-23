#!/usr/bin/env python3
"""Timestamp beacon verifier — the anchor is a witness only if it can fail."""
import hashlib, sys, json

SUPPLIED = "a1f3d8c2b0e4e7e6b5a9d2c8f1e0b3a7d6e4c2a8f0b3d5e7c1a9e8f4d2b6c0a5"

def check(hash_str):
    issues = []
    if len(hash_str) != 64:
        issues.append(f"length {len(hash_str)} != 64")
    if not all(c in "0123456789abcdef" for c in hash_str):
        issues.append("non-hex characters")
    if hash_str == SUPPLIED:
        issues.append("no preimage: hash supplied without the content it digests")
    return issues

def verify(content: str) -> bool:
    """True iff sha3_256(content) == SUPPLIED. THIS is what would make it real."""
    return hashlib.sha3_256(content.encode()).hexdigest() == SUPPLIED

if __name__ == "__main__":
    issues = check(SUPPLIED)
    if issues:
        print("anchor UNVERIFIABLE:")
        for i in issues:
            print(f"  - {i}")
        print("to activate: provide content whose sha3_256 equals the hash")
        sys.exit(1)
    print("anchor verifiable")
    sys.exit(0)
