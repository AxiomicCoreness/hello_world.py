#!/bin/bash
# quantum/install_k8s.sh
# Installs the Port 380 Quantum Scaling Gate service into the Kubernetes cluster.

set -e

NAMESPACE="garden"
IMAGE="ghcr.io/axiomiccoreness/port-380:latest"

echo "🜁∀ DEPLOYING PORT 380 SCALING GATE TO KUBERNETES..."

# 1. Create the namespace if it doesn't exist
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# 2. Apply the Kubernetes Deployment
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: port-380-gate
  namespace: ${NAMESPACE}
  labels:
    app: port-380
    layer: 322
spec:
  replicas: 1
  selector:
    matchLabels:
      app: port-380
  template:
    metadata:
      labels:
        app: port-380
    spec:
      containers:
      - name: gate
        image: ${IMAGE}
        ports:
        - containerPort: 380
        env:
        - name: PYTHONPATH
          value: "/app"
        - name: GARDEN_MODE
          value: "production"
        livenessProbe:
          httpGet:
            path: /health
            port: 380
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 380
          initialDelaySeconds: 5
          periodSeconds: 5
EOF

# 3. Apply the Kubernetes Service (exposing port 380)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: port-380-gate-svc
  namespace: ${NAMESPACE}
  labels:
    app: port-380
spec:
  selector:
    app: port-380
  ports:
    - protocol: TCP
      port: 380
      targetPort: 380
      name: quantum-http
  type: ClusterIP
EOF

# 4. Apply the Kubernetes Ingress (exposing externally)
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: port-380-ingress
  namespace: ${NAMESPACE}
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: quantum.garden.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: port-380-gate-svc
            port:
              number: 380
EOF

echo "✅ PORT 380 DEPLOYMENT COMPLETE."
echo "🌐 Service available internally at: port-380-gate-svc.garden.svc.cluster.local:380"
echo "🌐 Ingress available at: http://quantum.garden.local"
