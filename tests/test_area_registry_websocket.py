#!/usr/bin/env python3
"""
Regression test: area registry operations use the WebSocket API, not REST.

Upstream, get_areas/create_area/update_area/delete_area called
/api/config/area_registry over REST — an endpoint that returns 404 on modern HA
(the area registry is WebSocket-only). These tests assert each method now issues
the correct config/area_registry/* WS command. No live HA required.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import HomeAssistantClient


def _client_capturing():
    client = HomeAssistantClient("http://ha.test", "token")
    sent = []

    async def fake_ws(cmd):
        sent.append(cmd)
        return {"ok": True}

    client._ws_send_command = AsyncMock(side_effect=fake_ws)
    # Guard: REST must not be used for any area op.
    client._request = AsyncMock(side_effect=AssertionError("area ops must not use REST"))
    return client, sent


def test_get_areas_uses_ws_list():
    client, sent = _client_capturing()
    asyncio.run(client.get_areas())
    assert sent == [{"type": "config/area_registry/list"}], sent


def test_create_area_with_and_without_aliases():
    client, sent = _client_capturing()
    asyncio.run(client.create_area("Garage", ["bay"]))
    assert sent[-1] == {"type": "config/area_registry/create", "name": "Garage", "aliases": ["bay"]}, sent[-1]
    asyncio.run(client.create_area("Attic"))
    assert sent[-1] == {"type": "config/area_registry/create", "name": "Attic"}, sent[-1]


def test_update_area():
    client, sent = _client_capturing()
    asyncio.run(client.update_area("area_1", "Office", ["study"]))
    assert sent[-1] == {
        "type": "config/area_registry/update",
        "area_id": "area_1",
        "name": "Office",
        "aliases": ["study"],
    }, sent[-1]


def test_delete_area():
    client, sent = _client_capturing()
    asyncio.run(client.delete_area("area_1"))
    assert sent[-1] == {"type": "config/area_registry/delete", "area_id": "area_1"}, sent[-1]


if __name__ == "__main__":
    test_get_areas_uses_ws_list()
    test_create_area_with_and_without_aliases()
    test_update_area()
    test_delete_area()
    print("OK: area registry operations use the WebSocket API")
