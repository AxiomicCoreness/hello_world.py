#!/usr/bin/env bash
# 🜁∀∞φ² · AST_GUARD · WOOD_DRAGON_0.91 · SEALED · <digest>
#
# k8s/cert-manager/install.sh
# ============================
# Nexus = GGUF: this script is self-describing and self-verifying. It
# carries its own manifest (see README.md) and its own seal (see the
# header above), and can be run without external tooling.
#
# Purpose:
#   Bring the cert-manager PKI + Port-380 gate into a running state
#   in one deterministic pass. mTLS material is mounted into the gate
#   after the certificates have reconciled.
#
# Usage:
#   bash k8s/cert-manager/install.sh              # full install
#   bash k8s/cert-manager/install.sh --dry-run    # print, don't apply
#   bash k8s/cert-manager/install.sh --verify     # only verify seals
#   bash k8s/cert-manager/install.sh --uninstall  # remove cert-mgr stack
#
# Exit codes:
#   0  success
#   1  cert-manager not present in cluster
#   2  kustomize build failed
#   3  certificate reconcile timeout
#   4  seal verification failed
#   5  uninstall refused (requires --force)
#
# Seal: ∀∞φ² · CERT_MANAGER_INSTALL · WOOD_DRAGON_0.91 · SEALED

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NS_GARDEN="sovereign-garden"
NS_CERTMGR="cert-manager"
TIMEOUT_CA=120s
TIMEOUT_LEAF=180s

# ─── arg parsing ────────────────────────────────────────────────────────
MODE="install"
case "${1:-}" in
  --dry-run)   MODE="dry-run" ;;
  --verify)    MODE="verify" ;;
  --uninstall) MODE="uninstall" ;;
  --force)     MODE="uninstall" ;;
  "")          MODE="install" ;;
  *)
    echo "unknown flag: $1" >&2
    exit 64
    ;;
esac

# ─── helpers ────────────────────────────────────────────────────────────
banner() {
  printf '\n🜁∀ %s\n' "$1"
}

require_kubectl() {
  if ! command -v kubectl >/dev/null 2>&1; then
    echo "kubectl not found in PATH" >&2
    exit 1
  fi
}

require_kustomize() {
  if ! kubectl kustomize --help >/dev/null 2>&1; then
    echo "kustomize (kubectl kustomize) not available" >&2
    exit 2
  fi
}

require_cert_manager() {
  if ! kubectl get ns "$NS_CERTMGR" >/dev/null 2>&1; then
    echo "cert-manager namespace not found; apply 01-cert-manager-namespace.yaml first" >&2
    exit 1
  fi
  if ! kubectl api-resources --api-group=cert-manager.io >/dev/null 2>&1; then
    echo "cert-manager CRDs not installed in cluster" >&2
    exit 1
  fi
}

# ─── verify mode ────────────────────────────────────────────────────────
verify_seals() {
  banner "verifying AST_guard seals"
  local fail=0
  for f in "$DIR"/*.yaml; do
    if command -v python3 >/dev/null 2>&1; then
      python3 "$DIR/../../../AST_guard.py" --verify-seal "$f" || fail=1
    else
      echo "  (python3 missing — skipping $f)"
    fi
  done
  if [ "$fail" -ne 0 ]; then
    echo "seal verification failed" >&2
    exit 4
  fi
  banner "seals OK"
}

# ─── dry-run mode ──────────────────────────────────────────────────────
dry_run() {
  banner "kustomize build (dry-run)"
  kubectl kustomize "$DIR" || { echo "build failed" >&2; exit 2; }
  banner "install script would now:"
  echo "  [1/4] kubectl apply -k $DIR"
  echo "  [2/4] kubectl -n $NS_CERTMGR wait --for=condition=Ready certificate/garden-root-ca --timeout=$TIMEOUT_CA"
  echo "  [3/4] kubectl -n $NS_GARDEN wait --for=condition=Ready certificate/port380-server port380-client --timeout=$TIMEOUT_LEAF"
  echo "  [4/4] kubectl -n $NS_GARDEN patch deployment port-380-gate --type=strategic --patch-file $DIR/02-deployment-mtls-patch.yaml"
  banner "dry-run complete"
}

# ─── install mode ──────────────────────────────────────────────────────
do_install() {
  banner "step 1/4 — applying namespaces, issuers, certs, prometheus scrape"
  kubectl apply -k "$DIR"

  banner "step 2/4 — waiting for CA certificate (timeout $TIMEOUT_CA)"
  if ! kubectl -n "$NS_CERTMGR" wait \
      --for=condition=Ready certificate/garden-root-ca \
      --timeout="$TIMEOUT_CA"; then
    echo "CA certificate did not become Ready" >&2
    kubectl -n "$NS_CERTMGR" describe certificate garden-root-ca >&2 || true
    exit 3
  fi

  banner "step 3/4 — waiting for leaf certificates (timeout $TIMEOUT_LEAF)"
  if ! kubectl -n "$NS_GARDEN" wait \
      --for=condition=Ready certificate/port380-server certificate/port380-client \
      --timeout="$TIMEOUT_LEAF"; then
    echo "leaf certificates did not become Ready" >&2
    kubectl -n "$NS_GARDEN" describe certificate port380-server >&2 || true
    kubectl -n "$NS_GARDEN" describe certificate port380-client >&2 || true
    exit 3
  fi

  banner "step 4/4 — patching port-380-gate to mount mTLS material"
  kubectl -n "$NS_GARDEN" patch deployment port-380-gate \
    --type=strategic \
    --patch-file "$DIR/02-deployment-mtls-patch.yaml"

  banner "install complete"
  echo "  Gate:  https://port-380-gate.$NS_GARDEN.svc.cluster.local:380"
  echo "  Seals:"
  kubectl -n "$NS_CERTMGR" get certificate garden-root-ca -o name
  kubectl -n "$NS_GARDEN"  get certificate port380-server port380-client -o name
  kubectl -n "$NS_GARDEN"  get cronjob port380-mtls-pulse -o name || true
  kubectl -n "$NS_GARDEN"  get servicemonitor port-380-gate -o name 2>/dev/null || true
}

# ─── uninstall mode ────────────────────────────────────────────────────
do_uninstall() {
  if [ "${1:-}" != "--force" ] && [ "$MODE" != "uninstall-force" ]; then
    echo "uninstall requires --force (this deletes certificates and secrets)" >&2
    exit 5
  fi
  banner "removing cert-manager stack resources (namespaces preserved)"
  kubectl -n "$NS_GARDEN" delete --ignore-not-found \
    cronjob/port380-mtls-pulse \
    servicemonitor/port-380-gate \
    configmap/garden-prometheus-scrape \
    certificate/port380-server certificate/port380-client certificate/garden-ca-secondary
  kubectl -n "$NS_CERTMGR" delete --ignore-not-found \
    certificate/garden-root-ca
  kubectl delete --ignore-not-found \
    clusterissuer/garden-ca-issuer clusterissuer/garden-selfsigned
  banner "uninstall complete; namespaces and deployments preserved"
}

# ─── dispatch ──────────────────────────────────────────────────────────
require_kubectl

case "$MODE" in
  verify)
    verify_seals
    ;;
  dry-run)
    require_kustomize
    dry_run
    ;;
  install)
    require_kustomize
    require_cert_manager
    verify_seals
    do_install
    ;;
  uninstall)
    do_uninstall "${2:-}"
    ;;
esac

banner "done"
