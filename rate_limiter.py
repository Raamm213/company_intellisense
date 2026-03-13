import asyncio
import time


class RateLimiter:
    """
    Simple async rate limiter to avoid hitting free-tier API limits.
    
    Usage:
        limiter = RateLimiter(min_interval=4.0)  # 4 seconds between calls = 15 RPM
        await limiter.wait()
        response = await llm.ainvoke(prompt)
    """

    def __init__(self, min_interval: float = 4.0):
        """
        Args:
            min_interval: Minimum seconds between consecutive API calls.
                          Default 4.0 → max 15 requests/minute (safe for Gemini free tier).
        """
        self.min_interval = min_interval
        self._last_call_time: float = 0.0
        self._lock = asyncio.Lock()

    async def wait(self):
        """Wait until enough time has passed since the last call."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call_time
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                print(f"  ⏳ Rate limiter: waiting {sleep_time:.1f}s before next API call...")
                await asyncio.sleep(sleep_time)
            self._last_call_time = time.monotonic()
