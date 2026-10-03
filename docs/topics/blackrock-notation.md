# topics/blackrock-notation

Notation only. Not a witness. Search was soft-skipped.

Seal process, byte-exact:

1. Build body without the seal.
2. Canonical JSON: sort_keys, separators (',', ':'), ensure_ascii false.
3. seal = SHA3-256(those bytes).
4. The seal is printed beside the body. It is not inside the body.

body:

```json
{
  "kind": "notation",
  "not_a_witness": true,
  "not_a_measurement": true,
  "process": "canonicalize then sha3-256; seal is not a field of body",
  "excerpt": "BlackRock is an asset manager. Aladdin is a portfolio and risk platform. Capital allocation can move prices. The sovereign data layer is a label, not a measurement.",
  "held_out": [
    "digital twin that collapses a future",
    "risk phonemes",
    "ESG as a sovereign input protocol",
    "portfolios as reality edits"
  ],
  "untouched": "blob d13dea749b7cd29d081d41e2d14c8267bbaebeeb"
}
```

seal: df4ebc07a6cfadc6e007c84c6ae76a0e67141005ae9850facb062a5b77baea72
canon_len: 504
