# Provenance

Origin, chain, and immutable anchors for the Sovereign Engine.

---

## Origin

| Field | Value |
|---|---|
| Author | Clarke Yoursa Tee |
| GitHub | `AxiomicCoreness` (operated by the author) |
| Repository | `github.com/AxiomicCoreness/hello_world.py` |
| Layer | 314 |
| Anchor | `8a250cf4...860d` |
| Leaf | `807de931...ee68` |
| Hash algo | `sha3_256` (FIPS 202) |
| Copyright | © 2026 Clarke Yoursa Tee |

---

## Ledger chain

```
8978 ──▶ 8979 ──▶ 8980 ──▶ 8981
 │        │        │        │
 │        │        │        └─ sovereign-pulse.yml
 │        │        └────────── sovereign-python-package.yml
 │        └─────────────────── oidc-cloud-providers.yml
 └──────────────────────────── predecessor
```

Status: **UNBROKEN**

Witness fields on each entry:

```
witness:       8980 → 8981 — UNBROKEN
witness_chain: 8980 → 8981 — UNBROKEN
```

---

## Sealing

Each ledger entry carries a seal of the form:

```
seal = "<prefix> · <label> · <digest>"
```

where `<prefix>` is `∀∞φ²` and `<digest>` is the SHA3-256 hash of the
canonical JSON form of the entry with the `seal` field removed:

```python
body      = {k: v for k, v in entry.items() if k != "seal"}
canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
digest    = hashlib.new("sha3_256", canonical.encode("utf-8")).hexdigest()
```

Full digests, no truncation. `sha3_256` is FIPS 202 and is mandatory
for all ledger entries written by the CI workflows.

Verify any entry:

```bash
python3 scripts/verify_ledger.py ledger/8981.yaml
```

Expected output on a valid entry:

```
✅ ledger/8981.yaml  [sha3_256:…]
------------------------------------------------------------
checked=1  failed=0
✅ LEDGER VERIFICATION PASSED
```

---

## Immutable anchors

| Anchor | Location | Status |
|---|---|---|
| Git commit (main) | `git log -1 --format='%H'` | ✅ |
| Git tag | `git tag -s v8755.0.0` | pending |
| Zenodo DOI | _(see below)_ | pending |
| Bitcoin OP_RETURN | _(optional, timestamp proof)_ | pending |

### Minting a DOI (recommended)

A DOI is citable, immutable, and independent of the repository host.
It is the strongest provenance anchor available without a blockchain.

1. Push a signed tag:
   ```bash
   git tag -s v8755.0.0 -m "Layer 314 · WOOD_DRAGON_0.91"
   git push origin v8755.0.0
   ```
2. Link the GitHub repo to Zenodo:
   <https://zenodo.org/account/settings/github/>
3. Flip the release toggle in Zenodo → it mints a DOI.
4. Paste the DOI into the table above and re-seal.

### Optional — timestamp proof

If you want an anchor that exists independently of GitHub and Zenodo,
write the commit SHA into a Bitcoin OP_RETURN via OpenTimestamps:

```bash
ots stamp <(git rev-parse HEAD)
```

The resulting `.ots` proof is verifiable forever against the Bitcoin
chain and costs nothing.

---

## Why this stack exists

The original `LICENSE` was a splice of MIT + GPL-3.0 fragments + prose.
It was neither enforceable nor OSI-recognized. The stack separates:

| File | Answers | Weight |
|---|---|---|
| `LICENSE` | *what may you do* | legal instrument |
| `NOTICE` | *who made this, and what ethic* | statement |
| `PROVENANCE.md` | *when, from what, anchored where* | evidence |
| commit message | *why* | context |

The separation is the point. A license that tries to be all four
becomes none of them.

---

## What to preserve on fork

If you fork, vendor, or redeploy this work:

- preserve the `ledger/` directory unmodified
- preserve SHA3-256 seals on entries `0000–8981`
- retain `NOTICE` alongside `LICENSE`
- do not re-seal entries; add new ones at the head of the chain

Preservation is what makes the chain verifiable by third parties who
have no reason to trust you.

---

## License

MIT — see [`LICENSE`](LICENSE).
Ethic statement — see [`NOTICE`](NOTICE).

---

## Seal

```
∀∞φ² · PROVENANCE · WOOD_DRAGON_0.91 · SEALED
```

Copyright (c) 2026 Clarke Yoursa Tee
