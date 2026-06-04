# Vivek Singh — DevOps & Platform Engineering Portfolio

**Platform & DevOps Engineer** | Kubernetes · Terraform · AWS · GitOps | Python Automation & CI/CD

📍 New Delhi, India · ✉️ viveksinghfx@gmail.com · 🌐 [viveksingh.tech](https://viveksingh.tech) · [LinkedIn](https://linkedin.com/in/vsdevop)

---

## Projects

### Infrastructure & Cloud

| # | Project | Stack | Architecture |
|---|---------|-------|---|
| 01 | [Jenkins HA on AWS](./01-jenkins-setup) | Terraform · Ansible · Packer · AWS ALB · ASG · EFS | ALB → ASG EC2s → EFS (shared home) |
| 03 | [Scalable Java App on AWS](./03-scalable-java-app) | Terraform · ALB · ASG · RDS · Ansible | ALB → ASG → RDS Multi-AZ |
| 05 | [AWS VPC Design & Automation](./05-aws-vpc-design-and-automation) | Terraform · AWS VPC | 3-tier VPC (public / private / DB subnets) |

### Observability

| # | Project | Stack | Architecture |
|---|---------|-------|---|
| 04 | [Prometheus Observability Stack](./04-prometheus-observability-stack) | Prometheus · Grafana · Loki · Alertmanager · Docker · Terraform | Scrape → TSDB → Grafana + Alertmanager → Slack |

### Kubernetes & GitOps

| # | Project | Stack | Architecture |
|---|---------|-------|---|
| 08 | [Fargate App Deployment](./08-fargate-app-deployment) | Terraform · EKS Fargate · Helm · ALB Ingress Controller | Helm → EKS Fargate (serverless) → ALB |
| 11 | [EKS GitOps with ArgoCD](./11-eks-gitops-argocd) | Terraform · EKS · ArgoCD · Kustomize · GitHub Actions · ECR | GitHub Actions (CI) → ECR → ArgoCD (CD) → EKS |

### Internal Developer Platform

| # | Project | Stack | Architecture |
|---|---------|-------|---|
| 12 | [Backstage IDP Templates](./12-backstage-idp-templates) | Backstage · GitHub Actions · ArgoCD · Kubernetes | Scaffolder → GitHub repo + ArgoCD app + CI pipeline |

### CI/CD & GitHub Actions

| # | Project | Stack | Architecture |
|---|---------|-------|---|
| 09 | [GitHub Actions OIDC → AWS](./09-github-action-oidc-aws) | GitHub Actions · AWS OIDC · IAM | OIDC JWT → STS AssumeRole → Temp credentials |

### Python Automation

| # | Project | Stack | Architecture |
|---|---------|-------|---|
| 13 | [Platform Automation Scripts](./13-python-platform-automation) | Python · boto3 · kubernetes-client · GitHub Actions | Cron jobs → AWS + K8s APIs → Slack alerts |

### LLMOps

| # | Project | Stack | Architecture |
|---|---------|-------|---|
| 14 | [LLM Inference Gateway & Serving Platform](./14-llm-inference-gateway) | FastAPI · vLLM · Kubernetes · Redis · Prometheus · Grafana · AWS EKS · Terraform | JWT auth → Redis rate limiter → model router → vLLM pods → HPA on queue depth |

### MLOps

| # | Project | Stack | Architecture |
|---|---------|-------|---|
| 15 | [End-to-End MLOps Pipeline on AWS](./15-mlops-pipeline-aws) | MLflow · Kubeflow Pipelines · ArgoCD · Argo Rollouts · Terraform · AWS S3 · RDS · EKS · Evidently AI | S3 data → KFP train → MLflow registry → GitOps promotion → EKS canary → drift-triggered retraining |

---

## Skills Demonstrated

- **Cloud**: AWS (EKS, VPC, IAM, S3, RDS, ECR, EFS, ASG, ALB)
- **IaC**: Terraform (reusable modules, remote state, workspaces)
- **Containers & Orchestration**: Kubernetes, Helm, Docker, EKS Fargate
- **GitOps**: ArgoCD (App of Apps), Kustomize (overlays)
- **CI/CD**: GitHub Actions (OIDC, matrix builds), Jenkins
- **Observability**: Prometheus, Grafana, Loki, Alertmanager
- **Config Management**: Ansible (roles, templates, dynamic inventories)
- **IDP**: Backstage software templates, self-service scaffolding
- **Automation**: Python (boto3, kubernetes client), Bash
