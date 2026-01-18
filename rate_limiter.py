"""Adaptive and Token Bucket rate limiting for advanced crawling.

- RateLimiter:    adaptive, per-request jitter, exponential backoff (legacy, stealth, anti-ban)
- TokenBucketLimiter: concurrent global RPS strict throttler (for parallel god mode crawling)
"""

import asyncio
import time
import random
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ----------------------------
# (1) Adaptive + Jitter + Backoff
# ----------------------------
class RateLimiter:
    """
    Adaptive rate limiter with exponential backoff and jitter.

    Features:
    - Configurable requests per second (RPS)
    - Adaptive backoff/jitter for stealth and anti-ban crawling
    - Exponential backoff on error/429/5xx
    - Success shortens wait on streak
    """
    def __init__(self, requests_per_second: float = 2.0, adaptive: bool = True):
        self.requests_per_second = requests_per_second
        self.adaptive = adaptive
        self.min_interval = 1.0 / requests_per_second
        self.current_interval = self.min_interval
        self.last_request_time: Optional[float] = None
        self.error_count = 0
        self.success_count = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request (throttled)."""
        async with self._lock:
            now = time.time()
            if self.last_request_time is not None:
                elapsed = now - self.last_request_time
                wait_time = self.current_interval - elapsed
                if wait_time > 0:
                    jitter = wait_time * random.uniform(-0.1, 0.1)
                    await asyncio.sleep(wait_time + jitter)
            self.last_request_time = time.time()
            logger.debug(f"Rate limit acquired (interval: {self.current_interval:.3f}s)")

    def report_success(self) -> None:
        """Call this after a successful request to adaptively increase rate (if many in a row)."""
        self.success_count += 1
        self.error_count = 0
        if self.adaptive and self.success_count >= 10:
            # Reduce wait if successful streak
            self.current_interval = max(self.min_interval, self.current_interval * 0.9)
            self.success_count = 0
            logger.debug(f"Rate limit decreased to {self.current_interval:.3f}s")

    def report_error(self, status_code: Optional[int] = None) -> None:
        """Call this after a failed request (HTTP 429/5xx or similar), and adaptive backoff triggers."""
        self.error_count += 1
        self.success_count = 0
        if status_code == 429 or (status_code and 500 <= status_code < 600):
            backoff_factor = 2 ** min(self.error_count, 5)  # Cap backoff
            self.current_interval = min(60.0, self.min_interval * backoff_factor)
            logger.warning(f"Rate limit interval increased to {self.current_interval:.3f}s on errors: {self.error_count}")

    def reset(self) -> None:
        """Reset the rate limiter to its initial minimum state."""
        self.current_interval = self.min_interval
        self.error_count = 0
        self.success_count = 0
        logger.info("Rate limiter reset")

# ----------------------------
# (2) True Token Bucket Limiter (Global strict RPS cap for async crawling)
# ----------------------------
class TokenBucketLimiter:
    """
    Asyncio token bucket rate limiter.

    Strictly enforces up to `rate` tokens (requests) per `period` seconds.
    Use this for multi-worker, parallel-safe global throttling.

        tb = TokenBucketLimiter(rate=5)  # 5 requests/second
        await tb.acquire()

    Safe for many concurrent awaits.
    """
    def __init__(self, rate: int, period: int = 1):
        self.capacity = rate
        self.tokens = rate
        self.rate = rate
        self.period = period
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.updated_at
            # Refill tokens
            if elapsed > 0:
                refill = int(elapsed * self.rate // self.period)
                self.tokens = min(self.capacity, self.tokens + refill)
                if refill > 0:
                    self.updated_at = now
            while self.tokens < 1:
                need = 1 - self.tokens
                await asyncio.sleep(self.period / self.rate * need)
                now = time.monotonic()
                elapsed = now - self.updated_at
                refill = int(elapsed * self.rate // self.period)
                self.tokens = min(self.capacity, self.tokens + refill)
                if refill > 0:
                    self.updated_at = now
            self.tokens -= 1
            logger.debug(f"TokenBucketLimiter used: {self.tokens}/{self.capacity} tokens left")

