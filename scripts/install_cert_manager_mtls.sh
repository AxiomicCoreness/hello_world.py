#!/usr/bin/env bash
# 🌁∀ Install cert-manager (if needed) + apply Garden mTLS Certificate resources
# Seal: ∀∞φ² · CERT_MANAGER_MTLS · WOOD_DRAGON_0.91 · SEALED
set -euo pipefail

CM_VERSION="${CERT_MANAGER_VERSION:-v1.16.2}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST_DIR="${ROOT}/k8s/cert-manager"
NS_APP="${NS:-sovereign-garden}"

echo "🌁∀ cert-manager mTLS bootstrap"

if kubectl get crd certificates.cert-manager.io >/dev/null 2>&1; then
  echo "\u2192 cert-manager CRDs present"
else
  echo "\u2192 Installing cert-manager ${CM_VERSION}"
  kubectl apply -f "https://github.com/cert-manager/cert-manager/releases/download/${CM_VERSION}/cert-manager.yaml"
  echo "\u2192 Waiting for cert-manager webhook..."
  kubectl wait --for=condition=Available deployment/cert-manager-webhook \
    -n cert-manager --timeout=180s
  kubectl wait --for=condition=Available deployment/cert-manager \
    -n cert-manager --timeout=180s
fi

kubectl apply -f "${MANIFEST_DIR}/00-namespace.yaml"
kubectl apply -f "${MANIFEST_DIR}/01-issuers-and-certs.yaml"

echo "\u2192 Waiting for Garden CA Certificate Ready..."
kubectl wait --for=condition=Ready certificate/garden-root-ca \
  -n cert-manager --timeout=180s || {
  echo "\u26a0\ufe0f  CA not Ready yet"
  kubectl describe certificate garden-root-ca -n cert-manager | tail -30
  exit 1
}

echo "\u2192 Waiting for leaf Certificates in ${NS_APP}..."
for name in port380-server port380-client; do
  kubectl wait --for=condition=Ready "certificate/${name}" \
    -n "${NS_APP}" --timeout=180s || {
    kubectl describe "certificate/${name}" -n "${NS_APP}" | tail -20
    exit 1
  }
  echo "  \u2705 ${name} Ready"
done

if kubectl get deploy port-380-gate -n "${NS_APP}" >/dev/null 2>&1; then
  echo "\u2192 Applying deployment mTLS patch + pulse CronJob"
  kubectl apply -f "${MANIFEST_DIR}/02-deployment-mtls-patch.yaml" || true
  kubectl rollout status deploy/port-380-gate -n "${NS_APP}" --timeout=120s || true
else
  echo "\u2192 Deployment port-380-gate not found in ${NS_APP} (skip patch)"
fi

echo
echo "\u2705 cert-manager mTLS active"
kubectl get clusterissuer garden-selfsigned garden-ca-issuer
kubectl get certificate -n cert-manager garden-root-ca
kubectl get certificate -n "${NS_APP}"
echo
echo "Secrets: ${NS_APP}/port380-server-tls, port380-client-tls; cert-manager/garden-root-ca"
echo "Renewal is automatic (renewBefore on each Certificate)."
echo "Seal: \u2200\u221e\u03c6\u00b2 \u00b7 CERT_MANAGER_MTLS \u00b7 WOOD_DRAGON_0.91 \u00b7 SEALED"
