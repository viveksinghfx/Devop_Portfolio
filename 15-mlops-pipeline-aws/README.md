# End-to-End MLOps Pipeline on AWS

Complete MLOps lifecycle on AWS: data versioning in S3, experiment tracking with MLflow, automated retraining pipelines in Kubeflow, GitOps-driven model promotion via ArgoCD, and automated drift detection. New model versions reach production in under 15 minutes from merge with zero manual steps.

## Architecture

```
  ┌──────────────────────────────────────────────────────────────┐
  │                      DATA LAYER                              │
  │  S3 (raw) ──► DVC versioning ──► S3 (processed features)    │
  └─────────────────────────┬────────────────────────────────────┘
                             │
  ┌──────────────────────────▼────────────────────────────────────┐
  │                   TRAINING LAYER                              │
  │  Kubeflow Pipeline                                            │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
  │  │ Ingest   │→ │ Feature  │→ │  Train   │→ │ Evaluate   │  │
  │  │ & Validate│  │ Engineer │  │  (SKLearn│  │ (F1/AUC)   │  │
  │  └──────────┘  └──────────┘  │  /XGBoost│  └─────┬──────┘  │
  │                               └──────────┘        │          │
  └──────────────────────────────────────────── pass? ┘          │
                                                  │               │
  ┌───────────────────────────────────────────────▼──────────────┐
  │                   REGISTRY LAYER                              │
  │  MLflow Tracking Server (RDS backend, S3 artifact store)     │
  │  ┌─────────────────────────────────────────────────────────┐ │
  │  │  Experiment runs · Metrics · Params · Model artifacts   │ │
  │  └──────────────────────────┬──────────────────────────────┘ │
  └─────────────────────────────┼────────────────────────────────┘
                                 │  promote to "Production" stage
  ┌──────────────────────────────▼────────────────────────────────┐
  │                   DEPLOYMENT LAYER (GitOps)                   │
  │                                                               │
  │  model-promotion-bot (GitHub Actions)                         │
  │   ├── pulls model URI from MLflow registry                    │
  │   ├── updates k8s/overlays/prod/kustomization.yaml           │
  │   └── opens PR or auto-merges to main                        │
  │                 │                                             │
  │                 ▼                                             │
  │  ArgoCD watches repo → syncs inference Deployment to EKS     │
  │  Argo Rollouts: canary 10% → 50% → 100% over 10 min         │
  └──────────────────────────────────────────────────────────────┘
                                 │
  ┌──────────────────────────────▼────────────────────────────────┐
  │                  OBSERVABILITY & DRIFT                        │
  │  drift-detection/ (Evidently AI, runs as CronJob)            │
  │   ├── compares live prediction distribution vs training       │
  │   ├── Prometheus metrics: data_drift_score, psi_score        │
  │   └── Alertmanager → triggers Kubeflow retraining pipeline   │
  └──────────────────────────────────────────────────────────────┘
```

## Stack

| Layer | Tool |
|-------|------|
| **Data versioning** | DVC + AWS S3 |
| **Feature store** | S3 + Parquet (offline) |
| **Experiment tracking** | MLflow (RDS backend + S3 artifacts) |
| **Pipeline orchestration** | Kubeflow Pipelines v2 |
| **Model registry** | MLflow Model Registry |
| **Deployment** | Kubernetes (EKS) + Argo Rollouts |
| **GitOps CD** | ArgoCD |
| **IaC** | Terraform (EKS, RDS, S3, IAM, VPC) |
| **Drift detection** | Evidently AI (K8s CronJob) |
| **Observability** | Prometheus + Grafana + Alertmanager |
| **CI** | GitHub Actions |

## Key Results

- **Model in production in < 15 minutes** from merge to main, fully automated
- **Automated drift detection** triggers retraining without human intervention
- **Full experiment lineage** — every production model traceable to its dataset version, code commit, and hyperparameters
- **Canary rollouts** via Argo Rollouts; automatic rollback on metric degradation

## Quick Start

### 1. Provision AWS infrastructure

```bash
cd terraform
terraform init
terraform workspace new prod
terraform apply -var-file="envs/prod.tfvars"
```

### 2. Deploy Kubeflow Pipelines

