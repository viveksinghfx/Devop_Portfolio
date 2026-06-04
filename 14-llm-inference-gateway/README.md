# LLM Inference Gateway & Serving Platform

Self-hosted, OpenAI-compatible LLM inference gateway on Kubernetes. vLLM serves models behind a FastAPI gateway with JWT auth, rate limiting, per-model routing, and full Prometheus/Grafana observability. Deployed on AWS EKS via Terraform.

## Architecture

```
  Client (curl / app)
       │  POST /v1/chat/completions
       │  Authorization: Bearer <JWT>
       ▼
  AWS API Gateway (TLS termination)
       │
       ▼
  FastAPI Gateway  (gateway/)
  ┌─────────────────────────────────────────────────┐
  │  1. JWT validation (RS256)                       │
  │  2. Rate limiting   ──► Redis (token bucket)     │
  │  3. Model router    ──► selects vLLM backend     │
  │  4. Request proxy   ──► vLLM pod via ClusterIP   │
  └─────────────────────────────────────────────────┘
       │
       ├──► vLLM (Llama-3-8B)   — GPU node pool A
       ├──► vLLM (Mistral-7B)   — GPU node pool A
       └──► vLLM (CodeLlama-13B)— GPU node pool B
                 │
                 ▼
         Prometheus metrics
         ┌──────────────────────┐
         │ token_throughput      │
         │ time_to_first_token   │
         │ queue_depth           │
         │ p95 / p99 latency     │
         └──────────────────────┘
                 │
                 ▼
           Grafana dashboards + Alertmanager
```

## Stack

| Layer | Tool |
|-------|------|
| **Inference engine** | [vLLM](https://github.com/vllm-project/vllm) |
| **Gateway / API** | FastAPI + Pydantic |
| **Auth** | JWT (RS256) via PyJWT |
| **Rate limiting** | Redis (token-bucket algorithm) |
| **Orchestration** | Kubernetes (AWS EKS) |
| **Autoscaling** | HPA on `vllm_queue_depth` custom metric |
| **Observability** | Prometheus + Grafana + Alertmanager |
| **IaC** | Terraform (EKS, VPC, IAM, node groups) |
| **CI/CD** | GitHub Actions → ECR → ArgoCD |

## Key Results

- **p95 latency reduced by 40%** through vLLM continuous batching config and HPA tuning
- Sub-second cold-start via pre-warmed model weights on persistent node storage
- JWT + Redis rate limiting prevents quota abuse per API key
- Full OpenAI SDK compatibility — drop-in replacement for `openai` Python client

## Quick Start

### 1. Provision infrastructure

```bash
cd terraform
terraform init
terraform apply -var-file="envs/prod.tfvars"
```

### 2. Deploy to Kubernetes

```bash
# Install via ArgoCD app-of-apps
kubectl apply -f argocd/app-of-apps.yaml

# Or apply directly
kubectl apply -k k8s/overlays/prod
```

### 3. Generate a JWT token (dev)

```bash
python gateway/scripts/generate_token.py \
  --model llama3-8b \
  --tier standard \
  --ttl 86400
```

### 4. Test the gateway

```bash
curl https://<gateway-url>/v1/chat/completions \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3-8b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 256
  }'
```

## Repository Structure

```
14-llm-inference-gateway/
├── gateway/                  # FastAPI gateway service
│   ├── main.py               # App entrypoint, routes
│   ├── auth.py               # JWT validation (RS256)
│   ├── router.py             # Per-model routing logic
│   ├── rate_limiter.py       # Redis token-bucket limiter
│   ├── metrics.py            # Prometheus instrumentation
│   ├── Dockerfile
│   └── requirements.txt
├── k8s/
│   ├── base/                 # Kustomize base manifests
│   │   ├── gateway-deployment.yaml
│   │   ├── vllm-deployment.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── hpa.yaml          # Custom metric HPA
│   │   └── services.yaml
│   └── overlays/
│       ├── dev/
│       ├── staging/
│       └── prod/
├── monitoring/
│   ├── dashboards/
│   │   └── llm-inference.json   # Grafana dashboard JSON
│   ├── alerts/
│   │   └── llm-alerts.yaml      # Alertmanager rules
│   └── prometheus-rules.yaml
├── terraform/
│   ├── modules/
│   │   ├── eks/
│   │   └── gpu-nodegroup/
│   └── envs/
│       ├── dev.tfvars
│       └── prod.tfvars
└── docs/
    ├── architecture.md
    ├── rate-limiting.md
    └── model-routing.md
```

## Observability

Grafana dashboard (`monitoring/dashboards/llm-inference.json`) tracks:

| Metric | Description |
|--------|-------------|
| `vllm_token_throughput` | Tokens/sec per model |
| `vllm_time_to_first_token_seconds` | TTFT histogram (p50/p95/p99) |
| `vllm_queue_depth` | Pending requests per model pod |
| `gateway_request_duration_seconds` | End-to-end latency |
| `gateway_rate_limit_hits_total` | Throttled requests by key |

HPA scales vLLM pods when `vllm_queue_depth > 5` (configurable).

## Model Routing Logic

The gateway reads the `model` field in the request and routes to the appropriate vLLM `ClusterIP` service:

```python
MODEL_ROUTES = {
    "llama3-8b":     "http://vllm-llama3-8b-svc:8000",
    "mistral-7b":    "http://vllm-mistral-7b-svc:8000",
    "codellama-13b": "http://vllm-codellama-13b-svc:8000",
}
```

Unknown model names return HTTP 422 with a list of available models.

## Rate Limiting

Redis token-bucket per JWT `sub` claim:

| Tier | Requests/min | Tokens/day |
|------|-------------|------------|
| `free` | 10 | 50,000 |
| `standard` | 60 | 500,000 |
| `premium` | 300 | unlimited |

Rate limit headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`) are returned on every response.
