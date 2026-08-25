#!/usr/bin/env python3
"""
flux_cd_setup.py — Sovereign Garden Flux CD GitOps setup.

Creates GitRepository + Kustomization for AxiomicCoreness/hello_world.py.
Bootstrap via flux CLI is optional (FLUX_BOOTSTRAP=true).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from kubernetes import client, config
from kubernetes.client.rest import ApiException

REPO_URL = "https://github.com/AxiomicCoreness/hello_world.py"
BRANCH = "main"
NAMESPACE = "flux-system"
SOURCE_GROUP = "source.toolkit.fluxcd.io"
KUSTOMIZE_GROUP = "kustomize.toolkit.fluxcd.io"
API_VERSION = "v1"


def load_kube() -> None:
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def ensure_flux_cli() -> None:
    if shutil.which("flux"):
        print("flux CLI present:", run_cmd(["flux", "--version"]).stdout.strip())
        return
    print("flux CLI not found — install from https://fluxcd.io/flux/installation/")
    print("Skipping CLI install (non-interactive). Set FLUX_BOOTSTRAP only if flux is installed.")


def bootstrap_flux() -> None:
    if os.environ.get("FLUX_BOOTSTRAP", "false").lower() != "true":
        print("FLUX_BOOTSTRAP!=true — skip bootstrap (use existing flux-system or install manually)")
        return
    ensure_flux_cli()
    if not shutil.which("flux"):
        raise RuntimeError("flux CLI required for bootstrap")
    # Personal bootstrap needs GITHUB_TOKEN
    cmd = [
        "flux",
        "bootstrap",
        "github",
        "--owner=AxiomicCoreness",
        "--repository=hello_world.py",
        f"--branch={BRANCH}",
        "--path=kubernetes/",
        "--personal",
    ]
    print("Bootstrapping Flux...", " ".join(cmd))
    subprocess.run(cmd, check=True)


def ensure_namespace(name: str) -> None:
    v1 = client.CoreV1Api()
    try:
        v1.read_namespace(name)
    except ApiException as e:
        if e.status == 404:
            v1.create_namespace(
                client.V1Namespace(metadata=client.V1ObjectMeta(name=name))
            )
        else:
            raise


def upsert_git_repository() -> None:
    api = client.CustomObjectsApi()
    body = {
        "apiVersion": f"{SOURCE_GROUP}/{API_VERSION}",
        "kind": "GitRepository",
        "metadata": {"name": "sovereign-garden", "namespace": NAMESPACE},
        "spec": {
            "interval": "1m",
            "url": REPO_URL,
            "ref": {"branch": BRANCH},
        },
    }
    try:
        api.create_namespaced_custom_object(
            group=SOURCE_GROUP,
            version=API_VERSION,
            namespace=NAMESPACE,
            plural="gitrepositories",
            body=body,
        )
        print("GitRepository created.")
    except ApiException as e:
        if e.status == 409:
            api.patch_namespaced_custom_object(
                group=SOURCE_GROUP,
                version=API_VERSION,
                namespace=NAMESPACE,
                plural="gitrepositories",
                name="sovereign-garden",
                body=body,
            )
            print("GitRepository patched.")
        else:
            raise


def upsert_kustomization() -> None:
    api = client.CustomObjectsApi()
    body = {
        "apiVersion": f"{KUSTOMIZE_GROUP}/{API_VERSION}",
        "kind": "Kustomization",
        "metadata": {"name": "sovereign-garden", "namespace": NAMESPACE},
        "spec": {
            "interval": "5m",
            "path": "./kubernetes",
            "prune": True,
            "sourceRef": {"kind": "GitRepository", "name": "sovereign-garden"},
        },
    }
    try:
        api.create_namespaced_custom_object(
            group=KUSTOMIZE_GROUP,
            version=API_VERSION,
            namespace=NAMESPACE,
            plural="kustomizations",
            body=body,
        )
        print("Kustomization created.")
    except ApiException as e:
        if e.status == 409:
            api.patch_namespaced_custom_object(
                group=KUSTOMIZE_GROUP,
                version=API_VERSION,
                namespace=NAMESPACE,
                plural="kustomizations",
                name="sovereign-garden",
                body=body,
            )
            print("Kustomization patched.")
        else:
            raise


def main() -> None:
    load_kube()
    ensure_flux_cli()
    bootstrap_flux()
    # CR create requires flux controllers already in cluster
    try:
        ensure_namespace(NAMESPACE)
        upsert_git_repository()
        upsert_kustomization()
    except ApiException as e:
        print(f"Flux CRDs unavailable ({e.status}). Install/bootstrap Flux first.")
        raise SystemExit(1) from e
    print("Sovereign Garden Flux CD setup complete.")
    print("Check: kubectl get gitrepositories,kustomizations -n flux-system")


if __name__ == "__main__":
    main()
