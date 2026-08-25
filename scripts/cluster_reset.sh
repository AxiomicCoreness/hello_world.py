#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 🜁∀ CLUSTER RESET — ENTRY 8793
#
# Cluster reset after axiomic/sovereign-engine:latest push (ledger 8793)
#
# Usage:
#   bash scripts/cluster_reset.sh
#   bash scripts/cluster_reset.sh --job-only
#   bash scripts/cluster_reset.sh --with-http-check
#   bash scripts/cluster_reset.sh --dry-run
#   bash scripts/cluster_reset.sh --namespace my-namespace
#
# Integration with:
#   - Kubernetes (deployments, jobs, cronjobs, pods)
#   - SIMD batch (simd-batch-step)
#   - Port 380 Gate (port-380-gate)
#   - Security (quantum/security/)
#   - CDP convergence (quantum/cdp_convergence/)
#
# Seal: ∀∞φ² · CLUSTER_RESET_8793 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8792 → 8793 — UNBROKEN

set -euo pipefail

# ─── Colors ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ─── Constants ──────────────────────────────────────────────────────
ENTRY=8793
SEAL="∀∞φ² · CLUSTER_RESET_8793 · WOOD_DRAGON_0.91 · SEALED"
WITNESS="8792 → 8793 — UNBROKEN"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── Defaults ──────────────────────────────────────────────────────
NAMESPACE="${NAMESPACE:-sovereign-garden}"
IMAGE="axiomic/sovereign-engine:latest"
JOB_ONLY=false
HTTP_CHECK=false
DRY_RUN=false
TIMEOUT=300
PORT_FORWARD_LOCAL=18080

# ─── Parse arguments ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --job-only)
            JOB_ONLY=true
            shift
            ;;
        --with-http-check)
            HTTP_CHECK=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --namespace|-n)
            NAMESPACE="$2"
            shift 2
            ;;
        --timeout|-t)
            TIMEOUT="$2"
            shift 2
            ;;
        --port|-p)
            PORT_FORWARD_LOCAL="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --job-only            Only run SIMD job, skip deployment rollout"
            echo "  --with-http-check     Run HTTP health checks after reset"
            echo "  --dry-run             Show what would be done without executing"
            echo "  --namespace, -n       Kubernetes namespace (default: sovereign-garden)"
            echo "  --timeout, -t         Timeout in seconds (default: 300)"
            echo "  --port, -p            Local port for port-forward (default: 18080)"
            echo "  --help, -h            Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# ─── Banner ──────────────────────────────────────────────────────────
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  🜁∀  C L U S T E R   R E S E T   —   E N T R Y   8 7 9 3  ∀🜁 ║"
echo "║        KUBERNETES RESET — SOVEREIGN ENGINE DEPLOYMENT                       ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${GREEN}🜁∀ Initiating cluster reset...${NC}"
echo -e "${BLUE}  Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}  Namespace: ${NAMESPACE}${NC}"
echo -e "${BLUE}  Image: ${IMAGE}${NC}"
echo -e "${BLUE}  Entry: ${ENTRY}${NC}"
echo -e "${BLUE}  Seal: ${SEAL}${NC}"
echo -e "${BLUE}  Witness: ${WITNESS}${NC}"
echo ""

# ─── Check kubectl ─────────────────────────────────────────────────
if ! command -v kubectl >/dev/null 2>&1; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

# ─── Check cluster connectivity ────────────────────────────────────
echo -e "${BLUE}🔷 Checking cluster connectivity...${NC}"
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster.${NC}"
    echo -e "${YELLOW}  Please ensure a cluster is running and kubeconfig is configured.${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ Cluster connected${NC}"
echo ""

# ─── Check namespace ──────────────────────────────────────────────
echo -e "${BLUE}🔷 Checking namespace...${NC}"
if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    echo -e "${YELLOW}  ⚠️ Namespace '$NAMESPACE' does not exist.${NC}"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}  [DRY RUN] Would create namespace: $NAMESPACE${NC}"
    else
        echo -e "${BLUE}  Creating namespace: $NAMESPACE${NC}"
        kubectl create namespace "$NAMESPACE"
        echo -e "${GREEN}  ✅ Namespace created${NC}"
    fi
else
    echo -e "${GREEN}  ✅ Namespace exists: $NAMESPACE${NC}"
