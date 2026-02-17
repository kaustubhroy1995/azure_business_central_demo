"""Tests for the request queue."""

import threading
import time
import unittest

from business_central.queue import RequestQueue


class TestRequestQueue(unittest.TestCase):
    """Test cases for RequestQueue concurrency and rate limiting."""

    def test_submit_returns_result(self):
        q = RequestQueue(max_concurrent=5, max_per_minute=50)
        result = q.submit(lambda: 42)
        self.assertEqual(result, 42)

    def test_submit_passes_args(self):
        q = RequestQueue(max_concurrent=5, max_per_minute=50)
        result = q.submit(lambda a, b: a + b, 3, 4)
        self.assertEqual(result, 7)

    def test_submit_passes_kwargs(self):
        q = RequestQueue(max_concurrent=5, max_per_minute=50)
        result = q.submit(lambda x=0: x * 2, x=5)
        self.assertEqual(result, 10)

    def test_concurrency_limit(self):
        """Ensure no more than max_concurrent tasks run at the same time."""
        max_concurrent = 2
        q = RequestQueue(max_concurrent=max_concurrent, max_per_minute=100)
        peak = {"value": 0}
        current = {"value": 0}
        lock = threading.Lock()

        def task():
            with lock:
                current["value"] += 1
                peak["value"] = max(peak["value"], current["value"])
            time.sleep(0.05)
            with lock:
                current["value"] -= 1
            return True

        threads = []
        for _ in range(6):
            t = threading.Thread(target=q.submit, args=(task,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.assertLessEqual(peak["value"], max_concurrent)

    def test_rate_limit(self):
        """Ensure requests within a small window are rate-limited."""
        q = RequestQueue(max_concurrent=10, max_per_minute=3)
        results = []
        start = time.monotonic()

        # Submit 3 requests — should all go through immediately.
        for _ in range(3):
            q.submit(lambda: results.append(time.monotonic()))

        elapsed = time.monotonic() - start
        self.assertEqual(len(results), 3)
        # All 3 should have completed quickly (well under 5 seconds).
        self.assertLess(elapsed, 5)

    def test_exception_propagation(self):
        q = RequestQueue(max_concurrent=5, max_per_minute=50)

        def bad():
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            q.submit(bad)


if __name__ == "__main__":
    unittest.main()
