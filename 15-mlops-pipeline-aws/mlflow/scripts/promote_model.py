"""
Model Promotion Script
Promotes an MLflow model to Production stage and triggers GitOps deployment
by updating the Kubernetes kustomization.yaml in the repo.

Usage:
    python promote_model.py \
        --model-name fraud-detector \
        --version 42 \
        --stage Production
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient


MLFLOW_TRACKING_URI = os.environ.get(
    "MLFLOW_TRACKING_URI",
    "http://mlflow-svc.mlops.svc.cluster.local:5000",
)
GITHUB_REPO = os.environ.get("GITHUB_REPO", "viveksinghfx/Devop_Portfolio")
KUSTOMIZATION_PATH = "15-mlops-pipeline-aws/k8s/overlays/prod/kustomization.yaml"


def promote_model(model_name: str, version: int, stage: str) -> str:
    """Transition model stage in MLflow and return the model URI."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    # Demote current champion if moving to Production
    if stage == "Production":
        for mv in client.get_latest_versions(model_name, stages=["Production"]):
            client.transition_model_version_stage(
                name=model_name,
                version=mv.version,
                stage="Archived",
            )
            print(f"Archived previous champion: {model_name} v{mv.version}")

    client.transition_model_version_stage(
        name=model_name,
        version=str(version),
        stage=stage,
    )
    print(f"Promoted {model_name} v{version} → {stage}")

    model_uri = f"models:/{model_name}/{version}"
    return model_uri


def update_kustomization(model_name: str, version: int, model_uri: str) -> None:
    """
    Update the prod kustomization.yaml with the new model image tag.
    This commit is picked up by ArgoCD to trigger a rollout.
    """
    # In CI (GitHub Actions), the repo is already checked out
    kust_path = Path(KUSTOMIZATION_PATH)
    if not kust_path.exists():
        print(f"Kustomization not found at {kust_path}; skipping GitOps update")
        return

    content = kust_path.read_text()
    # Replace model URI annotation / image tag
    import re
    content = re.sub(
        r'(model-uri:\s*).*',
        f'model-uri: "{model_uri}"',
        content,
    )
    content = re.sub(
        r'(model-version:\s*).*',
        f'model-version: "{version}"',
        content,
    )
    kust_path.write_text(content)
    print(f"Updated {KUSTOMIZATION_PATH} with model URI: {model_uri}")

    subprocess.run(["git", "add", KUSTOMIZATION_PATH], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"chore(mlops): promote {model_name} v{version} to {MLFLOW_TRACKING_URI.split('.')[-1]}"],
        check=True,
    )
    subprocess.run(["git", "push"], check=True)
    print("GitOps commit pushed — ArgoCD will detect and roll out the new model")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--version", required=True, type=int)
    parser.add_argument("--stage", default="Production", choices=["Staging", "Production"])
    parser.add_argument("--skip-gitops", action="store_true")
    args = parser.parse_args()

    model_uri = promote_model(args.model_name, args.version, args.stage)

    if not args.skip_gitops and args.stage == "Production":
        update_kustomization(args.model_name, args.version, model_uri)


if __name__ == "__main__":
    main()
