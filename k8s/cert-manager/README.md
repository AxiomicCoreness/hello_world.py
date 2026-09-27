# k8s/cert-manager — Nexus = GGUF

This directory is a **single loadable identity** for the cert-manager PKI
that backs the Port-380 gate (Layer 314). Like a GGUF file, it is
self-describing: the manifest, the seal, the objects, and the apply
protocol are all contained here. No external documentation is required
to bring it up.

## Contents

| Path | Role |
|------|------|
| `00-namespace.yaml` | `sovereign-garden` namespace |
| `01-cert-manager-namespace.yaml` | `cert-manager` control-plane namespace |
| `01-issuers-and-certs.yaml` | ClusterIssuers + CA + leaf Certificates |
| `02-deployment-mtls-patch.yaml` | strategic-merge patch for the gate Deployment |
| `30-port380-mtls-pulse.yaml` | in-cluster 6h CronJob over mTLS |
| `40-prometheus-scrape.yaml` | ServiceMonitor + ConfigMap scrape config |
| `kustomization.yaml` | resource list + common labels |
| `install.sh` | one-shot installer (dry-run / verify / uninstall aware) |
| `README.md` | this file |

## Seal
