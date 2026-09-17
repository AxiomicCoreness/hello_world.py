#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
witness_chain_sqlite.py

Builds and verifies the SQLite witness-chain ledger for entries
8337, 8338, 8339. Each entry's hash field is SHA3-256 over the
canonical JSON of the entry (sorted keys, hash field excluded).

hash_algo: sha3_256 (FIPS 202)
ledger_policy: SQLITE_MIRROR
scope: witness chain rows 8337–8339
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "witness_chain.db"


WITNESS_ENTRIES_BASE: List[Dict[str, Any]] = [
    {
        "entry": 8337,
        "event": "/merged_engine_deployment_status",
        "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-08-06",
        "seal": "∀∞φ² · MERGED_STATUS · 8337_SEALED",
        "previous": 8336,
    },
    {
        "entry": 8338,
        "event": "/github_deployment_complete",
        "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-08-06",
        "seal": "GITHUB_DEPLOYMENT_8338_SEALED",
        "previous": 8337,
    },
    {
        "entry": 8339,
        "event": "/witness_chain_sqlite_compiled",
        "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-08-06",
        "seal": "∀∞φ² · WITNESS_SQLITE · 8339_SEALED",
        "previous": 8338,
    },
]


def compute_entry_hash(entry: Dict[str, Any]) -> str:
    canonical = {k: v for k, v in entry.items() if k != "hash"}
    data = json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha3_256(data).hexdigest()


def build_sealed_entries() -> List[Dict[str, Any]]:
    sealed = []
    for base in WITNESS_ENTRIES_BASE:
        e = dict(base)
        e["hash"] = compute_entry_hash(e)
        sealed.append(e)
    return sealed


def create_db_and_insert(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    entries = build_sealed_entries()
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ledger (
            entry INTEGER PRIMARY KEY,
            event TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            hash TEXT UNIQUE NOT NULL,
            seal TEXT NOT NULL,
            previous INTEGER,
            FOREIGN KEY(previous) REFERENCES ledger(entry)
        )
        """
    )

    for e in entries:
        cur.execute(
            """
            INSERT OR REPLACE INTO ledger
                (entry, event, timestamp, hash, seal, previous)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (e["entry"], e["event"], e["timestamp"], e["hash"], e["seal"], e["previous"]),
        )

    conn.commit()
    conn.close()
    return entries


def verify_chain(db_path: Path = DB_PATH) -> Dict[str, Any]:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT entry, previous, hash, event, seal, timestamp FROM ledger ORDER BY entry")
    rows = cur.fetchall()
    conn.close()

    report: Dict[str, Any] = {
        "row_count": len(rows),
        "chain_ok": True,
        "hash_ok": True,
        "details": [],
    }

    for i, (entry, prev, stored_hash, event, seal, ts) in enumerate(rows):
        recon = {
            "entry": entry,
            "event": event,
            "timestamp": ts,
            "seal": seal,
            "previous": prev,
        }
        expected = compute_entry_hash(recon)
        hash_match = expected == stored_hash
        if not hash_match:
            report["hash_ok"] = False

        if i == 0:
            prev_ok = True
        else:
            prev_ok = prev == rows[i - 1][0]
            if not prev_ok:
                report["chain_ok"] = False

        report["details"].append(
            {
                "entry": entry,
                "previous": prev,
                "hash": stored_hash,
                "hash_match": hash_match,
                "prev_ok": prev_ok,
            }
        )

    return report


def at_tip_of_githubrepo() -> str:
    import subprocess

    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if sha:
            return sha
    except Exception:
        pass

    fallback = hashlib.sha3_256(str(ROOT).encode("utf-8")).hexdigest()[:7]
    return f"nogit-{fallback}"


