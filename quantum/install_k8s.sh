#!/bin/bash
# quantum/install_k8s.sh
# Layer 314 + unified Ingress api.sovereign.garden/380
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAMESPACE="${NAMESPACE:-garden}"

echo "🜁∀ DEPLOYING PORT 380 SCALING GATE TO KUBERNETES (LAYER 314)..."
echo "   ROOT=$ROOT  NAMESPACE=$NAMESPACE"

kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

echo "Applying deployment-port-380.yaml..."
kubectl apply -n "${NAMESPACE}" -f "${ROOT}/k8s/deployment-port-380.yaml"

echo "Applying service-port-380.yaml..."
kubectl apply -n "${NAMESPACE}" -f "${ROOT}/k8s/service-port-380.yaml"

echo "Applying unified ingress.yaml (api.sovereign.garden/380)..."
kubectl apply -n "${NAMESPACE}" -f "${ROOT}/k8s/ingress.yaml"

echo "✅ PORT 380 GATE (LAYER 314) DEPLOYMENT COMPLETE."
echo "🌐 Service: port-380-gate.${NAMESPACE}.svc.cluster.local:380"
echo "🌐 Ingress: https://api.sovereign.garden/380"
