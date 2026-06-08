#!/usr/bin/env python3
"""
Regression test: the WebSocket connection raises aiohttp's max message size.

Home Assistant registry dumps (config/entity_registry/list, etc.) can exceed
aiohttp's 4 MiB default and trip WSCloseCode.MESSAGE_TOO_BIG. _ws_ensure_connected
must pass an explicit, larger max_msg_size to ws_connect. No live HA required.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
from server import HomeAssistantClient, WS_MAX_MSG_SIZE


def test_ws_connect_passes_max_msg_size():
    client = HomeAssistantClient("http://ha.test", "token")

    ws = AsyncMock()
    ws.closed = False
    # Auth handshake: auth_required -> (we send auth) -> auth_ok
    ws.receive_json = AsyncMock(side_effect=[{"type": "auth_required"}, {"type": "auth_ok"}])
    ws.send_json = AsyncMock()

    client.session = AsyncMock()
    client.session.ws_connect = AsyncMock(return_value=ws)

    asyncio.run(client._ws_ensure_connected())

    client.session.ws_connect.assert_awaited_once()
    _, kwargs = client.session.ws_connect.call_args
    assert kwargs.get("max_msg_size") == WS_MAX_MSG_SIZE, kwargs
    # Must be well above aiohttp's 4 MiB default that caused MESSAGE_TOO_BIG.
    assert WS_MAX_MSG_SIZE > 4 * 1024 * 1024, WS_MAX_MSG_SIZE


def test_env_override(monkeypatch_env="HA_WS_MAX_MSG_SIZE"):
    # Reloading the module with the env set should pick up the override.
    import importlib
    os.environ["HA_WS_MAX_MSG_SIZE"] = str(123456)
    try:
        importlib.reload(server)
        assert server.WS_MAX_MSG_SIZE == 123456, server.WS_MAX_MSG_SIZE
    finally:
        os.environ.pop("HA_WS_MAX_MSG_SIZE", None)
        importlib.reload(server)  # restore default for any later tests


if __name__ == "__main__":
    test_ws_connect_passes_max_msg_size()
    test_env_override()
    print("OK: WebSocket connection raises max_msg_size (with env override)")
