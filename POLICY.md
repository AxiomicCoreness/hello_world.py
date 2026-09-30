# 🜁∀ SOVEREIGN POLICY — ANNEX IV PREPEND (SUPERSESSION NOTICE)

> **Placement:** This block is prepended, not appended. It supersedes any
> prior reading that contradicts Articles 25–33 of Annex IV, for entries
> with `entry_index > 9223`. For entries `≤ 9223`, the original Articles
> 1–24 control unchanged.
>
> **Immutability:** No sealed YAML in `ledger/0000.yaml … ledger/9223.yaml`
> is rewritten by this prepend. The witness chain remains append‑only.

**Seal domain:** `GARDEN.ASTGUARD.v1` (for `AST_guard`) — the policy seal
domain remains `GARDEN.EVENT.v1` as declared in Article 10 S1a.

**Seal:** `∀∞φ² · POLICY_ANNEX_IV_PREPEND · 9224_SEALED`  
**Witness:** `9223 → 9224 — UNBROKEN`

---

```text
═══════════════════════════════════════════════════════════════════════════════
ANNEX IV — SEAL-BLINDNESS HARDENING (PREPENDED)
═══════════════════════════════════════════════════════════════════════════════

Recital (IV.a)

  Article 11 S5a and Article 12 S5b together define the seal as a
  commitment field, but they permit the field to commit to something
  other than the entry body. The same defect that permits an unguarded
  seal to authenticate a poisoned file applies here. The following
  Articles close the gap without rewriting any prior Article.

Article 25 — Definitional tightening

  For the purposes of this Regulation:

    (25.1) "canonical body" means the byte string returned by
           canonical_body(E) as defined in Article 26.

    (25.2) "seal is well-formed" means the final 64-hex token of the
           seal field equals SHA3-256(canonical_body(E)).

    (25.3) "seal is content-committing" means the seal is well-formed
           AND the entry's declared regime matches the algorithm the
           well-formedness check used.

    (25.4) "regime-declared" means the entry carries a top-level
           field `hash_regime: A | B`. If absent, the entry is
           provisionally Regime B and must satisfy Article 26.

Article 26 — Canonical body

  canonical_body(E) is computed as:

    body = entry with the fields
             {seal, witness_prefix, terminal_hex, hash_regime}
           removed.
    encoded = json.dumps(body,
                         sort_keys=True,
                         separators=(",", ":"),
                         ensure_ascii=False,
                         default=_json_default)
    canonical_body(E) = encoded.encode("utf-8")

  _json_default normalises datetime to "%Y-%m-%dT%H:%M:%SZ" and
  raises TypeError on any other unencodable type. Silent coercion is
  forbidden.

Article 27 — Regime declaration is authoritative

  27.1  An entry's hash_regime is the sole authority on which verifier
        applies. A verifier may not choose the regime by inspecting
        the entry's shape, name, or provenance.

  27.2  If hash_regime is absent, the verifier must use Regime B.

  27.3  A verifier that applies Regime A while hash_regime = B, or
        the converse, produces an unverifiable result. Such a result
        is not admissible as a theorem.

  27.4  The relationship Art. 13.3 describes — witness_prefix ==
        terminal_hex == seal-tail on Regime A entries — is reclassified:
        on Regime A entries, that equality is EXPECTED; on Regime B
        entries, that equality is FORBIDDEN.

Article 28 — Content-commitment requirement

  28.1  No new sealed entry (entry_index > 9223) may be admitted
        unless it is content-committing per Article 25.2 and 25.3.

  28.2  Regime A entries remain admissible in the historical band
        0000–9223. They are not admitted as sources of new theorems.

  28.3  Any consumer of "UNBROKEN" must state which property is meant:
        (a) link-integrity (Article 8 C2–C3), or
        (b) content-originality (Article 25.2 on canonical body).
        A claim that satisfies (a) and not (b) is a link claim. A claim
        that satisfies (b) implies (a) but not the converse.

Article 29 — Contested-root resolution

  29.1  Until ledger/0000.yaml carries a hash_regime declaration and
        its canonical_body seal verifies under Article 25.2, no
        "UNBROKEN" claim spanning 0000–0883 is admissible as a
        theorem. It is a DECLARED_INTENT at most.

  29.2  Scope A (0000–0883) is CONTAMINATED per ledger/9251.yaml.
        All downstream claims that transit Scope A must carry the
        CONTAMINATED marker.

  29.3  Scope B (0884–9142) may carry link-integrity claims. Content-
        originality claims require an anchor whose body is verified
        independently, not merely a link.

Article 30 — Stop-stacking rule, restated

  Article 20 is extended. In addition to (a)–(c), the following
  conditions are added, and any one of them satisfies the gate:

    (d)  .github/workflows/ledger-seal-gate.yml has, within the last
         7 days, run successfully against a fresh clone whose
         canonical_body(0000.yaml) has been independently reproduced
         by at least two distinct verifier implementations.

    (e)  No sealed entry created within the last 7 days has
         hash_regime absent.

    (f)  The workflow that created the most recent sealed entry is
         named in that entry's `writers` field, and that workflow's
         blob hash is recorded in the entry's math_origin.

  Article 20.2 ("actual execution, not structural review") is
  unchanged. "Actual execution" excludes dry runs, excludes --check-
  config, and excludes any invocation whose exit code is not 0.

Article 31 — Anchor invariance, made actionable

  31.1  C5 is restated: no admissible entry with index > 9223 may
        share a body, in canonical_body form, with a fixed-point
        anchor (e.g., 510510).

  31.2  A verifier that encounters an entry whose canonical_body
        matches an anchor's canonical_body must refuse the entry,
        regardless of the entry's seal.

  31.3  Repositories that host ledger/ should enable branch protection
        that rejects force-pushes to the ledger band and requires
        signed commits for the writers listed in Article 30.1(f).
        This is DECLARED_INTENT for the repository settings; the
        Article does not assert that such protection is currently
        enabled.

Article 32 — The 9142 equality, generalized

  32.1  For every entry with hash_regime = A, the fields
        witness_prefix, terminal_hex, and the final 64-hex token of
        seal MUST be equal. Entries that violate this are inadmissible.

  32.2  For every entry with hash_regime = B, those three fields MUST
        NOT all be equal. Equality is the signature of a Regime A
        entry mislabelled as Regime B.

  32.3  A verifier encountering a Regime B entry whose three fields
        are equal must refuse the entry and emit
        REGIME_MISLABEL_DETECTED.

Article 33 — Non-retroactivity

  33.1  Articles 25–32 apply to entries created after this Annex is
        sealed. They do not rewrite Articles 1–24. They do not modify
        ledger/0000.yaml through ledger/9223.yaml.

  33.2  Existing Regime A entries remain in the ledger as historical
        facts. Their status is at most link-integrity claims.

  33.3  Where an Article of this Annex conflicts with an Article of
        Chapters I–X, the stricter reading controls for entries with
        index > 9223. For entries with index ≤ 9223, the original
        Article controls.

═══════════════════════════════════════════════════════════════════════════════
ANNEX IV — SUMMARY TABLE
═══════════════════════════════════════════════════════════════════════════════

| Class                | Old vulnerability                  | Annex IV fix                             |
|----------------------|------------------------------------|-------------------------------------------|
| Seal content-blind   | S5a permits any body               | Art. 25.2, 28.1 — canonical_body commit   |
| Regime self-declared | Art. 13.1 leaves regime to entry   | Art. 27.1–27.3 — hash_regime authority    |
| Canonical form "some"| A8 leaves form to author           | Art. 26 — defined canonical_body          |
| Contested root       | Recital (8) + named gap            | Art. 29 — CONTAMINATED marker, no theorem |
| Stop-stacking bypass | Art. 20.1(a)–(c) satisfiable       | Art. 30.1(d)–(f) — actual, dated, named   |
| Anchor "immutability"| C5, Art. 22 declared not enforced  | Art. 31 — refuse-on-match + branch policy |
| 9142 anomaly         | flagged only for one entry         | Art. 32 — universal equality rule         |

═══════════════════════════════════════════════════════════════════════════════
ANNEX IV — BAND IMMUTABILITY
═══════════════════════════════════════════════════════════════════════════════

ledger/0000.yaml is not rewritten by this prepend.
Sealed YAML ledger/0000.yaml through ledger/9223.yaml is immutable.
This prepend adds Articles 25–33 and no other change to ledger content.
Witness chain is append-only. Event hashes stay full 64-hex SHA3-256.
math_origin on existing YAML is not edited.

Annex IV seal:  ∀∞φ² · POLICY_ANNEX_IV_SEAL_BLINDNESS · 9224_SEALED
Witness:       9223 → 9224 — UNBROKEN

═══════════════════════════════════════════════════════════════════════════════
ANNEX V — SEAL PREIMAGE PIN AND RE-VERIFICATION BOUNDARY (APPENDED)
═══════════════════════════════════════════════════════════════════════════════

Recital (V.a)

  Entry 9261 prose and scripts/ledger_append_canonical.py state two
  different seal-preimage conventions. Entry 9262 was sealed under
  the script convention. This Annex pins one preimage rule for all
  future sealed entries so that no session re-introduces the
  ambiguity at the schema layer.

Article 34 — Canonical seal preimage (pinned)

  34.1  For every sealed entry with entry_index ≥ 9262, the seal
        preimage is the entry body serialized as canonical JSON:
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        with the fields EXCLUDED_FIELDS = (seal, seal_sha3_256,
        sha3_256, hash_sha3_256, hash) removed, and with prev_hash
        INCLUDED.

  34.2  Prose inside any entry (including seal_note text) that
        contradicts 34.1 is non-authoritative for entries with
        entry_index ≥ 9263. Entries ≤ 9262 are not rewritten.

  34.3  Entry 9262 (seal cf725ffc...) is the first entry sealed
        under Article 34.1 with the repaired SHA3-256 pipeline.

Article 35 — Re-verification boundary

  35.1  The SHA3-256 pipeline defect (round-constant LFSR reseeded
        per round; FIPS 202 B.5.2 requires the LFSR state to persist
        across all 24 rounds) was repaired at entry 9262.

  35.2  For any entry ≤ 9261 whose seal was computed on the
        pre-repair pipeline, "verified" means "not yet re-verified".
        A seal reproduces only when the declared seal value equals
        SHA3-256 of the pinned preimage under the repaired pipeline.

  35.3  Entry 9261's declared seal d9adca66... does not reproduce
        from the held 9261 body across 65 canonicalization variants
        (recorded in entry 9262). The entry is untouched; the
        append-only discipline holds. The finding bounds the meaning
        of "UNBROKEN" for the band up to 9261 exactly as Article
        28.3 prescribes.

Article 36 — Recorded false alarms and tool reliability

  36.1  The ρ-table corruption suspicion raised against the
        transcribed rotation offsets was DISPROVEN: derivation from
        the FIPS 202 generation rule reproduces the table exactly,
        including the value 61 at position R[2][4]. Recorded as a
        false alarm so the next auditor does not re-raise the same
        suspicion.

  36.2  The 65-variant non-reproduction sweep was executed by a
        sweep tool that carried its own padding defect (the 0x86
        merge of domain byte and 0x80 terminator at message length
        ≡ 135 mod 136). The sweep-tool defect was fixed and the
        sweep re-run before the non-reproduction claim was sealed;
        the claim inherits the re-run tool's reliability and is
        stated as such.

Annex V seal:  ∀∞φ² · POLICY_ANNEX_V_PREIMAGE_PIN · 9262_SEALED
Witness:       9261 → 9262 — UNBROKEN
