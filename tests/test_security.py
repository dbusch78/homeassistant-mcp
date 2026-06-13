#!/usr/bin/env python3
"""
Tests for the security middleware layer (security/rate-limiting-validation):
  - RateLimiter token bucket (burst, exhaustion, refill, isolation).

No live Home Assistant required: everything exercises the middleware layer
directly with a deterministic injected clock.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
from server import RateLimiter, RateLimitExceeded


# --- rate limiter ------------------------------------------------------------

class _Clock:
    """Manually advanced monotonic clock."""

    def __init__(self):
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float):
        self.t += seconds


def test_rate_limiter_allows_burst_then_blocks():
    clock = _Clock()
    rl = RateLimiter(rpm=60, burst=5, time_fn=clock)
    # Full burst of 5 succeeds with no time passing.
    for _ in range(5):
        rl.check("c1")
    # 6th in the same instant is rejected.
    try:
        rl.check("c1")
    except RateLimitExceeded as e:
        assert e.retry_after > 0
    else:
        raise AssertionError("6th call in one instant must be rate-limited")


def test_rate_limiter_refills_over_time():
    clock = _Clock()
    rl = RateLimiter(rpm=60, burst=5, time_fn=clock)   # 1 token/sec
    for _ in range(5):
        rl.check("c1")
    # Drained. One second later exactly one token is back.
    clock.advance(1.0)
    rl.check("c1")                       # ok
    try:
        rl.check("c1")
    except RateLimitExceeded:
        pass
    else:
        raise AssertionError("only one token should have refilled after 1s")


def test_rate_limiter_isolates_clients():
    clock = _Clock()
    rl = RateLimiter(rpm=60, burst=2, time_fn=clock)
    rl.check("a"); rl.check("a")         # drain a
    # b has its own full bucket.
    rl.check("b"); rl.check("b")
    for cid in ("a", "b"):
        try:
            rl.check(cid)
        except RateLimitExceeded:
            pass
        else:
            raise AssertionError(f"{cid} bucket should be drained")


def test_rate_limiter_rejects_bad_config():
    for bad in ((0, 5), (60, 0), (-1, 5)):
        try:
            RateLimiter(rpm=bad[0], burst=bad[1])
        except ValueError:
            pass
        else:
            raise AssertionError(f"RateLimiter{bad} should reject non-positive config")


if __name__ == "__main__":
    test_rate_limiter_allows_burst_then_blocks()
    test_rate_limiter_refills_over_time()
    test_rate_limiter_isolates_clients()
    test_rate_limiter_rejects_bad_config()
    print("OK: rate limiting tests pass")
