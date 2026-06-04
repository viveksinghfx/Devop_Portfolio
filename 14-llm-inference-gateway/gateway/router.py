"""Per-model routing — maps model IDs to vLLM ClusterIP service URLs."""

from __future__ import annotations

import os

# Override individual routes via env vars for flexibility across envs
MODEL_ROUTES: dict[str, str] = {
    "llama3-8b":     os.getenv("VLLM_LLAMA3_8B_URL",     "http://vllm-llama3-8b-svc:8000"),
    "mistral-7b":    os.getenv("VLLM_MISTRAL_7B_URL",     "http://vllm-mistral-7b-svc:8000"),
    "codellama-13b": os.getenv("VLLM_CODELLAMA_13B_URL",  "http://vllm-codellama-13b-svc:8000"),
}


class UnsupportedModelError(ValueError):
    pass


def get_backend_url(model_id: str) -> str:
    """Return the ClusterIP service URL for the requested model."""
    url = MODEL_ROUTES.get(model_id)
    if url is None:
        available = ", ".join(MODEL_ROUTES.keys())
        raise UnsupportedModelError(
            f"Model '{model_id}' not found. Available models: {available}"
        )
    return url
