"""Adaptive rate limiting with exponential backoff for StealthCrawler v17."""

import asyncio
import time
import random
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Adaptive rate limiter with exponential backoff and jitter.
    
    Features:
    - Configurable requests per second
    - Adaptive rate limiting based on server health
    - Exponential backoff on errors
    - Jitter to prevent thundering herd
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
        """Acquire permission to make a request."""
        async with self._lock:
            now = time.time()
            
            if self.last_request_time is not None:
                elapsed = now - self.last_request_time
                wait_time = self.current_interval - elapsed
                
                if wait_time > 0:
                    # Add jitter (±10%)
                    jitter = wait_time * random.uniform(-0.1, 0.1)
                    await asyncio.sleep(wait_time + jitter)
            
            self.last_request_time = time.time()
            logger.debug(f"Rate limit acquired (interval: {self.current_interval:.3f}s)")
    
    def report_success(self) -> None:
        """Report a successful request."""
        self.success_count += 1
        self.error_count = 0
        
        if self.adaptive and self.success_count >= 10:
            # Gradually increase rate on sustained success
            self.current_interval = max(self.min_interval, self.current_interval * 0.9)
            self.success_count = 0
            logger.debug(f"Rate limit decreased to {self.current_interval:.3f}s")
    
    def report_error(self, status_code: Optional[int] = None) -> None:
        """Report a failed request and apply backoff."""
        self.error_count += 1
        self.success_count = 0
        
        # Check if rate limited (429) or server error (5xx)
        if status_code == 429 or (status_code and 500 <= status_code < 600):
            # Apply exponential backoff
            backoff_factor = 2 ** min(self.error_count, 5)  # Cap at 2^5 = 32x
            self.current_interval = min(60.0, self.min_interval * backoff_factor)
            logger.warning(f"Rate limit increased to {self.current_interval:.3f}s (errors: {self.error_count})")
    
    def reset(self) -> None:
        """Reset the rate limiter to initial state."""
        self.current_interval = self.min_interval
        self.error_count = 0
        self.success_count = 0
        logger.info("Rate limiter reset")
