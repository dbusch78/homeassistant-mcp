#!/usr/bin/env python3
"""
Tests for the security middleware layer (security/rate-limiting-validation):
  - RateLimiter token bucket (burst, exhaustion, refill, isolation),
  - validate_tool_input grammar + payload caps (rejects injection, accepts valid).

No live Home Assistant required: everything exercises the middleware layer
directly with a deterministic injected clock.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
from server import (
    RateLimiter,
    RateLimitExceeded,
    ToolInputError,
    validate_tool_input,
)


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


# --- input validation: rejects injection / malformed -------------------------

def _expect_reject(name, args, field=None):
    try:
        validate_tool_input(name, args)
    except ToolInputError as e:
        if field is not None:
            assert e.field == field, f"{name}: expected field {field}, got {e.field}"
    else:
        raise AssertionError(f"{name} {args} should have been rejected")


def test_validation_rejects_path_injection():
    # domain/service/event_type are interpolated into the REST path.
    _expect_reject("call_service", {"domain": "../../admin", "service": "x"}, "domain")
    _expect_reject("call_service", {"domain": "light", "service": "turn_on/../"}, "service")
    _expect_reject("fire_event", {"event_type": "a/b"}, "event_type")
    # config ids must not carry path separators.
    _expect_reject("update_automation", {"automation_id": "../secrets"}, "automation_id")
    _expect_reject("delete_script", {"script_id": "a/b"}, "script_id")


def test_validation_rejects_bad_entity_id():
    _expect_reject("get_entity_state", {"entity_id": "no_dot_here"}, "entity_id")
    _expect_reject("get_entity_state", {"entity_id": "light./etc/passwd"}, "entity_id")
    _expect_reject("set_state", {"entity_id": "Light.Kitchen", "state": "on"}, "entity_id")
    _expect_reject("delete_state", {"entity_id": "../x"}, "entity_id")


def test_validation_rejects_missing_required():
    _expect_reject("get_entity_state", {}, "entity_id")
    _expect_reject("call_service", {"domain": "light"}, "service")


def test_validation_rejects_payload_abuse():
    obj = {}
    cur = obj
    for _ in range(server.MAX_PAYLOAD_DEPTH + 2):
        cur["k"] = {}
        cur = cur["k"]
    _expect_reject("call_service",
                   {"domain": "light", "service": "turn_on", "service_data": obj},
                   "service_data")
    _expect_reject("set_state",
                   {"entity_id": "sensor.x", "state": "ok", "attributes": {"a": "y\x00z"}},
                   "attributes")
    _expect_reject("render_template",
                   {"template": "x" * (server.MAX_TEMPLATE_LEN + 1)},
                   "template")
    _expect_reject("set_state",
                   {"entity_id": "sensor.x", "state": "n\x00ul"},
                   "state")


# --- input validation: accepts valid calls (no false rejects) ----------------

def _expect_ok(name, args):
    validate_tool_input(name, args)   # must not raise


def test_validation_accepts_valid_calls():
    _expect_ok("call_service", {"domain": "light", "service": "turn_on",
                                "entity_id": "light.kitchen"})
    # entity_id as a list target is valid (goes into the body, not a path).
    _expect_ok("call_service", {"domain": "light", "service": "turn_on",
                                "entity_id": ["light.a", "light.b"]})
    _expect_ok("get_entity_state", {"entity_id": "binary_sensor.front_door"})
    _expect_ok("set_state", {"entity_id": "sensor.x", "state": "42",
                             "attributes": {"unit": "W"}})
    _expect_ok("fire_event", {"event_type": "my_custom_event", "event_data": {"a": 1}})
    _expect_ok("render_template", {"template": "{{ states('sensor.x') }}"})
    # toggle uses an entity_id; update uses a numeric config id.
    _expect_ok("toggle_automation", {"automation_id": "automation.morning"})
    _expect_ok("update_automation", {"automation_id": "1718294827361",
                                     "config": {"alias": "x", "action": []}})
    _expect_ok("delete_automation", {"automation_id": "1718294827361"})


def test_validation_ignores_unlisted_tools():
    # A read-only tool not in the spec table is never constrained.
    validate_tool_input("get_system_info", {"anything": "../etc", "x": "\x00"})
    validate_tool_input("search_entities", {"query": "kitchen/../"})


# --- exposure gate whitespace fix --------------------------------------------

def test_exposure_gate_rejects_whitespace_token():
    os.environ["MCP_AUTH_TOKEN"] = "   "          # effectively empty
    os.environ["MCP_ALLOWED_HOSTS"] = "172.21.30.5:8787"
    try:
        server._enforce_exposure_gate("172.21.30.5")
    except SystemExit as e:
        assert "MCP_AUTH_TOKEN" in str(e), str(e)
        assert "MCP_ALLOWED_HOSTS" not in str(e), str(e)
    else:
        raise AssertionError("whitespace-only MCP_AUTH_TOKEN must not satisfy the gate")
    finally:
        os.environ.pop("MCP_AUTH_TOKEN", None)
        os.environ.pop("MCP_ALLOWED_HOSTS", None)


if __name__ == "__main__":
    test_rate_limiter_allows_burst_then_blocks()
    test_rate_limiter_refills_over_time()
    test_rate_limiter_isolates_clients()
    test_rate_limiter_rejects_bad_config()
    test_validation_rejects_path_injection()
    test_validation_rejects_bad_entity_id()
    test_validation_rejects_missing_required()
    test_validation_rejects_payload_abuse()
    test_validation_accepts_valid_calls()
    test_validation_ignores_unlisted_tools()
    test_exposure_gate_rejects_whitespace_token()
    print("OK: rate limiting + input validation + exposure-gate tests pass")
