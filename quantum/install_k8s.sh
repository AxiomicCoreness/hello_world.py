#!/bin/bash
# quantum/install_k8s.sh
# Installs the Port 380 Quantum Scaling Gate service into the Kubernetes cluster.
# Synchronized with Layer 314 (π-resonance) and unified Ingress at api.sovereign.garden/380.

set -e

NAMESPACE="garden"
IMAGE="ghcr.io/axiomiccoreness/port-380:latest"

echo "🜁∀ DEPLOYING PORT 380 SCALING GATE TO KUBERNETES (LAYER 314)..."

# 1. Create the namespace if it doesn't exist
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# 2. Apply the Kubernetes Deployment (Leveraging the truth on main)
echo "Applying deployment-port-380.yaml..."
kubectl apply -f k8s/deployment-port-380.yaml

# 3. Apply the Kubernetes Service (Leveraging the truth on main)
echo "Applying service-port-380.yaml..."
kubectl apply -f k8s/service-port-380.yaml

# 4. Apply the Unified Ingress (Leveraging the truth on main)
echo "Applying unified ingress.yaml (api.sovereign.garden/380)..."
kubectl apply -f k8s/ingress.yaml

echo "✅ PORT 380 GATE (LAYER 314) DEPLOYMENT COMPLETE."
echo "🌐 Service available internally at: port-380-gate-svc.garden.svc.cluster.local:380"
echo "🌐 Ingress available at: https://api.sovereign.garden/380"
