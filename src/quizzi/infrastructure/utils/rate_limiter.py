import asyncio
import time
from dataclasses import dataclass


@dataclass
class UserBucket:
    tokens: float
    last_updated: float


class RateLimiter:
    def __init__(self, rate: int, period: int):
        self.rate = rate  
        self.period = period 
        self.fill_rate = rate / period
        self.buckets: dict[int, UserBucket] = {}
        self._lock = asyncio.Lock()

    async def check(self, user_id: int) -> tuple[bool, float]:
        async with self._lock:
            now = time.time()
            
            if user_id not in self.buckets:
                self.buckets[user_id] = UserBucket(
                    tokens=self.rate - 1,
                    last_updated=now
                )
                return True, 0.0
            
            bucket = self.buckets[user_id]
            
            elapsed = now - bucket.last_updated
            added_tokens = elapsed * self.fill_rate
            bucket.tokens = min(self.rate, bucket.tokens + added_tokens)
            bucket.last_updated = now
            
            if bucket.tokens >= 1:
                bucket.tokens -= 1
                return True, 0.0
            else:
                wait_time = (1 - bucket.tokens) / self.fill_rate
                return False, wait_time

    async def cleanup(self) -> None:
        async with self._lock:
            full_buckets = [
                user_id for user_id, bucket in self.buckets.items()
                if bucket.tokens >= self.rate
            ]
            for user_id in full_buckets:
                del self.buckets[user_id]


class PasswordRateLimiter(RateLimiter):
    def __init__(self):
        super().__init__(rate=5, period=3600)
