#!/usr/bin/env bash
# 🜁∀∞φ² · CANVAS_INSTALL_ISTIO_TRAFFIC_SHIFT · WOOD_DRAGON_GATE · SEALED
#
# Canvas-local installer — canvases/istio-traffic-shifting/
# ---------------------------------------------------------------------------
# Applies the manifests for this canvas. Chooses one approach:
#   --approach=host     host-level (two Services + host-routed VS)
#   --approach=subset   subset-level (single Service + DestinationRule)
#   --approach=both     apply both (only if namespaces don't collide)
#
# Dry-run by default. Use --apply to actually send to the cluster.
#
# Usage:
#   bash install.sh                     # dry-run, approach=subset
#   bash install.sh --approach=host     # dry-run, host-level
#   bash install.sh --apply             # actually apply, subset-level
#   bash install.sh --apply --approach=host
#
# Exit codes:
#   0  success (dry-run or applied)
#   1  apply error
#   2  missing kubectl
# ---------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── Constants (canvas-scoped) ──────────────────────────────────────────
CANVAS_ID="istio-traffic-shifting"
LAYER="359"
RELATED_ENTRY="8809"
SEAL="∀∞φ² · ISTIO_TRAFFIC_SHIFT · WOOD_DRAGON_GATE · SEALED"

NAMESPACE="sovereign-garden"

# ─── Flags ──────────────────────────────────────────────────────────────
APPROACH="subset"
APPLY=0

for arg in "$@"; do
  case "$arg" in
    --approach=host)   APPROACH="host" ;;
    --approach=subset) APPROACH="subset" ;;
    --approach=both)   APPROACH="both" ;;
    --apply)           APPLY=1 ;;
    -h|--help)
      sed -n '3,25p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

# ─── Colour / TTY ───────────────────────────────────────────────────────
if [ -t 1 ]; then
  BOLD="$(printf '\033[1m')"
  RESET="$(printf '\033[0m')"
  GREEN="$(printf '\033[32m')"
  YELLOW="$(printf '\033[33m')"
  RED="$(printf '\033[31m')"
else
  BOLD=""; RESET=""; GREEN=""; YELLOW=""; RED=""
fi

say()  { printf '%s%s%s\n' "$BOLD" "$1" "$RESET"; }
ok()   { printf '%s✅ %s%s\n' "$GREEN" "$1" "$RESET"; }
warn() { printf '%s⚠️  %s%s\n' "$YELLOW" "$1" "$RESET"; }
die()  { printf '%s❌ %s%s\n' "$RED" "$1" "$RESET" >&2; exit "${2:-1}"; }

# ─── Banner ─────────────────────────────────────────────────────────────
say "🜁∀ Canvas · ${CANVAS_ID} · layer ${LAYER} · entry ${RELATED_ENTRY}"
say "   seal: ${SEAL}"
say ""

# ─── kubectl check ──────────────────────────────────────────────────────
if [ "$APPLY" = "1" ]; then
  command -v kubectl >/dev/null 2>&1 || die "kubectl not found" 2
fi

# ─── Manifest selection ─────────────────────────────────────────────────
FILES=()
case "$APPROACH" in
  host)
    FILES=(
      "${SCRIPT_DIR}/service-stable.yaml"
      "${SCRIPT_DIR}/service-canary.yaml"
      "${SCRIPT_DIR}/virtualservice.yaml"
      "${SCRIPT_DIR}/rollout.yaml"
    )
    ;;
  subset)
    FILES=(
      "${SCRIPT_DIR}/service.yaml"
      "${SCRIPT_DIR}/destinationrule.yaml"
      "${SCRIPT_DIR}/virtualservice.yaml"
      "${SCRIPT_DIR}/rollout.yaml"
    )
    ;;
  both)
    warn "both mode requires non-colliding Service names — verify before --apply"
    FILES=(
      "${SCRIPT_DIR}/service-stable.yaml"
      "${SCRIPT_DIR}/service-canary.yaml"
      "${SCRIPT_DIR}/service.yaml"
      "${SCRIPT_DIR}/destinationrule.yaml"
      "${SCRIPT_DIR}/virtualservice.yaml"
      "${SCRIPT_DIR}/rollout.yaml"
    )
    ;;
esac

# ─── Existence check ────────────────────────────────────────────────────
for f in "${FILES[@]}"; do
  if [ ! -f "$f" ]; then
    die "manifest missing: $f" 1
  fi
done
ok "approach=${APPROACH} · ${#FILES[@]} manifest(s) located"

# ─── Apply / dry-run ────────────────────────────────────────────────────
for f in "${FILES[@]}"; do
  if [ "$APPLY" = "1" ]; then
    say "→ applying $(basename "$f")"
    kubectl apply -n "${NAMESPACE}" -f "$f"
  else
    say "→ [dry-run] kubectl apply -n ${NAMESPACE} -f $(basename "$f")"
  fi
done

# ─── Verification hint ──────────────────────────────────────────────────
say ""
if [ "$APPLY" = "1" ]; then
  ok "applied — check the VirtualService weights:"
  say "    kubectl -n ${NAMESPACE} get virtualservice sovereign-garden -o yaml"
  say "    kubectl argo rollouts get rollout sovereign-garden -n ${NAMESPACE}"
else
  ok "dry-run complete — pass --apply to send to the cluster"
fi

say ""
say "∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞"
