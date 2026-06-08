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

### Changed
- `.gitignore` now excludes `CLAUDE.md` so machine/network-specific deployment
  context (VLAN topology, Home Assistant host IP) is never committed to the public
  fork.

### Fixed
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

## [1.0.0] — Fork baseline

Initial fork of `maximeallanic/homeassistant-mcp`. Subsequent fixes, security work,
and features are recorded under `[Unreleased]` until the next tagged release.
