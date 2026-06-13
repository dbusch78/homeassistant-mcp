#!/usr/bin/env python3
"""
Tests for the Streamable HTTP transport.

Covers the security-critical entry points without a live Home Assistant:
  - the non-loopback exposure gate (must refuse to start without creds),
  - the exact DNS-rebinding default lists,
  - a real boot-and-list_tools smoke test over HTTP (no HA needed; tools/list is
    served from the static tool list).
"""

import asyncio
import os
import socket
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server


# --- exposure gate -----------------------------------------------------------

def test_gate_allows_loopback():
    # Loopback never requires creds.
    server._enforce_exposure_gate("127.0.0.1")
    server._enforce_exposure_gate("localhost")
    server._enforce_exposure_gate("::1")


def test_gate_blocks_non_loopback_without_creds():
    for var in ("MCP_AUTH_TOKEN", "MCP_ALLOWED_HOSTS"):
        os.environ.pop(var, None)
    try:
        server._enforce_exposure_gate("0.0.0.0")
    except SystemExit as e:
        assert "MCP_AUTH_TOKEN" in str(e) and "MCP_ALLOWED_HOSTS" in str(e), str(e)
    else:
        raise AssertionError("non-loopback bind without creds must refuse to start")


def test_gate_requires_both_creds():
    os.environ["MCP_AUTH_TOKEN"] = "x"
    os.environ.pop("MCP_ALLOWED_HOSTS", None)
    try:
        server._enforce_exposure_gate("172.21.30.5")
    except SystemExit as e:
        assert "MCP_ALLOWED_HOSTS" in str(e) and "MCP_AUTH_TOKEN" not in str(e), str(e)
    else:
        raise AssertionError("must still refuse when only one cred is set")
    finally:
        os.environ.pop("MCP_AUTH_TOKEN", None)


def test_gate_passes_non_loopback_with_both_creds():
    os.environ["MCP_AUTH_TOKEN"] = "x"
    os.environ["MCP_ALLOWED_HOSTS"] = "172.21.30.5:8787"
    try:
        server._enforce_exposure_gate("172.21.30.5")  # should not raise
    finally:
        os.environ.pop("MCP_AUTH_TOKEN", None)
        os.environ.pop("MCP_ALLOWED_HOSTS", None)


# --- DNS-rebinding defaults ---------------------------------------------------

def test_security_settings_exact_defaults():
    for var in ("MCP_ALLOWED_HOSTS", "MCP_ALLOWED_ORIGINS"):
        os.environ.pop(var, None)
    s = server._build_security_settings("127.0.0.1", 8787)
    assert s.enable_dns_rebinding_protection is True
    assert s.allowed_hosts == ["127.0.0.1:8787"], s.allowed_hosts
    assert s.allowed_origins == ["http://127.0.0.1:8787"], s.allowed_origins


def test_security_settings_env_override():
    os.environ["MCP_ALLOWED_ORIGINS"] = "http://a:1, http://b:2"
    try:
        s = server._build_security_settings("127.0.0.1", 8787)
        assert s.allowed_origins == ["http://a:1", "http://b:2"], s.allowed_origins
    finally:
        os.environ.pop("MCP_ALLOWED_ORIGINS", None)


# --- boot + tools/list over HTTP ---------------------------------------------

def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_http_initialize_and_list_tools():
    import uvicorn
    from mcp.client.streamable_http import streamablehttp_client
    from mcp import ClientSession

    port = _free_port()
    app = server.build_http_app("127.0.0.1", port, "/mcp")
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    uv = uvicorn.Server(config)

    thread = threading.Thread(target=uv.run, daemon=True)
    thread.start()

    # Wait until the port accepts connections (or fail fast).
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                break
        except OSError:
            time.sleep(0.1)
    else:
        raise AssertionError("HTTP server did not start within 10s")

    async def _exercise():
        url = f"http://127.0.0.1:{port}/mcp"
        async with streamablehttp_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                return [t.name for t in tools.tools]

    def _forged_host_status(target_path: str) -> int:
        # Real TCP connection to the bound port, but a spoofed Host header — the
        # exact shape of a DNS-rebinding attack. Must be rejected (421), proving
        # protection is live and not merely configured.
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        # Both "/mcp" and "/mcp/" are registered as explicit Routes that serve 200
        # directly (no 307 redirect), so the transport security middleware runs on
        # the bare path too. Exercise the given form to prove that.
        conn.request(
            "POST", target_path,
            body=b"{}",
            headers={
                "Host": "evil.attacker.example",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        status = conn.getresponse().status
        conn.close()
        return status

    try:
        names = asyncio.run(_exercise())
        forged_status_bare = _forged_host_status("/mcp")
        forged_status_slash = _forged_host_status("/mcp/")
    finally:
        uv.should_exit = True
        thread.join(timeout=10)

    assert "get_entity_state" in names, names
    assert "restart_homeassistant" in names
    # No duplicates, and the full surface is advertised over HTTP.
    assert len(names) == len(set(names)), "duplicate tool names over HTTP"
    assert len(names) >= 80, f"expected the full tool set, got {len(names)}"
    # DNS-rebinding protection actively rejects a spoofed Host header on BOTH the
    # bare path and its trailing-slash form (neither redirects away first).
    assert forged_status_bare == 421, f"forged Host on /mcp should be 421, got {forged_status_bare}"
    assert forged_status_slash == 421, f"forged Host on /mcp/ should be 421, got {forged_status_slash}"


if __name__ == "__main__":
    test_gate_allows_loopback()
    test_gate_blocks_non_loopback_without_creds()
    test_gate_requires_both_creds()
    test_gate_passes_non_loopback_with_both_creds()
    test_security_settings_exact_defaults()
    test_security_settings_env_override()
    test_http_initialize_and_list_tools()
    print("OK: HTTP transport gate, security defaults, and live tools/list all pass")
