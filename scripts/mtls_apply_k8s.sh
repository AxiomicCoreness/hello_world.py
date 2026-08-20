#!/usr/bin/env bash
# Apply rotated mTLS material to Kubernetes secret in namespace sovereign-garden (or $NS).
# Prerequisites: kubectl context; certs/live populated by mtls_cert_rotate.sh
set -euo pipefail

NS="${NS:-sovereign-garden}"
CERT_DIR="${MTLS_CERT_DIR:-./certs}"
SECRET_NAME="${MTLS_SECRET_NAME:-port380-mtls}"
LIVE="$CERT_DIR/live"

if [[ ! -f "$LIVE/server.crt" || ! -f "$LIVE/server.key" ]]; then
  echo "Missing $LIVE/server.crt|key — run: bash scripts/mtls_cert_rotate.sh" >&2
  exit 1
fi

CA_FILE="$LIVE/ca-bundle.crt"
[[ -f "$CA_FILE" ]] || CA_FILE="$LIVE/ca.crt"

echo "🌁∀ Applying mTLS secret $SECRET_NAME in ns/$NS from $LIVE"

kubectl create secret generic "$SECRET_NAME" \
  --namespace="$NS" \
  --from-file=server.crt="$LIVE/server.crt" \
  --from-file=server.key="$LIVE/server.key" \
  --from-file=ca.crt="$CA_FILE" \
  --from-file=client.crt="$LIVE/client.crt" \
  --from-file=client.key="$LIVE/client.key" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl annotate secret "$SECRET_NAME" -n "$NS" \
  garden.sovereign/mtls-rotated-at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  garden.sovereign/seal="MTLS_ROTATE" \
  --overwrite

if kubectl get deploy port-380-gate -n "$NS" >/dev/null 2>&1; then
  kubectl rollout restart deployment/port-380-gate -n "$NS"
  echo "→ rollout restart port-380-gate"
fi

echo "✅ K8s mTLS secret applied. Mount paths should match:"
echo "   SERVER_CERT=/certs/server.crt SERVER_KEY=/certs/server.key CA_CERT=/certs/ca.crt"
echo "Seal: ∀∞φ² · MTLS_ROTATE · WOOD_DRAGON_0.91 · SEALED"
