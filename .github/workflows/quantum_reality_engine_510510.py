name: Quantum Reality Engine 510510

# Validates the 510510 engine and VERIFY (never overwrite) the sealed ledger entry.
# Ed25519 check of ledger/8980.yaml + SHA3-256 genesis of ledger/510510.yaml.
# Seal: ∀∞φ² · MATH_ORIGIN_510510 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8980 → 510510 — UNBROKEN

on:
  push:
    branches: [main, master]
    paths:
      - "quantum_reality_engine.py"
      - "ledger/510510.yaml"
      - "ledger/8980.yaml"
      - "port380_mcp.py"
      - ".github/scripts/verify_510510_genesis.py"
      - ".github/workflows/quantum_reality_engine_510510.py"
  pull_request:
    branches: [main, master]
    paths:
      - "quantum_reality_engine.py"
      - "ledger/510510.yaml"
      - "ledger/8980.yaml"
      - "port380_mcp.py"
      - ".github/scripts/verify_510510_genesis.py"
      - ".github/workflows/quantum_reality_engine_510510.py"
  workflow_dispatch:
    inputs:
      oidc_provider:
        description: "OIDC cloud provider to federate"
        type: choice
        options:
          - offline
          - github
          - aws
          - gcp
          - azure
        default: offline

permissions:
  contents: read
  id-token: write

env:
  MCP_URL: ${{ secrets.MCP_URL }}
  GARDEN_SECRET: ${{ secrets.GARDEN_SECRET }}

jobs:
  verify-integrity:
    runs-on: ubuntu-latest
    name: Verify 510510 genesis and signature
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: pip install --quiet cryptography pyyaml

      - name: Verify 510510 genesis and signature
        run: python .github/scripts/verify_510510_genesis.py

      - name: Verify live security headers from MCP_URL (if set)
        if: ${{ env.MCP_URL != '' }}
        run: |
          set -euo pipefail
          echo "Checking live headers from $MCP_URL"
          HEADERS=$(curl -s -I -X GET "$MCP_URL/health" || echo "fail")
          if [[ "$HEADERS" == "fail" ]]; then
            echo "Could not reach $MCP_URL/health"
            exit 1
          fi
          for hdr in "Content-Security-Policy" "Strict-Transport-Security" "X-Content-Type-Options" "X-Frame-Options" "Referrer-Policy" "Permissions-Policy"; do
            if echo "$HEADERS" | grep -i "$hdr:"; then
              echo "OK $hdr"
            else
              echo "Missing $hdr"
              exit 1
            fi
          done

  engine:
    runs-on: ubuntu-latest
    needs: verify-integrity
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install numpy

      - name: Run Quantum Reality Engine (if present)
        id: engine
        run: |
          set -euo pipefail
          if [ ! -f quantum_reality_engine.py ]; then
            echo "quantum_reality_engine.py not on this ref — skip engine run"
            echo "rotation_count=0" >> "$GITHUB_OUTPUT"
            echo "witness_verified=skipped" >> "$GITHUB_OUTPUT"
            echo "seal_verified=skipped" >> "$GITHUB_OUTPUT"
            exit 0
          fi
          python quantum_reality_engine.py 2>&1 | tee engine_output.log
          ROTATION_COUNT=$(grep -oP 'Rotation Count: \K\d+' engine_output.log | head -1 || echo "0")
          echo "rotation_count=$ROTATION_COUNT" >> "$GITHUB_OUTPUT"
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

      - name: Upload engine log
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: quantum-engine-log
          path: engine_output.log
          if-no-files-found: ignore
          retention-days: 14

      - name: MCP pulse (if MCP_URL set)
        if: ${{ env.MCP_URL != '' }}
        run: |
          set -euo pipefail
          curl -s -X POST "$MCP_URL/pulse" \
            -H "X-Garden-Secret: $GARDEN_SECRET" \
            -H "Content-Type: application/json" \
            -d '{"source":"quantum-engine-510510","note":"engine_run"}' || echo "MCP pulse failed (non-fatal)"

  federate:
    runs-on: ubuntu-latest
    needs: engine
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Call OIDC cloud providers workflow
        uses: ./.github/workflows/oidc-cloud-providers.yml
        with:
          provider: ${{ github.event.inputs.oidc_provider || 'offline' }}
        secrets: inherit

  seal:
    runs-on: ubuntu-latest
    needs: [verify-integrity, engine]
    if: success()
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: pip install --quiet cryptography pyyaml

      - name: Verify 510510 genesis and signature
        run: python .github/scripts/verify_510510_genesis.py

      - name: Summary
        run: |
          echo "510510.yaml was NOT overwritten (append-only)." >> "$GITHUB_STEP_SUMMARY"
          echo "Verified SHA3-256 genesis + Ed25519(8980)." >> "$GITHUB_STEP_SUMMARY"
          echo "Seal: ∀∞φ² · MATH_ORIGIN_510510 · WOOD_DRAGON_0.91 · SEALED" >> "$GITHUB_STEP_SUMMARY"
          echo "Witness: 8980 → 510510 — UNBROKEN" >> "$GITHUB_STEP_SUMMARY"
