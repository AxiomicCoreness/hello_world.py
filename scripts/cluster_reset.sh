#!/usr/bin/env bash
# Cluster reset after axiomic/sovereign-engine:latest push (ledger 8793)
# Usage:
#   bash scripts/cluster_reset.sh
#   bash scripts/cluster_reset.sh --job-only
#   bash scripts/cluster_reset.sh --with-http-check
set -euo pipefail

NS="${NAMESPACE:-sovereign-garden}"
IMG="axiomic/sovereign-engine:latest"

echo "[cluster-reset] namespace=$NS image=$IMG"

if [[ "${1:-}" != "--job-only" ]]; then
  # Force Deployment pods to re-pull :latest
  if kubectl get deployment port-380-gate -n "$NS" &>/dev/null; then
    kubectl patch deployment port-380-gate -n "$NS" --type=strategic -p '{
      "spec": {
        "template": {
          "spec": {
            "containers": [{
              "name": "sovereign-engine",
              "image": "axiomic/sovereign-engine:latest",
              "imagePullPolicy": "Always"
            }]
          }
        }
      }
    }' 2>/dev/null || \
    kubectl patch deployment port-380-gate -n "$NS" --type=strategic -p '{
      "spec": {
        "template": {
          "spec": {
            "containers": [{
              "name": "port-380",
              "image": "axiomic/sovereign-engine:latest",
              "imagePullPolicy": "Always"
            }]
          }
        }
      }
    }' 2>/dev/null || true

    kubectl rollout restart deployment/port-380-gate -n "$NS" || true
    kubectl rollout status deployment/port-380-gate -n "$NS" --timeout=180s || true
  else
    echo "[cluster-reset] deployment/port-380-gate not found — skip rollout"
  fi

  # Ensure CronJob exists and uses Always
  kubectl apply -f kubernetes/cronjob-simd-step.yaml -n "$NS"
fi

# Manual one-shot SIMD job (mesh + step + dispatch)
JOB="simd-manual-$(date +%s)"
echo "[cluster-reset] creating Job $JOB from CronJob simd-batch-step"
kubectl create job --from=cronjob/simd-batch-step "$JOB" -n "$NS"
kubectl wait --for=condition=complete "job/$JOB" -n "$NS" --timeout=300s || \
  kubectl logs -n "$NS" "job/$JOB" --tail=80 || true

if [[ "${1:-}" == "--with-http-check" || "${2:-}" == "--with-http-check" ]]; then
  echo "[cluster-reset] port-forward health + mesh + deepseek status"
  kubectl port-forward -n "$NS" svc/port-380-gate 18080:380 &>/tmp/pf-380.log &
  PF=$!
  sleep 2
  curl -s -o /dev/null -w "health:%{http_code}\n" http://127.0.0.1:18080/health || true
  # If hello_world is the same image on another service, probe mesh/deepseek via deploy pod
  POD=$(kubectl get pods -n "$NS" -l app=port-380-gate -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
  if [[ -n "${POD:-}" ]]; then
    kubectl exec -n "$NS" "$POD" -- python -c "
from orchestrator.simd_step import local_mesh, local_step
import json
print(json.dumps({'step': local_step(0.99, 202.6, 0.0, 1.0), 'mesh': local_mesh(7, 202.6, 0.618)}, indent=2))
" 2>/dev/null || true
  fi
  kill $PF 2>/dev/null || true
fi

echo "[cluster-reset] done"
kubectl get cronjobs,jobs,pods -n "$NS" -l 'app in (simd-batch-step,port-380-gate)'
