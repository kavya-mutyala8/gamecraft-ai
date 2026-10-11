"""Tiny in-memory sliding-window limiter.

Per-process only: behind multiple workers/instances use a shared store (e.g. Redis)
or an API gateway instead.
"""

import math
import time
from collections import defaultdict, deque

from fastapi import Request

from app.errors import RateLimitedError


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        if self.limit <= 0:
            return
        now = time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise RateLimitedError(retry_after=max(1, math.ceil(self.window - (now - q[0]))))
        q.append(now)


def enforce_rate_limit(request: Request) -> None:
    """FastAPI dependency for generation routes."""
    client = request.client.host if request.client else "unknown"
    request.app.state.limiter.check(client)
