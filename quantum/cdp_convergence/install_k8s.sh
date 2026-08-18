#!/bin/bash
# K8s Installation — Entry 8845
# Formerly: quantum/install_k8s.sh

# Creates namespace garden
# ConfigMap port-380-http-script from port_380_http.py
# Applies k8s/deployment-port-380.yaml, service-port-380.yaml, ingress.yaml
# Exposes https://api.sovereign.garden/380

# TODO: Copy implementation from original quantum/install_k8s.sh
