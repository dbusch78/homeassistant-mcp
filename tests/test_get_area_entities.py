#!/usr/bin/env python3
"""
Regression test for the get_area_entities tool handler.

Upstream, get_area_entities returned a static placeholder
("Area entity lookup requires additional implementation"). It now resolves a
human-friendly area name (case-insensitively, including aliases) to an area_id
and delegates to get_entities_by_area. These tests run without a live Home
Assistant by patching the client.
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import handle_call_tool


AREAS = [
    {"area_id": "living_room", "name": "Living Room", "aliases": ["lounge"]},
    {"area_id": "bedroom", "name": "Bedroom", "aliases": []},
]


def _call(area_name: str):
    async def _run():
        with patch("server.HA_TOKEN", "test-token"), \
             patch("server.HomeAssistantClient") as MockClient:
            client = AsyncMock()
            client.get_areas = AsyncMock(return_value=AREAS)
            client.get_entities_by_area = AsyncMock(
                return_value={"items": [{"entity_id": "light.lr"}], "total": 1}
            )
            MockClient.return_value.__aenter__.return_value = client
            result = await handle_call_tool("get_area_entities", {"area_name": area_name})
            payload = json.loads(result[0].text)
            return client, payload

    return asyncio.run(_run())


def test_resolves_name_to_area_id_and_delegates():
    client, payload = _call("living room")  # case-insensitive
    client.get_entities_by_area.assert_awaited_once_with(area_id="living_room")
    assert payload["total"] == 1, payload


def test_matches_alias():
    client, payload = _call("Lounge")  # alias of living_room
    client.get_entities_by_area.assert_awaited_once_with(area_id="living_room")


def test_unknown_area_returns_error_without_delegating():
    client, payload = _call("Garage")
    client.get_entities_by_area.assert_not_awaited()
    assert payload["error"] == "area_not_found", payload
    assert "Garage" in payload["message"]


if __name__ == "__main__":
    test_resolves_name_to_area_id_and_delegates()
    test_matches_alias()
    test_unknown_area_returns_error_without_delegating()
    print("OK: get_area_entities resolves names, aliases, and unknown areas")
