from collections import defaultdict, deque
from time import time

from fastapi import HTTPException, status


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._storage: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time()
        bucket = self._storage[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
            )
        bucket.append(now)
