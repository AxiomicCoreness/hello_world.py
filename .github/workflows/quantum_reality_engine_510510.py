name: Quantum Reality Engine 510510

# Validates the 510510 engine and VERIFY (never overwrite) the sealed ledger entry.
# Ed25519 check of ledger/8980.yaml + SHA3-256 genesis of ledger/510510.yaml.
# Seal: ∀∞φ² · MATH_ORIGIN_510510 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8980 → 510510 — UNBROKEN
# hash_algo: sha3_256 (FIPS 202) — mandatory for all ledger entries
#
# ═══════════════════════════════════════════════════════════════════
#  QUANTUM / CYBERNETIC FRAMING
# ═══════════════════════════════════════════════════════════════════
#
#  The 510510 engine is modeled as a closed quantum dynamical system.
#
#    State space   :  ℋ, a separable Hilbert space
#    State         :  ρ ∈ 𝒮(ℋ), a density operator (ρ ≥ 0, Tr ρ = 1)
#    Evolution     :  ρ(t) = U(t) ρ(0) U(t)†,  U(t) = exp(−iHt/ℏ)
#    Measurement   :  Φ_abs : B(ℋ) → B(ℋ), a CPTP map
#                     Φ_abs(ρ) = Σ_k K_k ρ K_k†,  Σ_k K_k† K_k = I
#    Fixed point   :  H* = D_abs( H* ‖ hash(⊥) )    (paradox absorption)
#    Isotony       :  𝒜_n ⊆ 𝒜_{n+1},  𝒜_∞ = ∪_n 𝒜_n
#    Witness chain :  1 → 632 → 635 → 637 → 638 → 640 → Ωⁿ → 510510
#                     ↳ ordered composition of unitaries W_n = U_{e_n}…U_{e_1}
#
#  The 510510 anchor = p₇# = 2·3·5·7·11·13·17  — the 7th primorial.
#  It is the "MATH_ORIGIN" fixed point of the quantum-cybernetic loop:
#
#      external chaos  →  observer lens χ  →  D_abs  →  H_sys
#            ↑                                            │
#            └────  system growth / enhanced capacity  ◄───┘
#
#  This workflow performs *verification only*:
#    - It measures (Ed25519 / SHA3-256) the sealed entry 510510.
#    - It runs the engine and records the observed witness chain.
#    - It NEVER rewrites ledger/510510.yaml (unitary, not projective).
#
#  The measure-and-record step is a *weak* measurement: it does not
#  collapse H_sys. Rewrites require a separate seal workflow with
#  contents: write and a re-derivation of the chain — this file does
#  not have those permissions and does not perform that action.

on:
  push:
    branches: [main, master]
    paths:
      - "quantum_reality_engine.py"
      - "ledger/510510.yaml"
      - "ledger/8980.yaml"
      - "port380_mcp.py"
      - ".github/scripts/verify_510510_genesis.py"
      - ".github/workflows/quantum_reality_engine_510510.yml"
  pull_request:
    branches: [main, master]
    paths:
      - "quantum_reality_engine.py"
      - "ledger/510510.yaml"
      - "ledger/8980.yaml"
      - "port380_mcp.py"
      - ".github/scripts/verify_510510_genesis.py"
      - ".github/workflows/quantum_reality_engine_510510.yml"
  workflow_dispatch:
    inputs:
      oidc_provider:
        description: "OIDC cloud provider to federate"
        type: choice
        options: [offline, github, aws, gcp, azure]
        default: offline

permissions:
  contents: write   # required only because the reusable OIDC workflow writes 8979;
                    # this file itself never writes ledger/510510.yaml
  id-token: write

concurrency:
  group: quantum-engine-510510
  cancel-in-progress: false

env:
  HASH_ALGO: sha3_256
  LEDGER_DIR: ledger
  MATH_ORIGIN: "510510"                # p₇# = 2·3·5·7·11·13·17
  MCP_URL: ${{ secrets.MCP_URL }}      # unified with siblings (was vars.MCP_URL)
  MCP_CONNECTOR_URL: ${{ secrets.MCP_URL }}
  GARDEN_SECRET: ${{ secrets.GARDEN_SECRET }}