```bash
# Install KFP on existing EKS cluster
kubectl apply -k kubeflow/install/

# Compile and upload the training pipeline
cd kubeflow/pipelines
pip install kfp==2.7.0
python training_pipeline.py --compile
kfp pipeline upload --endpoint $KFP_ENDPOINT training_pipeline.yaml
```

### 3. Start MLflow Tracking Server

```bash
kubectl apply -f mlflow/k8s/mlflow-deployment.yaml

# MLflow will connect to RDS (Postgres) and use S3 for artifacts
# Connection string injected via Kubernetes secret
```

### 4. Trigger a training run

```bash
# Manual trigger via KFP SDK
python kubeflow/scripts/trigger_run.py \
  --dataset-version v1.2.3 \
  --model-type xgboost \
  --experiment-name "fraud-detection-prod"

# Or push to main — GitHub Actions triggers automatically
git push origin main
```

### 5. Promote a model to production

```bash
python mlflow/scripts/promote_model.py \
  --model-name fraud-detector \
  --version 42 \
  --stage Production
# This triggers the GitHub Actions model-promotion workflow
```

## Repository Structure

```
15-mlops-pipeline-aws/
├── terraform/
│   ├── modules/
│   │   ├── eks/              # EKS cluster + node groups
│   │   ├── rds/              # Postgres for MLflow backend
│   │   └── s3-buckets/       # data, artifacts, model store
│   └── envs/
│       ├── dev.tfvars
│       └── prod.tfvars
├── kubeflow/
│   ├── pipelines/
│   │   └── training_pipeline.py   # KFP v2 pipeline definition
│   ├── components/
│   │   ├── ingest/           # Data ingestion + validation
│   │   ├── feature_eng/      # Feature engineering
│   │   ├── train/            # Model training (XGBoost / sklearn)
│   │   └── evaluate/         # Evaluation + pass/fail gate
│   └── scripts/
│       └── trigger_run.py
├── mlflow/
│   ├── k8s/
│   │   └── mlflow-deployment.yaml
│   └── scripts/
│       ├── promote_model.py  # Promotes model + triggers GitOps
│       └── fetch_model.py    # Fetches production model URI
├── argocd/
│   ├── app-of-apps.yaml
│   └── apps/
│       ├── mlflow.yaml
│       └── inference-service.yaml
├── drift-detection/
│   ├── detector.py           # Evidently AI drift checks
│   ├── k8s/
│   │   └── cronjob.yaml      # Runs every 6 hours
│   └── requirements.txt
└── docs/
    ├── architecture.md
    ├── drift-detection.md
    └── model-promotion.md
```

## Drift Detection

The drift detector (`drift-detection/detector.py`) runs as a Kubernetes CronJob every 6 hours:

1. Fetches production prediction logs from S3
2. Compares distribution against training data (PSI, KS-test, Evidently reports)
3. Publishes `data_drift_score` and `feature_psi_*` to Prometheus
4. If drift score exceeds threshold → calls Kubeflow API to trigger retraining pipeline

```yaml
# drift-detection/k8s/cronjob.yaml
schedule: "0 */6 * * *"   # every 6 hours
```

## Model Promotion Flow

```
MLflow run completes (eval metrics pass)
         │
         ▼
promote_model.py
  ├── mlflow.set_registered_model_alias("champion", version=N)
  └── GitHub API: update k8s/overlays/prod/kustomization.yaml
              with new model image/URI
         │
         ▼
GitHub Actions: model-promotion.yaml
  └── git commit + push → triggers ArgoCD sync
         │
         ▼
ArgoCD detects diff → applies to EKS
         │
         ▼
Argo Rollouts: canary 10% → 50% → 100%
  └── auto-rollback if error_rate > 1% or latency p95 > 2s
```

## Grafana Dashboards

| Dashboard | Panels |
|-----------|--------|
| **Training Pipeline** | Run duration, success rate, metric history per experiment |
| **Model Registry** | Active model versions, promotion history, champion vs challenger |
| **Inference Service** | Request rate, latency (p50/p95/p99), prediction distribution |
| **Drift Monitor** | PSI scores per feature, data drift trend, retrain trigger history |
