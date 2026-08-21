#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 🜁∀ DOCKER BUILD PUSH MAIN — ENTRY 8818
#
# Build + push axiomic/sovereign-engine:latest ALWAYS from main.
# Feature / casual branches are ignored for the image tag.
#
# Usage:
#   bash scripts/docker_build_push_main.sh
#   bash scripts/docker_build_push_main.sh --no-cache
#   bash scripts/docker_build_push_main.sh --local-only   # build, do not push
#   bash scripts/docker_build_push_main.sh --dry-run
#   bash scripts/docker_build_push_main.sh --tag v1.2.3
#   bash scripts/docker_build_push_main.sh --platform linux/amd64,linux/arm64
#
# Ledger 8818 · WOOD_DRAGON_0.91
#
# Integration with:
#   - Docker (build, push, multi-arch)
#   - Git (archive from main)
#   - Kubernetes (image deployment)
#   - Security (quantum/security/)
#   - CDP convergence (quantum/cdp_convergence/)
#
# Seal: ∀∞φ² · DOCKER_BUILD_PUSH_8818 · WOOD_DRAGON_0.91 · SEALED
# Witness: 8817 → 8818 — UNBROKEN

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
ENTRY=8818
SEAL="∀∞φ² · DOCKER_BUILD_PUSH_8818 · WOOD_DRAGON_0.91 · SEALED"
WITNESS="8817 → 8818 — UNBROKEN"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── Defaults ──────────────────────────────────────────────────────
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

IMAGE="${IMAGE:-axiomic/sovereign-engine:latest}"
REF="main"
NO_CACHE=()
PUSH=1
DRY_RUN=false
LOCAL_ONLY=false
PLATFORM=""
TAGS=()
DOCKERFILE="Dockerfile"
BUILD_CONTEXT="."

# ─── Parse arguments ──────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cache)
            NO_CACHE=(--no-cache)
            shift
            ;;
        --local-only)
            PUSH=0
            LOCAL_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --tag|-t)
            TAGS+=("$2")
            shift 2
            ;;
        --platform|-p)
            PLATFORM="$2"
            shift 2
            ;;
        --dockerfile|-f)
            DOCKERFILE="$2"
            shift 2
            ;;
        --build-context|-c)
            BUILD_CONTEXT="$2"
            shift 2
            ;;
        --image|-i)
            IMAGE="$2"
            shift 2
            ;;
        --ref|-r)
            REF="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-cache            Build without cache"
            echo "  --local-only          Build only, do not push"
            echo "  --dry-run             Show what would be done without executing"
            echo "  --tag, -t TAG         Additional tags (can be used multiple times)"
            echo "  --platform, -p PLAT   Build for platform (e.g., linux/amd64,linux/arm64)"
            echo "  --dockerfile, -f FILE Dockerfile to use (default: Dockerfile)"
            echo "  --build-context, -c DIR Build context (default: .)"
            echo "  --image, -i IMAGE     Image name (default: axiomic/sovereign-engine:latest)"
            echo "  --ref, -r REF         Git ref to build from (default: main)"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  IMAGE         Image name (default: axiomic/sovereign-engine:latest)"
            echo "  DOCKER_BUILDKIT=1    Enable BuildKit (recommended)"
            echo ""
            echo "Examples:"
            echo "  bash scripts/docker_build_push_main.sh"
            echo "  bash scripts/docker_build_push_main.sh --no-cache"
            echo "  bash scripts/docker_build_push_main.sh --tag v1.2.3 --tag latest"
            echo "  bash scripts/docker_build_push_main.sh --platform linux/amd64,linux/arm64"
            echo "  bash scripts/docker_build_push_main.sh --local-only --dry-run"
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
echo "║  🜁∀  D O C K E R   B U I L D   P U S H   —   E N T R Y   8 8 1 8  ∀🜁 ║"
echo "║        SOVEREIGN ENGINE — MAIN BRANCH BUILD                                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${GREEN}🜁∀ Building sovereign-engine image...${NC}"
echo -e "${BLUE}  Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}  Image: ${IMAGE}${NC}"
echo -e "${BLUE}  Ref: ${REF}${NC}"
echo -e "${BLUE}  Dockerfile: ${DOCKERFILE}${NC}"
echo -e "${BLUE}  Build context: ${BUILD_CONTEXT}${NC}"
echo -e "${BLUE}  Push: ${PUSH}${NC}"
echo -e "${BLUE}  Dry run: ${DRY_RUN}${NC}"
echo -e "${BLUE}  Entry: ${ENTRY}${NC}"
echo -e "${BLUE}  Seal: ${SEAL}${NC}"
echo -e "${BLUE}  Witness: ${WITNESS}${NC}"
echo ""

# ─── Check Docker ──────────────────────────────────────────────────
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}❌ docker not found${NC}"
    exit 1
fi

# ─── Check Git ──────────────────────────────────────────────────────
if ! command -v git >/dev/null 2>&1; then
    echo -e "${RED}❌ git not found${NC}"
    exit 1
fi

