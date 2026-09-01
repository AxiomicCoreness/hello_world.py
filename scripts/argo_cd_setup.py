# argo_cd_setup.py
"""
Argo CD Python fallback setup.
"""
import os
from kubernetes import client, config

def setup_k8s():
    try:
        config.load_incluster_config()
        print("✅ In-cluster config loaded")
    except:
        config.load_kube_config()
        print("✅ Kubeconfig loaded from local")
    return client.CoreV1Api()

if __name__ == "__main__":
    v1 = setup_k8s()
    try:
        ns = v1.read_namespace("argocd")
        print(f"✅ Namespace argocd found: {ns.metadata.name}")
    except Exception as e:
        print(f"❌ Error: {e}")
