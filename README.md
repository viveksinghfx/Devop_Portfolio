<div align="center">

```
██╗   ██╗██╗██╗   ██╗███████╗██╗  ██╗    ███████╗██╗███╗   ██╗ ██████╗ ██╗  ██╗
██║   ██║██║██║   ██║██╔════╝██║ ██╔╝    ██╔════╝██║████╗  ██║██╔════╝ ██║  ██║
██║   ██║██║██║   ██║█████╗  █████╔╝     ███████╗██║██╔██╗ ██║██║  ███╗███████║
╚██╗ ██╔╝██║╚██╗ ██╔╝██╔══╝  ██╔═██╗     ╚════██║██║██║╚██╗██║██║   ██║██╔══██║
 ╚████╔╝ ██║ ╚████╔╝ ███████╗██║  ██╗    ███████║██║██║ ╚████║╚██████╔╝██║  ██║
  ╚═══╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝
```

### DevOps · MLOps · LLMOps Engineer

**Building production-grade cloud-native infrastructure — from bare Terraform to LLM serving platforms**

[![Location](https://img.shields.io/badge/📍_New_Delhi-India-orange?style=flat-square)](https://maps.google.com/?q=New+Delhi)
[![Email](https://img.shields.io/badge/✉️_viveksinghfx@gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white)](mailto:viveksinghfx@gmail.com)
[![Website](https://img.shields.io/badge/🌐_viveksingh.tech-0A0A0A?style=flat-square)](https://viveksingh.tech)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-vsdevop-0077B5?style=flat-square&logo=linkedin)](https://linkedin.com/in/vsdevop)
[![GitHub](https://img.shields.io/badge/GitHub-viveksinghfx-181717?style=flat-square&logo=github)](https://github.com/viveksinghfx)

</div>

---

## About

3+ years building and operating cloud-native infrastructure on AWS — across DevOps, MLOps, and LLMOps. I've shipped everything from Jenkins HA clusters and GitOps deployment platforms to self-hosted LLM inference gateways and automated ML retraining pipelines. Background in Python automation from high-volume VFX production (Disney+, Transformers, Ant-Man).

I care about **zero-downtime deploys**, **full observability**, and systems that run themselves.

---

## Tech Stack

<table>
<tr>
<td valign="top" width="33%">

**Cloud & IaC**
```
AWS        EKS · VPC · IAM · S3
           RDS · ECR · EFS · ALB
Terraform  Modules · Workspaces
           Remote State
Ansible    Roles · Packer AMIs
```

</td>
<td valign="top" width="33%">

**Containers & GitOps**
```
Kubernetes  EKS · Fargate · Helm
Docker      Multi-stage builds
ArgoCD      App-of-Apps · Rollouts
Kustomize   Overlay environments
GitHub Actions  OIDC · Matrix builds
```

</td>
<td valign="top" width="33%">

**ML / LLM Ops**
```
MLflow      Tracking · Registry
Kubeflow    Pipelines v2
vLLM        GPU inference
FastAPI     OpenAI-compatible API
Evidently   Drift detection
```

</td>
</tr>
<tr>
<td valign="top">

**Observability**
```
Prometheus  Custom metrics · HPA
Grafana     Dashboards · Alerting
Loki        Log aggregation
Alertmanager  PagerDuty · Slack
```

</td>
<td valign="top">

**Languages**
```
Python   boto3 · asyncio · Pydantic
Bash     Automation scripts
HCL      Terraform modules
YAML     K8s · CI/CD manifests
```

</td>
<td valign="top">

**Platforms**
```
Backstage  IDP · Self-service
Redis      Rate limiting · Cache
Jenkins    HA on AWS ASG+EFS
Next.js    Frontend deployment
```

</td>
</tr>
</table>

---

## Projects

### 🏗️ Infrastructure & Cloud

| | Project | Highlights |
|---|---|---|
| **01** | [**Jenkins HA on AWS**](./01-jenkins-setup) | Terraform + Ansible + Packer · ALB → ASG EC2s → EFS shared home · Zero-downtime controller restarts |
| **03** | [**Scalable Java App on AWS**](./03-scalable-java-app) | ALB → ASG → RDS Multi-AZ · Ansible provisioning · Auto-scaling on CPU |
| **05** | [**AWS VPC Design & Automation**](./05-aws-vpc-design-and-automation) | 3-tier VPC (public / private / DB subnets) · NAT gateways · Security group layering |

---

### 📊 Observability

| | Project | Highlights |
|---|---|---|
| **04** | [**Prometheus Observability Stack**](./04-prometheus-observability-stack) | Prometheus + Grafana + Loki + Alertmanager · Docker + Terraform deploy · Slack alerting |

---

### ☸️ Kubernetes & GitOps

| | Project | Highlights |
|---|---|---|
| **08** | [**Fargate App Deployment**](./08-fargate-app-deployment) | Serverless EKS Fargate · Helm chart · ALB Ingress Controller · No node management |
| **11** | [**EKS GitOps with ArgoCD**](./11-eks-gitops-argocd) | GitHub Actions CI → ECR → ArgoCD CD → EKS · Full deploy under 8 min · Drift detection |

---

### 🤖 MLOps

| | Project | Highlights |
|---|---|---|
| **15** | [**End-to-End MLOps Pipeline on AWS**](./15-mlops-pipeline-aws) | Kubeflow Pipelines v2 · MLflow registry · ArgoCD GitOps promotion · Argo Rollouts canary · Evidently drift detection → auto-retraining · **Model in prod < 15 min from merge** |

```
S3 (versioned data)
    └─► Kubeflow Pipeline: ingest → features → train → evaluate (F1 gate) → MLflow register
                                                                               │
                                                                     ArgoCD GitOps commit
                                                                               │
                                                               EKS canary rollout (10% → 100%)
                                                                               │
                                                           Evidently drift CronJob (every 6h)
                                                               └─► auto-trigger retraining
```

---

### 🧠 LLMOps

| | Project | Highlights |
|---|---|---|
| **14** | [**LLM Inference Gateway & Serving Platform**](./14-llm-inference-gateway) | vLLM on EKS · OpenAI-compatible FastAPI · JWT (RS256) auth · Redis rate limiting · Custom metric HPA · **p95 latency reduced 40%** |

```
Client
  └─► FastAPI Gateway
        ├─► JWT validation (RS256)
        ├─► Redis token-bucket rate limiter (free / standard / premium)
        └─► Model router
              ├─► vLLM (Llama-3-8B)    GPU node pool
              ├─► vLLM (Mistral-7B)    GPU node pool
              └─► vLLM (CodeLlama-13B) GPU node pool
                        │
                  Prometheus: token_throughput · TTFT · queue_depth
                  HPA: scale on vllm_queue_depth > 5
```

---

### 🛠️ Developer Platform & Automation

| | Project | Highlights |
|---|---|---|
| **09** | [**GitHub Actions OIDC → AWS**](./09-github-action-oidc-aws) | No long-lived credentials · OIDC JWT → STS AssumeRole → scoped IAM role |
| **12** | [**Backstage IDP Templates**](./12-backstage-idp-templates) | Self-service service scaffolding · Auto-creates GitHub repo + ArgoCD app + CI pipeline |
| **13** | [**Platform Automation Scripts**](./13-python-platform-automation) | boto3 + kubernetes-client · Stale resource cleanup · ECR image GC · K8s health reports → Slack |

---

## Key Results

```
🚀  Full deploy cycle under 8 min       EKS GitOps platform (zero manual steps)
⚡  p95 LLM latency reduced 40%         vLLM batching + HPA tuning
🤖  Model to production < 15 min        MLOps pipeline (merge → EKS canary)
🔄  Auto drift-triggered retraining     Evidently AI + Kubeflow Pipelines
🔐  Zero long-lived AWS credentials     GitHub Actions OIDC across all CI/CD
```

---

## Work Experience

**Neevya Therapy** *(2024 – Present)* — **DevOps Engineer (Freelance)**
> Sole engineer for an AI therapy chatbot platform. Built entire AWS infrastructure (EKS, VPC, IAM, RDS, S3) from scratch with Terraform. CI/CD via GitHub Actions + Argo Rollouts canary. Full Prometheus/Grafana observability stack.

**Harikatha Studio** *(11/2024 – 01/2026)* — **Pipeline & Automation Engineer**
> Houdini → Unreal Engine bridge. FastAPI microservices exposing studio tooling as REST APIs. Procedural asset generation workflows.

**Technicolor Animation Productions** *(07/2023 – 06/2024)* — **FX Artist TD**
> Python automation across high-volume VFX pipelines. FastAPI pipeline APIs. Productions: *Crater (Disney+)*, *Transformers: Rise of the Beasts*, *Ant-Man and the Wasp: Quantumania*.

---

<div align="center">

*All projects include Terraform IaC, Kubernetes manifests, CI/CD pipelines, and observability config.*
*Each folder is self-contained with a README covering architecture, quick-start, and design decisions.*

**[viveksingh.tech](https://viveksingh.tech) · [viveksinghfx@gmail.com](mailto:viveksinghfx@gmail.com)**

</div>
