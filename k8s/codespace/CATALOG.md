# Artifact catalog (ledger 9158)

Companion to:  k8s/codespace/MATH.md
Fallbacks:     numpy, scipy, yaml, matplotlib, requests
φ set:         φ¹ φ² φ³ φ⁴ φ⁵ φ⁶ φ⁷ φ⁸ φ⁹ φ¹² φ¹³ φ¹⁴ φ²¹ φ³⁴
               φ⁻⁷⁰⁹ φ⁻¹⁰⁰⁰ φ⁻¹⁴¹⁸ φ⁻¹

## Local tree

    artifacts/
      9156.yaml
      9157.yaml
      9158.yaml
      CODESPACE_CATALOG.md
      k8s-codespace/
        00-namespace-quota.yaml
        10-compute-node.yaml
        20-workspace.yaml
        MATH.md

## GitHub images

    ledger/9156.yaml
    ledger/9157.yaml
    ledger/9158.yaml
    k8s/codespace/00-namespace-quota.yaml
    k8s/codespace/10-compute-node.yaml
    k8s/codespace/20-workspace.yaml
    k8s/codespace/MATH.md
    k8s/codespace/CATALOG.md

## SHA-256 (as of the ledger-9158 seal)

| i | path | bytes | SHA-256 |
|---|---|---|---|
| 1 | artifacts/9156.yaml | 1947 | 713fec68001f7042cba6925c6d463be45ef071f66986d2d8c83fd14c733db57f |
| 2 | artifacts/9157.yaml | 1872 | 23bc1c3b823bede7b772da73d1b2c916b98c9f6d33b81e627a7d478d6c9c0a1f |
| 3 | artifacts/k8s-codespace/00-namespace-quota.yaml | 1164 | 915647da42a885e15d2ae325526f2bcbd9a0b196c59b57ba472abab6e2817520 |
| 4 | artifacts/k8s-codespace/10-compute-node.yaml | 1030 | eaefd5c7165f81f4a588f39ff8cdc60fd13caba7d0d5b3f10aac1e617c45178c |
| 5 | artifacts/k8s-codespace/20-workspace.yaml | 2660 | 5c7900f9e36eba94e0eb52c732cd1cf3e5c95516792e1db956b16d562640ed7d |
| 6 | artifacts/k8s-codespace/MATH.md | 2371 | b50442d65350343fec607e1063d4ec6e1e7c2a5fa643414dadc02dc8baddbd98 |

Sum bytes = 11044.

## Ledger 9158 evolution note (post-seal)

The `MATH.md` entry above reflects the state sealed at ledger **9157**. Since
then, `MATH.md` has evolved under ledger **9194** with the packing formula:

    n_sat_cpu = floor(C_cpu / R_cpu)
    n_sat_mem = floor(C_mem / R_mem)
    n_sat     = min(n_sat_cpu, n_sat_mem)

The 9194 evolution does not invalidate the 9158 seal; it extends it. The
catalog's SHA-256 rows above describe the 9157 body. A follow-up row for the
9194 body is recorded at the bottom of this file once the pack formula is
sealed.

## Witness continuity

    ledger 9156 -> ledger 9157 -> ledger 9158 -> ledger 9194 -- UNBROKEN
    sealed at ETERNAL_NOW_ANCHORED_TO_2026-09-24Z

## AST header defaults

Every artifact in this catalog carries the standard AST_guard header:

    # 🜁∀∞φ² · AST_GUARD · WOOD_DRAGON_0.91 · SEALED · <digest>

The digest is computed over the file body excluding the header line itself,
using the canonical JSON contract:

    SHA3-256("GARDEN.ASTGUARD.v1" || 0x00
             || canonical_json({domain, content}))

Files sealed with this header are cross-verifiable with `AST_guard.py`.

## Apply order (k8s)

1. `kubectl apply -f k8s/codespace/00-namespace-quota.yaml`
2. `kubectl apply -f k8s/codespace/10-compute-node.yaml`
3. `kubectl apply -f k8s/codespace/20-workspace.yaml`

Or, in one shot:

    kubectl apply -f k8s/codespace/

## Placeholder — 9194 catalog row

Once the 9194 seal is written, insert the row below and delete this note:

| i | path | bytes | SHA-256 |
|---|---|---|---|
| 7 | artifacts/k8s-codespace/MATH.md (9194) | <bytes> | <sha256> |