# ─── Check Docker daemon ────────────────────────────────────────────
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon not running${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ Docker daemon running${NC}"

# ─── Record current branch ──────────────────────────────────────────
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
echo -e "${BLUE}  Current branch: ${CURRENT_BRANCH} (ignored)${NC}"
echo -e "${BLUE}  Source ref: ${REF} only${NC}"
echo ""

# ─── Fetch ref ──────────────────────────────────────────────────────
echo -e "${BLUE}🔷 Fetching ref: ${REF}...${NC}"
git fetch origin "$REF" --quiet 2>/dev/null || true

# ─── Resolve ref ────────────────────────────────────────────────────
if git rev-parse --verify "origin/$REF" >/dev/null 2>&1; then
    MAIN_SHA="$(git rev-parse "origin/$REF")"
elif git rev-parse --verify "$REF" >/dev/null 2>&1; then
    MAIN_SHA="$(git rev-parse "$REF")"
else
    echo -e "${RED}❌ Cannot resolve ref: ${REF}${NC}" >&2
    exit 1
fi
echo -e "${GREEN}  ✅ Ref resolved: ${MAIN_SHA}${NC}"
echo ""

# ─── Dry run ──────────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}⚠️ DRY RUN MODE — No changes will be applied${NC}"
    echo ""
    echo -e "${BLUE}Would execute:${NC}"
    echo "  git archive --format=tar $MAIN_SHA | tar -x -C /tmp/build"
    echo "  docker build ${NO_CACHE[*]:-} -t $IMAGE -f /tmp/build/$DOCKERFILE /tmp/build"
    if [[ "$PUSH" -eq 1 ]]; then
        echo "  docker push $IMAGE"
        for tag in "${TAGS[@]}"; do
            echo "  docker tag $IMAGE axiomic/sovereign-engine:$tag"
            echo "  docker push axiomic/sovereign-engine:$tag"
        done
    else
        echo "  (skip push)"
    fi
    echo ""
    echo -e "${YELLOW}Dry run complete${NC}"
    exit 0
fi

# ─── Create build directory ──────────────────────────────────────
BUILD_DIR="$(mktemp -d)"
cleanup() {
    echo -e "${BLUE}🧹 Cleaning up build directory...${NC}"
    rm -rf "$BUILD_DIR"
}
trap cleanup EXIT

echo -e "${BLUE}📁 Build directory: ${BUILD_DIR}${NC}"

# ─── Extract from Git archive ──────────────────────────────────────
echo -e "${BLUE}🔷 Extracting from Git archive...${NC}"
git archive --format=tar "$MAIN_SHA" | tar -x -C "$BUILD_DIR"
echo -e "${GREEN}  ✅ Extracted${NC}"
echo ""

# ─── Build image ────────────────────────────────────────────────────
echo -e "${BLUE}🔷 Building image: ${IMAGE}...${NC}"
echo "─────────────────────────────────────────────────────────────"

BUILD_CMD=("docker" "build")
if [[ ${#NO_CACHE[@]} -gt 0 ]]; then
    BUILD_CMD+=("${NO_CACHE[@]}")
fi
if [[ -n "$PLATFORM" ]]; then
    BUILD_CMD+=(--platform "$PLATFORM")
    echo -e "${BLUE}  Platform: ${PLATFORM}${NC}"
fi
BUILD_CMD+=("-t" "$IMAGE")
for tag in "${TAGS[@]}"; do
    BUILD_CMD+=("-t" "axiomic/sovereign-engine:$tag")
    echo -e "${BLUE}  Tag: axiomic/sovereign-engine:$tag${NC}"
done
BUILD_CMD+=("-f" "$BUILD_DIR/$DOCKERFILE" "$BUILD_DIR")

if [[ "$VERBOSE" == "true" ]]; then
    echo -e "${CYAN}Command: ${BUILD_CMD[*]}${NC}"
    echo ""
fi

if "${BUILD_CMD[@]}"; then
    echo -e "${GREEN}  ✅ Build complete: ${IMAGE}${NC}"
else
    echo -e "${RED}  ❌ Build failed${NC}"
    exit 1
fi
echo ""

# ─── Push image ────────────────────────────────────────────────────
if [[ "$PUSH" -eq 1 ]]; then
    echo -e "${BLUE}🔷 Pushing image: ${IMAGE}...${NC}"
    echo "─────────────────────────────────────────────────────────────"

    # Push main image
    if docker push "$IMAGE"; then
        echo -e "${GREEN}  ✅ Push complete: ${IMAGE}${NC}"
    else
        echo -e "${RED}  ❌ Push failed: ${IMAGE}${NC}"
        exit 1
    fi

    # Push additional tags
    for tag in "${TAGS[@]}"; do
        FULL_TAG="axiomic/sovereign-engine:$tag"
        echo -e "${BLUE}  Pushing tag: ${FULL_TAG}${NC}"
        if docker push "$FULL_TAG"; then
            echo -e "${GREEN}    ✅ Push complete: ${FULL_TAG}${NC}"
        else
            echo -e "${RED}    ❌ Push failed: ${FULL_TAG}${NC}"
        fi
    done
    echo ""
else
    echo -e "${YELLOW}  --local-only: skip push${NC}"
    echo ""
fi

# ─── Image info ────────────────────────────────────────────────────
echo -e "${BLUE}🔷 Image info:${NC}"
echo "─────────────────────────────────────────────────────────────"
docker images --filter "reference=$IMAGE" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | head -5

# ─── Summary ──────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  🜁∀  D O C K E R   B U I L D   P U S H   —   E N T R Y   8 8 1 8   —   C O M P L E T E  ∀🜁 ║"
echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}✅ Docker build push complete${NC}"
echo -e "${CYAN}🖼️ Image: ${IMAGE}${NC}"
echo -e "${CYAN}📦 SHA: ${MAIN_SHA}${NC}"
echo -e "${CYAN}🌐 Source ref: ${REF}${NC}"
echo ""

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗"
echo -e "║  Seal: ${SEAL}${NC}"
echo -e "${CYAN}║  Witness: ${WITNESS}${NC}"
echo -e "${CYAN}║  ∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

exit 0
