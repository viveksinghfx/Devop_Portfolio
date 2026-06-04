"""Prometheus instrumentation for the LLM gateway."""

from prometheus_client import Counter, Histogram, make_asgi_app
from fastapi import FastAPI

REQUEST_COUNT = Counter(
    "gateway_requests_total",
    "Total requests proxied by the gateway",
    ["model", "tier", "status"],
)

REQUEST_LATENCY = Histogram(
    "gateway_request_duration_seconds",
    "End-to-end request latency",
    ["model"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

RATE_LIMIT_HITS = Counter(
    "gateway_rate_limit_hits_total",
    "Requests rejected by the rate limiter",
    ["tier"],
)


def setup_metrics(app: FastAPI) -> None:
    """Mount /metrics endpoint (scraped by Prometheus)."""
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