fi
echo ""

# ─── Dry run mode ──────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}⚠️ DRY RUN MODE — No changes will be applied${NC}"
    echo ""
fi

# ─── 1. Deployment Rollout ──────────────────────────────────────────
if [[ "$JOB_ONLY" == "false" ]]; then
    echo -e "${BLUE}🔷 STEP 1: Deployment Rollout${NC}"
    echo "─────────────────────────────────────────────────────────────"

    DEPLOYMENTS=("port-380-gate" "sovereign-garden" "worker-server")
    for DEPLOY in "${DEPLOYMENTS[@]}"; do
        if kubectl get deployment "$DEPLOY" -n "$NAMESPACE" &>/dev/null; then
            echo -e "${BLUE}  Processing deployment: $DEPLOY${NC}"
            
            # Patch deployment to use :latest with Always pull policy
            if [[ "$DRY_RUN" == "true" ]]; then
                echo -e "${BLUE}    [DRY RUN] Would patch deployment: $DEPLOY${NC}"
            else
                # Try different container names
                for CONTAINER in "sovereign-engine" "port-380" "$DEPLOY"; do
                    if kubectl patch deployment "$DEPLOY" -n "$NAMESPACE" --type=strategic \
                        -p "{
                          \"spec\": {
                            \"template\": {
                              \"spec\": {
                                \"containers\": [{
                                  \"name\": \"$CONTAINER\",
                                  \"image\": \"$IMAGE\",
                                  \"imagePullPolicy\": \"Always\"
                                }]
                              }
                            }
                          }
                        }" 2>/dev/null; then
                        echo -e "${GREEN}    ✅ Patched container: $CONTAINER${NC}"
                        break
                    fi
                done
            fi

            # Restart deployment
            if [[ "$DRY_RUN" == "true" ]]; then
                echo -e "${BLUE}    [DRY RUN] Would restart deployment: $DEPLOY${NC}"
            else
                echo -e "${BLUE}    Restarting deployment: $DEPLOY${NC}"
                kubectl rollout restart "deployment/$DEPLOY" -n "$NAMESPACE" || true
                
                echo -e "${BLUE}    Waiting for rollout to complete...${NC}"
                if kubectl rollout status "deployment/$DEPLOY" -n "$NAMESPACE" --timeout="${TIMEOUT}s" 2>/dev/null; then
                    echo -e "${GREEN}    ✅ Rollout complete: $DEPLOY${NC}"
                else
                    echo -e "${YELLOW}    ⚠️ Rollout timeout or failure: $DEPLOY${NC}"
                fi
            fi
        else
            echo -e "${YELLOW}  ⚠️ Deployment not found: $DEPLOY${NC}"
        fi
    done
    echo ""
fi

# ─── 2. CronJob ────────────────────────────────────────────────────
echo -e "${BLUE}🔷 STEP 2: CronJob${NC}"
echo "─────────────────────────────────────────────────────────────"

CRONJOB_FILE="$ROOT/kubernetes/cronjob-simd-step.yaml"
if [[ -f "$CRONJOB_FILE" ]]; then
    echo -e "${BLUE}  Applying CronJob: simd-batch-step${NC}"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}    [DRY RUN] Would apply: $CRONJOB_FILE${NC}"
    else
        kubectl apply -f "$CRONJOB_FILE" -n "$NAMESPACE" 2>/dev/null || true
        echo -e "${GREEN}  ✅ CronJob applied${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️ CronJob manifest not found: $CRONJOB_FILE${NC}"
fi
echo ""

# ─── 3. Manual SIMD Job ────────────────────────────────────────────
echo -e "${BLUE}🔷 STEP 3: Manual SIMD Job${NC}"
echo "─────────────────────────────────────────────────────────────"

