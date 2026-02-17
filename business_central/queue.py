"""Request queue with concurrency and rate limiting."""

import threading
import time
from collections import deque
from typing import Any, Callable


class RequestQueue:
    """A thread-safe request queue that enforces:

    - A maximum number of concurrent in-flight requests.
    - A maximum number of requests per time window (rate limiting).

    Args:
        max_concurrent: Maximum concurrent requests allowed.
        max_per_minute: Maximum requests allowed per 60-second window.
    """

    def __init__(self, max_concurrent: int = 5, max_per_minute: int = 50):
        self._max_concurrent = max_concurrent
        self._max_per_minute = max_per_minute
        self._semaphore = threading.Semaphore(max_concurrent)
        self._lock = threading.Lock()
        self._timestamps: deque[float] = deque()

    def _wait_for_rate_limit(self) -> None:
        """Block until we are within the rate-limit window."""
        while True:
            with self._lock:
                now = time.monotonic()
                # Remove timestamps older than 60 seconds.
                while self._timestamps and self._timestamps[0] <= now - 60:
                    self._timestamps.popleft()
                if len(self._timestamps) < self._max_per_minute:
                    self._timestamps.append(now)
                    return
                # Calculate how long to wait.
                wait = 60 - (now - self._timestamps[0])
            time.sleep(max(wait, 0.1))

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Submit a callable through the queue.

        Blocks until a concurrency slot is available and the rate limit
        allows a new request, then executes *fn*.

        Args:
            fn: The callable to execute.
            *args: Positional arguments for *fn*.
            **kwargs: Keyword arguments for *fn*.

        Returns:
            The return value of *fn*.
        """
        self._wait_for_rate_limit()
        self._semaphore.acquire()
        try:
            return fn(*args, **kwargs)
        finally:
            self._semaphore.release()
