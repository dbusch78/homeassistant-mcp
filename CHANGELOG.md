# Changelog

All notable changes to this project (a fork of
[maximeallanic/homeassistant-mcp](https://github.com/maximeallanic/homeassistant-mcp))
are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This fork starts fresh at **v1.0.0** — a significant divergence from upstream, not a
patch release. Changes relative to the upstream baseline are recorded under the
`[1.0.0]` heading below.

## [Unreleased]

### Added
- `CHANGELOG.md` following Keep a Changelog, tracking this fork's divergence from
  upstream.
- Streamable HTTP transport (`--transport http`, env `MCP_TRANSPORT=http`)
  alongside stdio, sharing the same tool handlers — for Claude Code and networked
  AI agents. Configurable host/port/path (`MCP_HTTP_HOST`/`PORT`/`PATH`, default
  `127.0.0.1:8787/mcp`). DNS-rebinding protection is always enabled with exact
  host/origin allow-lists (overridable via `MCP_ALLOWED_HOSTS`/`MCP_ALLOWED_ORIGINS`);
  a non-loopback bind refuses to start without `MCP_AUTH_TOKEN` and
  `MCP_ALLOWED_HOSTS`; optional bearer-token auth via `MCP_AUTH_TOKEN`. Adds
  `starlette`/`uvicorn` deps and raises the `mcp` floor to `>=1.27.0`.
- Per-client rate limiting on every tool call, across both transports. CLAUDE.md
  listed rate limiting as a standing requirement ("must remain enabled"), but it
  was never actually wired to the tool path — the only limiter lived on the
  unused SSE manager. This is net-new: a token-bucket limiter at the single
  tool-call chokepoint, keyed per MCP session (HTTP) or per process (stdio).
  Configurable via `MCP_RATE_LIMIT_RPM` (default 120) and `MCP_RATE_LIMIT_BURST`
  (default 20); over-limit calls return `{"error": "rate_limited",
  "retry_after_seconds": N}` without contacting Home Assistant.
- Input validation on service-call tools, run before any Home Assistant request.
  CLAUDE.md required input sanitization on service-call tools, but none existed.
  This is net-new: identifiers interpolated into HA REST paths (`domain`,
  `service`, `event_type`, `entity_id`, automation/script config ids) are
  validated against HA's own grammar — blocking `/`, `..`, and control chars
  that could escape the intended endpoint — and free-form payloads are bounded
  (nesting depth, string length, NUL bytes). Invalid input returns
  `{"error": "validation_failed", ...}` instead of reaching HA. Read-only tools
  are unconstrained; validation never rejects a call HA would have accepted.

### Changed
- `.gitignore` now excludes `CLAUDE.md` so machine/network-specific deployment
  context (VLAN topology, Home Assistant host IP) is never committed to the public
  fork.

### Fixed
- HTTP transport now serves both `/mcp` and `/mcp/` with a `200` directly, instead
  of `307`-redirecting the bare path to the trailing-slash form. The single
  Starlette `Mount("/mcp", ...)` issued that redirect at the routing layer, costing
  an extra POST round-trip per call and tripping Claude Code's `/doctor` setup
  warning. The endpoint is now registered as two explicit `Route`s pointing at one
  pure-ASGI handler (so every method — POST/GET/DELETE — passes through). Bearer
  auth and DNS-rebinding protection are unchanged and verified live on both paths.
- Remove duplicate `restart_homeassistant` tool definition. The tool was declared
  twice in `handle_list_tools` (upstream bug), so the server advertised 88 tool
  entries for 87 distinct tools; some MCP clients reject duplicate tool names.
- `get_area_entities` now actually works. Upstream it returned the placeholder
  `"Area entity lookup requires additional implementation"`. It now resolves the
  area name (case-insensitively, including aliases) to an `area_id` and delegates
  to the working `get_entities_by_area` lookup, returning a clear `area_not_found`
  error (with the list of known areas) when no area matches.
- `subscribe_events` and `get_sse_stats` now return explicit not-implemented
  responses instead of silently failing (upstream bug: server.py:1152). Real-time
  streaming is deferred to `feature/sse-streaming` on the HTTP transport; the
  `SSEManager` class is retained and marked with a TODO.
- `start_mcp.sh` now uses the `venv/` virtualenv to match `setup.sh` and
  `start_server.sh` (it referenced a nonexistent `.venv/`, so the script failed
  for anyone who ran the documented `setup.sh`).
- Startup scripts now load `.env` via `set -a; . ./.env; set +a` instead of
  `export $(cat .env | xargs)`. The old form errored on `#` comments and mangled
  any value containing spaces or quotes; the new form sources them correctly.
- README now states Python 3.10+ to match `pyproject.toml`'s `requires-python =
  ">=3.10"` (it claimed 3.11+; the code uses no 3.11-only features).
- Area registry operations (`get_areas`, `create_area`, `update_area`,
  `delete_area`) now use the WebSocket `config/area_registry/*` API. The previous
  REST endpoint `/api/config/area_registry` returns 404 on modern HA (verified
  against 2026.6) — the area registry is WebSocket-only, like the device and entity
  registries. This also unblocks `get_area_entities`, which delegates to
  `get_areas`.
- WebSocket connections now raise aiohttp's max message size to 64 MiB
  (configurable via `HA_WS_MAX_MSG_SIZE`, `0` = unlimited). The 4 MiB default
  tripped `WSCloseCode.MESSAGE_TOO_BIG` on large registry dumps — on this instance
  `config/entity_registry/list` is ~6.5 MB (10,901 entities) — breaking every
  WS-backed tool (entity registry, areas-by-area, automations, …).
- `tests/test_mcp_tools.py` no longer fails tools whose schema omits the optional
  JSON Schema `required` key (a tool with no mandatory params correctly omits it).
  The check now validates `required` only when present — it must be a list naming
  declared properties.

### Security
- Non-loopback exposure gate now treats a whitespace-only `MCP_AUTH_TOKEN` or
  `MCP_ALLOWED_HOSTS` as missing (`os.getenv(var, "").strip()`), closing a gap
  where e.g. `MCP_AUTH_TOKEN="   "` satisfied the gate while being effectively
  empty, allowing an unauthenticated non-loopback bind.
- Bearer-auth middleware now denies non-`http` client scopes instead of passing
  them through. Previously it only checked `Authorization` on `http` scopes, so a
  `websocket` scope would bypass auth entirely. No WebSocket routes are mounted
  today, so this is fail-closed hardening for when SSE/WS transports are added.

## [1.0.0] — Fork baseline

Initial fork of `maximeallanic/homeassistant-mcp`. Subsequent fixes, security work,
and features are recorded under `[Unreleased]` until the next tagged release.