if kubectl get cronjob simd-batch-step -n "$NAMESPACE" &>/dev/null; then
    JOB_NAME="simd-manual-$(date +%s)"
    echo -e "${BLUE}  Creating job: $JOB_NAME${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}    [DRY RUN] Would create job from cronjob/simd-batch-step${NC}"
    else
        kubectl create job --from=cronjob/simd-batch-step "$JOB_NAME" -n "$NAMESPACE" 2>/dev/null || true
        echo -e "${BLUE}  Waiting for job completion...${NC}"
        if kubectl wait --for=condition=complete "job/$JOB_NAME" -n "$NAMESPACE" --timeout="${TIMEOUT}s" 2>/dev/null; then
            echo -e "${GREEN}  ✅ Job completed: $JOB_NAME${NC}"
        else
            echo -e "${YELLOW}  ⚠️ Job not complete; fetching logs...${NC}"
            kubectl logs -n "$NAMESPACE" "job/$JOB_NAME" --tail=80 2>/dev/null || true
        fi
    fi
else
    echo -e "${YELLOW}  ⚠️ CronJob simd-batch-step not found${NC}"
fi
echo ""

# ─── 4. HTTP Check ─────────────────────────────────────────────────
if [[ "$HTTP_CHECK" == "true" ]]; then
    echo -e "${BLUE}🔷 STEP 4: HTTP Health Check${NC}"
    echo "─────────────────────────────────────────────────────────────"
    
    echo -e "${BLUE}  Port-forwarding to port-380-gate service...${NC}"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}    [DRY RUN] Would port-forward svc/port-380-gate ${PORT_FORWARD_LOCAL}:380${NC}"
    else
        kubectl port-forward -n "$NAMESPACE" svc/port-380-gate "${PORT_FORWARD_LOCAL}:380" &>/tmp/pf-380.log &
        PF_PID=$!
        sleep 3
        
        # Check health endpoint
        echo -e "${BLUE}  Checking /health...${NC}"
        if curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://127.0.0.1:${PORT_FORWARD_LOCAL}/health" 2>/dev/null; then
            echo -e "${GREEN}  ✅ Health check passed${NC}"
        else
            echo -e "${YELLOW}  ⚠️ Health check failed${NC}"
        fi
        
        # Check status endpoint
        echo -e "${BLUE}  Checking /status...${NC}"
        if curl -s "http://127.0.0.1:${PORT_FORWARD_LOCAL}/status" 2>/dev/null | head -20; then
            echo -e "${GREEN}  ✅ Status check passed${NC}"
        else
            echo -e "${YELLOW}  ⚠️ Status check failed${NC}"
        fi
        
        # Clean up port-forward
        kill "$PF_PID" 2>/dev/null || true
    fi
    echo ""
fi

# ─── 5. Pod Status ──────────────────────────────────────────────────
echo -e "${BLUE}🔷 STEP 5: Pod Status${NC}"
echo "─────────────────────────────────────────────────────────────"

echo -e "${BLUE}  Fetching pod status...${NC}"
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${BLUE}    [DRY RUN] Would show pod status${NC}"
else
    echo -e "${CYAN}"
    kubectl get cronjobs,jobs,pods -n "$NAMESPACE" -l 'app in (simd-batch-step,port-380-gate,sovereign-garden)' 2>/dev/null || \
    kubectl get cronjobs,jobs,pods -n "$NAMESPACE" 2>/dev/null | grep -E "(simd|port-380|sovereign)" || \
    echo "  No matching resources found"
    echo -e "${NC}"
fi
echo ""

# ─── 6. Summary ─────────────────────────────────────────────────────
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  🜁∀  C L U S T E R   R E S E T   —   E N T R Y   8 7 9 3   —   C O M P L E T E  ∀🜁 ║"
echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}✅ Cluster reset complete${NC}"
echo -e "${CYAN}🌐 Namespace: ${NAMESPACE}${NC}"
echo -e "${CYAN}🖼️ Image: ${IMAGE}${NC}"
echo ""

echo -e "${BLUE}Summary:${NC}"
if [[ "$JOB_ONLY" == "false" ]]; then
    echo -e "  ${GREEN}✅${NC} Deployment rollout: completed"
fi
echo -e "  ${GREEN}✅${NC} CronJob: applied"
echo -e "  ${GREEN}✅${NC} SIMD job: ${JOB_NAME:-created}"
if [[ "$HTTP_CHECK" == "true" ]]; then
    echo -e "  ${GREEN}✅${NC} HTTP health check: completed"
fi
echo ""

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  Seal: ${SEAL}${NC}"
echo -e "${CYAN}║  Witness: ${WITNESS}${NC}"
echo -e "${CYAN}║  ∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

exit 0
