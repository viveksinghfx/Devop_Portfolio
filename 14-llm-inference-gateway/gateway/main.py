"""
LLM Inference Gateway — FastAPI entrypoint
OpenAI-compatible API surface backed by vLLM pods on Kubernetes.
"""

from __future__ import annotations

import time
import httpx
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import verify_jwt, JWTClaims
from router import get_backend_url, UnsupportedModelError
from rate_limiter import RateLimiter, RateLimitExceeded
from metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    RATE_LIMIT_HITS,
    setup_metrics,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rate_limiter: RateLimiter | None = None
http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rate_limiter, http_client
    rate_limiter = RateLimiter()
    await rate_limiter.connect()
    http_client = httpx.AsyncClient(timeout=120.0)
    logger.info("Gateway started — Redis and HTTP client ready")
    yield
    await rate_limiter.close()
    await http_client.aclose()
    logger.info("Gateway shutdown complete")


app = FastAPI(
    title="LLM Inference Gateway",
    description="OpenAI-compatible self-hosted LLM gateway with JWT auth and rate limiting",
    version="1.0.0",
    lifespan=lifespan,
)
setup_metrics(app)


# ── Request / Response models ────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[Message]
    max_tokens: int = Field(default=512, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = False


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/healthz")
async def health():
    return {"status": "ok"}


@app.get("/v1/models")
async def list_models(claims: JWTClaims = Depends(verify_jwt)):
    from router import MODEL_ROUTES
    return {
        "object": "list",
        "data": [
            {"id": model_id, "object": "model", "owned_by": "self-hosted"}
            for model_id in MODEL_ROUTES
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
    claims: JWTClaims = Depends(verify_jwt),
):
    start = time.perf_counter()
    subject = claims.sub
    tier = claims.tier

    # Rate limiting
    try:
        remaining = await rate_limiter.check(subject, tier)
    except RateLimitExceeded as exc:
        RATE_LIMIT_HITS.labels(tier=tier).inc()
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(exc.reset_at),
                "Retry-After": str(exc.retry_after),
            },
        )

    # Model routing
    try:
        backend_url = get_backend_url(payload.model)
    except UnsupportedModelError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Proxy to vLLM
    target = f"{backend_url}/v1/chat/completions"
    body = payload.model_dump()

    try:
        if payload.stream:
            return await _stream_response(target, body, remaining, start, tier)
        else:
            resp = await http_client.post(target, json=body)
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.RequestError as exc:
        logger.error("Backend unreachable: %s", exc)
        raise HTTPException(status_code=503, detail="Upstream model unavailable")

    elapsed = time.perf_counter() - start
    REQUEST_COUNT.labels(model=payload.model, tier=tier, status="200").inc()
    REQUEST_LATENCY.labels(model=payload.model).observe(elapsed)

    return resp.json()


async def _stream_response(
    target: str,
    body: dict[str, Any],
    remaining: int,
    start: float,
    tier: str,
) -> StreamingResponse:
    model = body["model"]

    async def generator():
        async with http_client.stream("POST", target, json=body) as resp:
            async for chunk in resp.aiter_text():
                yield chunk

        elapsed = time.perf_counter() - start
        REQUEST_COUNT.labels(model=model, tier=tier, status="200").inc()
        REQUEST_LATENCY.labels(model=model).observe(elapsed)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"X-RateLimit-Remaining": str(remaining)},
    )
