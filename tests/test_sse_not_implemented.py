#!/usr/bin/env python3
"""
Test that subscribe_events and get_sse_stats report not-implemented.

Upstream, subscribe_events claimed a successful subscription that never emitted
events, and get_sse_stats returned fabricated stats. Under stdio there is no
channel to push events to the client, so both now return a structured
not_implemented response. Runs without a live Home Assistant.
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import handle_call_tool


def _call(tool: str, args: dict):
    async def _run():
        with patch("server.HA_TOKEN", "test-token"), \
             patch("server.HomeAssistantClient") as MockClient:
            MockClient.return_value.__aenter__.return_value = AsyncMock()
            result = await handle_call_tool(tool, args)
            return json.loads(result[0].text)

    return asyncio.run(_run())


def test_subscribe_events_not_implemented():
    payload = _call("subscribe_events", {"events": ["state_changed"]})
    assert payload["error"] == "not_implemented", payload
    assert payload["alternatives"] == ["get_history", "get_entity_state", "get_logbook"]


def test_get_sse_stats_not_implemented():
    payload = _call("get_sse_stats", {})
    assert payload["error"] == "not_implemented", payload


if __name__ == "__main__":
    test_subscribe_events_not_implemented()
    test_get_sse_stats_not_implemented()
    print("OK: subscribe_events and get_sse_stats report not_implemented")
