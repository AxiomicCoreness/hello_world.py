#!/usr/bin/env python3
"""
verify_phi9_unitary.py — Clarke Yoursa Tee

Verifies sha3_256(b"wood-dragon-0.91")[:16] and φ⁹ unitary angles.
Pure stdlib. Numbers come from this process — not from prior traced claims.
"""
import hashlib
import math

PHI = (1 + math.sqrt(5)) / 2

key = hashlib.sha3_256(b"wood-dragon-0.91").hexdigest()[:16]
print(f"sha3_256(wood-dragon-0.91)[:16] = {key}")
print("disproven trace claim           = 3f4c2b1a9e7d8c6f")
print()

theta = PHI ** 9
mod = theta % (2 * math.pi)
c, s = math.cos(theta), math.sin(theta)

print(f"phi^9          = {theta:.15f} rad")
print(f"theta mod 2pi  = {mod:.15f} rad")
print(f"cos(theta)     = {c:.15f}")
print(f"sin(theta)     = {s:.15f}")
print(f"cos^2+sin^2    = {c*c + s*s:.15f}")
