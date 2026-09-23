# Timestamp Beacon — content witness (no seal)
#
# beacons/timestamp.md — records the temporal anchor pushed to this branch.
#
# The supplied hash below is recorded VERBATIM but flagged: a cryptographic
# anchor requires the hash to be COMPUTED from content. A hash supplied
# without the content it digests cannot be verified — it is a claim, not
# a witness. See checks in timestamp_beacon.py.

supplied_hash: a1f3d8c2b0e4e7e6b5a9d2c8f1e0b3a7d6e4c2a8f0b3d5e7c1a9e8f4d2b6c0a5
supplied_hash_length: 64
recorded_at: 2026-09-23T20:53:58.223Z
verifiable: false — no preimage provided
status: UNVERIFIABLE_ANCHOR
disposition: pending content whose sha3_256 equals the supplied hash
