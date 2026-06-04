"""Redis token-bucket rate limiter."""

from __future__ import annotations

import os
import time

import redis.asyncio as aioredis

TIER_LIMITS: dict[str, dict[str, int]] = {
    "free":     {"rpm": 10,  "daily_tokens": 50_000},
    "standard": {"rpm": 60,  "daily_tokens": 500_000},
    "premium":  {"rpm": 300, "daily_tokens": -1},  # -1 = unlimited
}

_REDIS_URL = os.getenv("REDIS_URL", "redis://redis-svc:6379")


class RateLimitExceeded(Exception):
    def __init__(self, reset_at: int, retry_after: int):
        self.reset_at = reset_at
        self.retry_after = retry_after


class RateLimiter:
    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def connect(self):
        self._redis = await aioredis.from_url(_REDIS_URL, decode_responses=True)

    async def close(self):
        if self._redis:
            await self._redis.aclose()

    async def check(self, subject: str, tier: str) -> int:
        """
        Sliding-window RPM check using Redis INCR + EXPIRE.
        Returns remaining requests in this window.
        Raises RateLimitExceeded if over limit.
        """
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        rpm = limits["rpm"]

        now = int(time.time())
        window_key = f"rl:{subject}:{now // 60}"  # 1-minute window

        count = await self._redis.incr(window_key)
        if count == 1:
            await self._redis.expire(window_key, 60)

        if count > rpm:
            reset_at = (now // 60 + 1) * 60
            raise RateLimitExceeded(reset_at=reset_at, retry_after=reset_at - now)

        return rpm - count
