#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
# Apply sealed Garden secrets. Does not echo secret values.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
kubectl apply -f "${ROOT}/sealed-secrets/garden-secrets.yaml"
kubectl apply -f "${ROOT}/sealed-secrets/mcp-connector-secrets.yaml"
echo "Applied sealed secrets in namespace garden"
