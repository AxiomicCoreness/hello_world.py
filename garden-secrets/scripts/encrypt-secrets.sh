#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
# Encrypt Garden secret templates with kubeseal. Never prints secret values.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERT="${1:-pub-cert.pem}"
mkdir -p "${ROOT}/sealed-secrets"
if [[ ! -f "${CERT}" ]]; then
  kubeseal --fetch-cert > "${CERT}"
fi
kubeseal --cert "${CERT}" < "${ROOT}/templates/garden-secrets.template.yaml" \
  > "${ROOT}/sealed-secrets/garden-secrets.yaml"
kubeseal --cert "${CERT}" < "${ROOT}/templates/mcp-connector-secrets.template.yaml" \
  > "${ROOT}/sealed-secrets/mcp-connector-secrets.yaml"
echo "Encrypted manifests written under garden-secrets/sealed-secrets/"