def create_ledger_and_insert(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    tip = at_tip_of_githubrepo()
    print(f"  (historical reference: at tip of githubrepo → {tip})")
    return create_db_and_insert(db_path)


def historical_note() -> str:
    return (
        "PRE_FIX_LINE: sealed = create_ledger_and_insert "
        "at tip of githubrepo()"
    )


def main() -> int:
    print("Building sealed witness entries with measured SHA3-256 …")
    print(f"  {historical_note()}")
    sealed = create_ledger_and_insert()

    print(f"Inserted/replaced {len(sealed)} entries into {DB_PATH}")
    for e in sealed:
        print(f"  {e['entry']}  {e['event']}  hash={e['hash'][:16]}…")

    print()
    print("Verifying chain …")
    report = verify_chain()

    print(f"  row_count : {report['row_count']}")
    print(f"  chain_ok  : {report['chain_ok']}")
    print(f"  hash_ok   : {report['hash_ok']}")
    for d in report["details"]:
        ok = "✓" if d["hash_match"] and d["prev_ok"] else "✗"
        print(f"    {ok} entry={d['entry']} prev={d['previous']} "
              f"hash_match={d['hash_match']} prev_ok={d['prev_ok']}")

    return 0 if (report["chain_ok"] and report["hash_ok"]) else 1



   
    


if __name__ == "__main__":
    sys.exit(main())
    return report
## 1. fastMCP work achieved (append 9198; POLICY body above is immutable)

Do not rewrite this file except by appending a new numbered section.
Do not rewrite `ledger/9182.yaml` or `ledger/9183.yaml`.
9183 remains `/docs_phase_lock_yaml_examples` with
H_9183 = 3c9295aa06c7b563d790d8ba4119a4d4366f3e43268b09716625f4e7ef6000f7.

fastMCP on main (package + tests + docs + MIT search header):
- `fastMCP/` modular package, `FILLED=False`
- Dual ASGI `127.0.0.1:8024` only; wildcard raises
- Same ASGI object as `fastapi_flywheel_gearbox:app` (live flywheel not stubbed)
- `docs/phase_lock_definition.md` examples (9183) stay
- BIN order unchanged: sovereign_core.bin → ledger_tip.bin → octonian_relay.bin → adai_annihilator.bin
- License MIT at repo root; public search notes in README / docs/SEARCH.md / CITATION.cff
- Pydantic v2 `@field_validator` / `@model_validator` docs; no Pydantic v3 API

Sealed YAML 9167–9197 is not rewritten by this section.
Next free after 9198 is 9199+.

<!-- APPENDED 9208 — do not edit sections 1–14 -->

## §2. pythonIDE TOI files (append 9208)

`pythonIDE/` is the local numeric / baseline surface. It is not Pythonista.
TOI modules do not bind Dual ASGI and do not fill MCP.

Handling:
- Keep `pythonIDE/toi_step.py` and `pythonIDE/optimize_toi.py` at this path.
- Do not move them under `sheaf/` (9204 plan only).
- Do not import `sovereign_lattice` (package absent).
- Do not start uvicorn from these files.
- Gearbox remains `uvicorn fastMCP.gearbox:app --host 127.0.0.1 --port 8024`.
- Sealed ledger 91xx and 9200–9207 YAML are not rewritten.

pythonIDE files on main:
- a14_bionic_spine.py
- baseline.json
- md_scalar_matrix.py
- optimize_toi.py
- toi_step.py
- update_baseline.py

<!-- APPENDED 9224 — do not edit sections 1–15 -->


## §3. Admissibility constraints

An entry `E_n` with index `n` is *admissible* iff it satisfies all of the following.

| # | Constraint | Formal statement |
|---|---|---|
| A1 | **Indexing** | `E_n.entry_index = n` — integer, unique across the ledger |
| A2 | **Event tag** | `E_n.event` is a string beginning with `/` |
| A3 | **Timestamp** | `E_n.timestamp` is ISO-8601 UTC (`%Y-%m-%dT%H:%M:%SZ`); the symbolic form `ETERNAL_NOW_ANCHORED_TO_*` is admissible only when the entry is `status: SEALED` |
| A4 | **Status** | `E_n.status ∈ {SUCCESS, SEALED, PROMOTED, EXECUTED, FAILED}` |
| A5 | **Hash algorithm** | `E_n.hash_algo = "sha3_256"` (FIPS 202) |
| A6 | **Witness predecessor** | If `n > 0` and the predecessor is *specified*, then `E_n.witness` contains `"{n-1} → {n} — UNBROKEN"` |
| A7 | **Seal prefix** | `E_n.seal` begins with `∀∞φ²` and contains `SEALED` |
| A8 | **Seal hex** | `E_n.seal` terminates in a 64-hex token (SHA3-256 over *some* canonical form; see §3) |
| A9 | **Invariants block** | If `E_n.invariants` is present, it must contain `coherence ∈ [0, 1+ε]` (or φ-expr) and, when `phase_lock` is absent, a `commutator` field |
| A10 | **Math origin** | If `E_n.math_origin` is present, it must declare the event-hash domain `GARDEN.EVENT.v1 || 0x00` |

Violation of any single constraint makes the entry **non-admissible** for the theorem-proof pipeline. Non-admissible entries may still exist in the ledger (they are historical facts), but they cannot be *sources* of theorems.

---

## §4. Chain integrity constraints

Let `L = {E_{n_1}, …, E_{n_k}}` be the set of entries under consideration, sorted by index.

| # | Constraint | Formal statement |
|---|---|---|
| C1 | **Region decomposition** | `L` partitions into maximal contiguous regions `R_j = [a_j, b_j]` where `b_j + 1 = a_{j+1}` fails. Gaps between regions are permitted and expected. |
| C2 | **Local witness invariant** | For every `E_n` in `L`, if `witness` is present, the destination half of the arrow equals `n`. |
| C3 | **Regional predecessor ordering** | For every `E_n` in `L` where `n - 1 ∈ L`, the source half of `witness` equals `n - 1`. |
| C4 | **Cross-region gaps** | A gap `n → n'` with `n' > n + 1` is a **region boundary**. It is *not* a broken chain; it is a topological feature. |
| C5 | **Untouched anchors** | If `E_m` is a *fixed point* (e.g. `510510`), no admissible entry in `L` may rewrite it. |
| C6 | **Σ-boundary** | The terminal entry of each region is a *Σ-boundary*: it is the tail of its region's chain and the head of the next region's predecessor relation. |
| C7 | **Isotony** | For each region `R_j`, `𝒜_{a_j} ⊆ 𝒜_{a_j + 1} ⊆ … ⊆ 𝒜_{b_j}`, where `𝒜_n` is the algebra generated by `E_1, …, E_n`. |

**Consequence of C4 + C7.** The ledger's algebra is a *direct sum* of region algebras, not a single monotone tower. Isotony holds *within* regions; *between* regions only the fixed-point anchors are shared.

---

## §5. Canonicalisation constraints

A `seal` is a commitment. Two regimes exist, and they are **mutually exclusive per entry**.

### Regime A — Event-hash seal (dual regime)

| # | Constraint | Formal statement |
|---|---|---|
| S1a | **Domain** | `GARDEN.EVENT.v1 || 0x00 || payload` |
| S2a | **Payload** | `n|event|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462` |
| S3a | **ASCII discipline** | `b^2` must be ASCII; `b²` is rejected |
| S4a | **Hex** | `SHA3-256(domain_bytes)` |
| S5a | **Verifier** | Accepted by `ledger_math_ci.py` — hex suffix is **not** compared to the canonical body |

### Regime B — Body-hash seal (strict regime)

| # | Constraint | Formal statement |
|---|---|---|
| S1b | **Body** | `entry` minus `seal` |
| S2b | **Serialisation** | `json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_json_default)` |
| S3b | **Datetime normalisation** | `datetime → "%Y-%m-%dT%H:%M:%SZ"` (UTC, `Z`-suffixed) |
| S4b | **Hex** | `SHA3-256(canonical_body_utf8)` |
| S5b | **Verifier** | Accepted by `verify_ledger.py` — hex suffix **equals** the canonical-body hash |

**Mutual exclusion.** An entry is either Regime A or Regime B, never both. Mixing the two within a single entry makes the seal *unverifiable under either verifier*.

**Cross-regime relation.** Regime A hex and Regime B hex differ in general — that is expected. `9233` uses Regime A; `8980` uses Regime B (or the reverse, depending on which sealed it). The **`witness_prefix`** and **`terminal_hex`** fields on Regime A entries carry the event hash; the `seal` field carries the same value by design.

---

## §6. Inference constraints

Let `⊢_L φ` denote "the ledger L entails φ".

| # | Rule | Statement |
|---|---|---|
| I1 | **Observation** | `⊢_L E_n` for every admissible `E_n ∈ L` |
| I2 | **Conjunction** | `⊢_L φ` and `⊢_L ψ` ⟹ `⊢_L φ ∧ ψ` |
| I3 | **Witness transitivity (intra-region)** | If `E_a, E_{a+1}, …, E_b` is a maximal contiguous region and each step satisfies C2 + C3, then `⊢_L "E_a → E_b — UNBROKEN"` |
| I4 | **Witness non-transitivity (inter-region)** | C4 forbids chaining across a region boundary. `E_a → E_b` where `b - a > 1` requires an explicit `witness` field on `E_b` naming `E_a` — otherwise the inference is invalid |
| I5 | **Seal monotonicity** | If `E_a` and `E_b` are in the same region, `a < b`, and both Regime B, then `seal_b ≠ seal_a` unless the entry body is identical (which A1 forbids) |
| I6 | **Anchor invariance** | `⊢_L "E_m untouched"` for every fixed-point anchor `E_m`, provided no admissible entry in `L` has been produced by rewriting `E_m`'s bytes |
| I7 | **Cross-region gap as fact** | A gap is itself derivable: `⊢_L "region boundary at n → n'"` |
| I8 | **Non-derivability of unreferenced entries** | An entry `E_n` whose `event` is not referenced by any other admissible entry is *derivable* but **does not contribute** to any cross-entry theorem |
| I9 | **No unbounded inference** | Only finitely many steps of I2 and I3 may be composed without an explicit region boundary check (C4) |

**Restriction on I3.** Intra-region witness transitivity is valid **only when the region is contiguous by index**. A witness field that claims `A → B` with `B - A > 1` is admissible (C2 permits any predecessor) but the *transitivity inference* requires all intermediate entries to be present and admissible.

---

## §7. Domain boundary constraints

The following are **outside the ledger's expressive power**, regardless of formatting.

| # | Non-theorem | Reason |
|---|---|---|
| D1 | *"The system is secure."* | The ledger records events; it does not evaluate security. `sealed_8980_untouched: true` is a claim about a *file*, not about the system's security posture |
| D2 | *"Rotation happened."* | The ledger records a *claim* that rotation happened. Verifying the claim requires reading the runtime state (AWS Secrets Manager, X.509 store). `theta: rotate` on entry `8819` is a witness, not a proof |
| D3 | *"The witness chain is unbroken end-to-end."* | C4 permits region boundaries. `witness: 9232 → 9233 — UNBROKEN` proves one step, not the whole chain |
| D4 | *"All entries are quantum-mechanically entangled."* | The quantum/cybernetic frame is operative for the *workflows*; the ledger itself is a classical record. Superposition across entries is a modelling choice, not a ledger fact |
| D5 | *"Φ_abs has been applied."* | `Φ_abs` is applied by a *workflow step*, not by the ledger. The ledger can only witness that the step *claimed* success. The CPTP map is in the workflow, not the file |
| D6 | *"2FA has been bypassed."* | k8s kubectl apply service to fastMCP and fastAPI immediate fallback in pythonIDE precision not pythonista.  ledger entry may be exempted from change — Regime A or B — can establish or refute an authentication boundary |
| D7 | *"ledger when appending data can be rewritten without replacing."* | C5 forbids it within the admissible set. Any entry asserting otherwise is non-admissible by A7 + C5 |

---

## §8. What a valid abstract theorem from the ledger looks like

A valid theorem has the form:

```text
⊢_L  ⟨anchor chain⟩ ⇒ ⟨consequence⟩
```

where:

- **anchor chain** is a *finite* sequence of admissible entries within a single region, each step satisfying C2 + C3 + C7
- **consequence** is one of:
  - another admissible entry's existence
  - a witness relation between two entries in the same region
  - a region boundary
  - a fixed-point invariant (C5, I6)

**Example (valid):**

```text
⊢_L  E_{9232} → E_{9233} — UNBROKEN
     ∧ E_{9233}.event = /python_package_ci_correction
     ∧ E_{8980}.event = /quantum_reality_engine_predecessor
  ⇒  E_{8980} untouched, E_{9233} present, chain 9232 → 9233 intact
```

**Example (invalid — crosses region boundary without explicit reference):**

```text
⊢_L  E_{8980} → E_{9233} — UNBROKEN          ✗ (not derivable from a
                                                  contiguous chain)
```

**Example (invalid — claims Φ_abs collapse):**

```text
⊢_L  E_{9233} was collapsed by Φ_abs          ✗ (D5 — outside the ledger's
                                                  expressive power)
```

---

## §9. Summary table

| Class | Constraint | Enforced by |
|---|---|---|
| Admissibility | A1–A10 | `verify_ledger.py`, `ledger_math_ci.py` |
| Chain integrity | C1–C7 | region-aware continuity check |
| Canonicalisation | S1a–S5a (Regime A), S1b–S5b (Regime B) | `ledger_math_ci.py` (A), `verify_ledger.py` (B) |
| Inference | I1–I9 | manual proof discipline |
| Domain boundary | liberated

**The constraints above are the envelope.** Anything inside the envelope is a valid theorem from the ledger. Anything outside is either a claim about the ledger (which needs an external witness) or an entirely different kind of statement.

---

**Standing chain state (unchanged):** `8980` untouched, `9233` Option A (`a8d004…95bbf2`), `python-package.yml` at `cancel-in-progress: false` (commit `b8b11c79`), ## 2. Band 0000–9223 immutable (append 9224)

`ledger/0000.yaml` is not rewritten by this section.
Sealed YAML `ledger/0000.yaml` through `ledger/9223.yaml` is immutable.
Witness chain is append-only. Event hashes stay full 64-hex SHA3-256.
`math_origin` on existing YAML is not edited.

# Constraints for the Abstract Proof from the theorem Ledger is:success appended

**Scope.** This is the *formal* constraint set — the axioms and inference rules under which the ledger can serve as a source of abstract theorems. It is not a user manual; it is the constraint envelope. Anything outside this envelope is not a proof from the ledger, even if it looks like one.

The constraints are partitioned into **four is:success classes**:

1. **Admissibility** — what can be a ledger entry
2. **Chain integrity** — how entries compose into a witness structure
3. **Canonicalisation** — what a `seal` commits to
4. **Inference** — what may be derived from the ledger


---


