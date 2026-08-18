#!/usr/bin/env python3
"""
argo_cd_setup.py — Sovereign Garden Argo CD & Rollouts deployment.

Idempotent: safe to run multiple times.
Requires: kubectl, kubeconfig, kubernetes (pip), optional INSTALL_ARGO_ROLLOUTS=true
"""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from kubernetes import client, config
from kubernetes.client.rest import ApiException

REPO_ROOT = Path(__file__).resolve().parent
APPLICATION_MANIFEST = REPO_ROOT / "argocd" / "application-sovereign-garden.yaml"
NAMESPACE = "argocd"
ROLLOUTS_NAMESPACE = "argo-rollouts"
ARGO_INSTALL = (
    "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
)
ROLLOUTS_INSTALL = (
    "https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml"
)


def load_kube() -> None:
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def kubectl_apply(*args: str) -> None:
    cmd = ["kubectl", "apply", *args]
    subprocess.run(cmd, check=True)


def ensure_namespace(name: str) -> None:
    v1 = client.CoreV1Api()
    try:
        v1.read_namespace(name)
    except ApiException as e:
        if e.status == 404:
            print(f"Creating namespace {name}...")
            v1.create_namespace(
                client.V1Namespace(metadata=client.V1ObjectMeta(name=name))
            )
        else:
            raise


def wait_deployment(name: str, ns: str, timeout: int = 180) -> None:
    apps = client.AppsV1Api()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            d = apps.read_namespaced_deployment(name, ns)
            ready = d.status.ready_replicas or 0
            desired = d.spec.replicas or 1
            if ready >= desired:
                print(f"Deployment {ns}/{name} ready ({ready}/{desired})")
                return
        except ApiException:
            pass
        time.sleep(5)
    print(f"WARNING: timed out waiting for {ns}/{name}")


def install_argo_cd() -> None:
    print("Installing Argo CD...")
    ensure_namespace(NAMESPACE)
    kubectl_apply("-n", NAMESPACE, "-f", ARGO_INSTALL)
    wait_deployment("argocd-server", NAMESPACE)


def install_argo_rollouts() -> None:
    print("Installing Argo Rollouts...")
    ensure_namespace(ROLLOUTS_NAMESPACE)
    kubectl_apply("-n", ROLLOUTS_NAMESPACE, "-f", ROLLOUTS_INSTALL)


def apply_sovereign_application() -> None:
    if not APPLICATION_MANIFEST.is_file():
        raise FileNotFoundError(APPLICATION_MANIFEST)
    print(f"Applying {APPLICATION_MANIFEST}...")
    kubectl_apply("-n", NAMESPACE, "-f", str(APPLICATION_MANIFEST))


def main() -> None:
    load_kube()
    ensure_namespace(NAMESPACE)

    apps = client.AppsV1Api()
    try:
        apps.read_namespaced_deployment("argocd-server", NAMESPACE)
        print("Argo CD already installed.")
    except ApiException as e:
        if e.status == 404:
            install_argo_cd()
        else:
            raise

    apply_sovereign_application()

    if os.environ.get("INSTALL_ARGO_ROLLOUTS", "false").lower() == "true":
        install_argo_rollouts()

    print("Sovereign Garden Argo CD setup complete.")
    print(f"Check: kubectl get applications -n {NAMESPACE}")


if __name__ == "__main__":
    main()