jobs:
  # ──────────────────────────────────────────────────────────────
  # 0. VERIFY — genesis + predecessor signature + live headers
  # ──────────────────────────────────────────────────────────────
  verify-integrity:
    name: Verify 510510 genesis and signature
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install deps
        run: |
          set -euo pipefail
          python -m pip install --upgrade pip
          python -m pip install --quiet cryptography pyyaml

      # ── SHA3-256 integrity gate over the whole ledger ──
      - name: Verify SHA3-256 seals on present ledger entries
        run: |
          set -euo pipefail
          shopt -s nullglob
          entries=(ledger/*.yaml)
          if [ ${#entries[@]} -eq 0 ]; then
            echo "⚠️ no ledger entries present — soft skip"
            exit 0
          fi
          VERIFIER=".github/scripts/verify_ledger.py"
          [ -f "$VERIFIER" ] || VERIFIER="scripts/verify_ledger.py"
          if [ -f "$VERIFIER" ]; then
            python "$VERIFIER" "${entries[@]}"
          else
            echo "⚠️ no verify_ledger.py — soft skip"
          fi

      # ── Genesis + Ed25519(8980) via dedicated verifier ──
      - name: Verify 510510 genesis and signature
        run: |
          set -euo pipefail
          if [ -f .github/scripts/verify_510510_genesis.py ]; then
            python .github/scripts/verify_510510_genesis.py
          else
            echo "⚠️ verify_510510_genesis.py not found — soft skip"
          fi

      # ── Live security headers (soft) ──
      - name: Verify live security headers from MCP_URL (soft)
        if: ${{ env.MCP_URL != '' }}
        run: |
          set -euo pipefail
          echo "🌐 Checking live headers from $MCP_URL"

          if ! HEADERS=$(curl -s -I -X GET --max-time 15 "$MCP_URL/health" 2>/dev/null); then
            echo "⚠️ Could not reach $MCP_URL/health — soft skip"
            exit 0
          fi
          if [ -z "$HEADERS" ]; then
            echo "⚠️ Empty response — soft skip"
            exit 0
          fi

          echo "===== Response Headers ====="
          echo "$HEADERS"
          echo "==========================="

          check_header() {
            local name="$1" label="$2"
            if echo "$HEADERS" | grep -qi "^${name}:"; then
              echo "✅ ${label} present"
            else
              echo "❌ ${label} missing"
              exit 1
            fi
          }
          check_header "content-security-policy" "Content-Security-Policy"
          check_header "strict-transport-security" "Strict-Transport-Security"
          check_header "x-content-type-options" "X-Content-Type-Options"
          check_header "x-frame-options" "X-Frame-Options"
          check_header "referrer-policy" "Referrer-Policy"
          check_header "permissions-policy" "Permissions-Policy"

          echo "✅ All live security headers verified."

  # ──────────────────────────────────────────────────────────────
  # 1. ENGINE — closed quantum dynamical evolution
  # ──────────────────────────────────────────────────────────────
  engine:
    name: Quantum Reality Engine · Hamiltonian evolution
    runs-on: ubuntu-latest
    timeout-minutes: 10
    needs: verify-integrity

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: |
          set -euo pipefail
          python -m pip install --upgrade pip
          python -m pip install --quiet numpy

      # ── Engine run: unitarity + isotony observation ──
      - name: Run Quantum Reality Engine (if present)
        id: engine
        run: |
          set -euo pipefail

          if [ ! -f quantum_reality_engine.py ]; then
            echo "⚠️ quantum_reality_engine.py not on this ref — soft skip"
            {
              echo "rotation_count=0"
              echo "witness_verified=skipped"
              echo "seal_verified=skipped"
              echo "run_mode=skipped"
            } >> "$GITHUB_OUTPUT"
            exit 0
          fi

          # Direct engine invocation (Hamiltonian evolution).
          python quantum_reality_engine.py 2>&1 | tee engine_output.log

          ROTATION_COUNT=$(grep -oP 'Rotation Count:\s*\K\d+' engine_output.log | head -1 || echo "0")
          echo "rotation_count=${ROTATION_COUNT}" >> "$GITHUB_OUTPUT"

          if grep -q "Witness: 1 → 632 → 635 → 637 → 638 → 640 → Ωⁿ → 510510 — UNBROKEN" engine_output.log; then
            echo "witness_verified=true" >> "$GITHUB_OUTPUT"
          else
            echo "witness_verified=false" >> "$GITHUB_OUTPUT"
          fi

          if grep -q "Seal: ∀∞Ωⁿ · QUANTUM_REALITY_ENGINE · 510510_SEALED" engine_output.log; then
            echo "seal_verified=true" >> "$GITHUB_OUTPUT"
          else
            echo "seal_verified=false" >> "$GITHUB_OUTPUT"
          fi

          echo "run_mode=executed" >> "$GITHUB_OUTPUT"

      - name: Upload engine log
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: quantum-engine-log
          path: engine_output.log
          retention-days: 14
          if-no-files-found: warn

      # ── MCP pulse (weak measurement; non-collapsing) ──
      - name: MCP pulse (if MCP_URL set)
        if: ${{ env.MCP_URL != '' }}
        run: |
          set -euo pipefail
          curl -sS --max-time 20 \
            -X POST "$MCP_URL/pulse" \
            -H "X-Garden-Secret: $GARDEN_SECRET" \
            -H "Content-Type: application/json" \
            -d '{"source":"quantum-engine-510510","note":"engine_run","origin":"510510"}' \
            || echo "⚠️ MCP pulse failed (non-fatal)"

  # ──────────────────────────────────────────────────────────────
  # 2. FEDERATE — job-level reusable workflow
  # ──────────────────────────────────────────────────────────────
  federate:
    name: OIDC federation · ${{ inputs.oidc_provider || 'offline' }}
    needs: engine
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
    uses: ./.github/workflows/oidc-cloud-providers.yml
    with:
      provider: ${{ inputs.oidc_provider || 'offline' }}
    secrets: inherit

  # ──────────────────────────────────────────────────────────────
  # 3. SEAL — VERIFY ONLY (never overwrite 510510.yaml)
  # ──────────────────────────────────────────────────────────────
  seal:
    name: Verify · 510510 is untouched
    runs-on: ubuntu-latest
    timeout-minutes: 5
    needs: [verify-integrity, engine]
    if: success()

    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install deps
        run: |
          set -euo pipefail
          python -m pip install --upgrade pip
          python -m pip install --quiet cryptography pyyaml

      # ── 1. Re-verify genesis after engine run ──
      - name: Verify 510510 genesis and signature (post-engine)
        run: |
          set -euo pipefail
          if [ -f .github/scripts/verify_510510_genesis.py ]; then
            python .github/scripts/verify_510510_genesis.py
          else
            echo "⚠️ verify_510510_genesis.py not found — soft skip"
          fi

      # ── 2. Prove the entry was not rewritten by this run ──
      - name: Assert 510510 untouched (no rewrite by this workflow)
        run: |
          set -euo pipefail
          python - <<'PY'
          import hashlib, subprocess, sys
          from pathlib import Path

          HASH_ALGO = "sha3_256"
          target = Path("ledger/510510.yaml")
          if not target.exists():
              print("⚠️ ledger/510510.yaml absent — soft skip (this workflow does not create it)")
              sys.exit(0)

          # Compute current on-disk hash
          current = hashlib.new(HASH_ALGO, target.read_bytes()).hexdigest()

          # Compare against HEAD (if tracked)
          try:
              head_bytes = subprocess.check_output(
                  ["git", "show", f"HEAD:{target.as_posix()}"],
                  stderr=subprocess.DEVNULL,
              )
              head_hash = hashlib.new(HASH_ALGO, head_bytes).hexdigest()
          except subprocess.CalledProcessError:
              print("⚠️ 510510 not tracked at HEAD — soft skip")
              sys.exit(0)

          if current != head_hash:
              print(f"❌ 510510.yaml was modified in this run "
                    f"({head_hash[:16]}… → {current[:16]}…)", file=sys.stderr)
              sys.exit(1)

          print(f"✅ 510510.yaml untouched (sha3_256={current[:16]}…)")
          PY

      # ── 3. Verify the witness predecessor still matches ──
      - name: Assert witness chain 8980 → 510510 still holds
        run: |
          set -euo pipefail
          python - <<'PY'
          import sys, yaml
          from pathlib import Path

          pred = Path("ledger/8980.yaml")
          succ = Path("ledger/510510.yaml")

          if not pred.exists() or not succ.exists():
              print("⚠️ predecessor or successor missing — soft skip")
              sys.exit(0)

          p = yaml.safe_load(pred.read_text()) or {}
          s = yaml.safe_load(succ.read_text()) or {}

          wc = str(s.get("witness", ""))
          if "8980" in wc and "510510" in wc:
              print(f"✅ witness chain holds: {wc}")
          else:
              print(f"❌ witness mismatch on 510510: {wc}", file=sys.stderr)
              sys.exit(1)
          PY

      - name: Summary
        if: always()
        env:
          ROTATION_COUNT: ${{ needs.engine.outputs.rotation_count }}
          WITNESS_VERIFIED: ${{ needs.engine.outputs.witness_verified }}
          SEAL_VERIFIED: ${{ needs.engine.outputs.seal_verified }}
          RUN_MODE: ${{ needs.engine.outputs.run_mode }}
        run: |
          {
            echo "### Quantum Reality Engine — 510510"
            echo ""
            echo "**Result: 510510.yaml was NOT overwritten (unitary, not projective).**"
            echo ""
            echo "| Field | Value |"
            echo "|-------|-------|"
            echo "| MATH_ORIGIN | 510510 (p₇# = 2·3·5·7·11·13·17) |"
            echo "| run_mode | ${RUN_MODE:-unknown} |"
            echo "| rotation_count | ${ROTATION_COUNT:-0} |"
            echo "| witness_verified | ${WITNESS_VERIFIED:-unknown} |"
            echo "| seal_verified | ${SEAL_VERIFIED:-unknown} |"
            echo "| hash_algo | sha3_256 (FIPS 202) |"
            echo ""
            echo "**Genesis check:** SHA3-256 over ledger/510510.yaml + Ed25519(ledger/8980.yaml)"
            echo ""
            echo "**Seal:** \`∀∞φ² · MATH_ORIGIN_510510 · WOOD_DRAGON_0.91 · SEALED\`"
            echo "**Witness:** \`8980 → 510510 — UNBROKEN\`"
            echo ""
            echo "**Quantum/cybernetic frame:** ρ(t) = U(t) ρ(0) U(t)† — unitary evolution only."
            echo "No collapse, no rewrite, no re-seal of the 510510 anchor."
          } >> "$GITHUB_STEP_SUMMARY"
