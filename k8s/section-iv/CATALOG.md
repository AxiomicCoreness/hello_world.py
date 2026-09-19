# Section IV — Genesis catalog

| File | Role |
|------|------|
| 00-namespace.yaml | namespace garden-argo-sink |
| 10-configmap-payload-schema.yaml | ARGO payload JSON schema |
| 20-service-headless.yaml | headless service, clusterIP None |
| 30-deployment-sink.yaml | sink deployment, replicas=0 |
| 40-networkpolicy.yaml | deny-by-default, ingress only on 8024 |
| MATH.md | capacity axiom |
| CATALOG.md | this file |

No rewrite of ledger files or prior k8s manifests.
