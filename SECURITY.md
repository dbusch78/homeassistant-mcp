# Security Policy

This is a hardened fork of
[maximeallanic/homeassistant-mcp](https://github.com/maximeallanic/homeassistant-mcp).
The MCP server exposes Home Assistant's full control surface to an AI client, so
the transport and tool layers enforce defense in depth. This document describes
that model and how to report a vulnerability.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | ✅ active |
| 1.0.x   | ⚠️ superseded by 1.1.x — please upgrade |
| upstream / pre-fork | tracked separately upstream |

## Reporting a Vulnerability

Please **do not open a public issue** for security problems.

Report privately via GitHub: **Security → Report a vulnerability** (private
vulnerability reporting) on this repository. Include the affected version, a
description, and reproduction steps if available. You can expect an initial
acknowledgement within a few days; fixes are developed on a private branch and
disclosed once a patched release is available.

## Security Model

Design principles (inherited from the project's deployment philosophy): **local
control only, privacy first, least privilege, security by default.** No data
leaves the network and there are no cloud dependencies in this stack.

### Transport security

The **stdio** transport is a local subprocess launched by the client; its trust
boundary is the local machine. The **Streamable HTTP** transport (opt-in via
`--transport http` / `MCP_TRANSPORT=http`) adds network reach and is hardened in
layers:

1. **Loopback by default** — binds `127.0.0.1:8787`. Nothing is network-exposed
   unless you change `MCP_HTTP_HOST`.
2. **Non-loopback exposure gate** — on a non-loopback bind the server **refuses
   to start** unless *both* `MCP_AUTH_TOKEN` and `MCP_ALLOWED_HOSTS` are set
   (whitespace-only values count as unset). This prevents a stray
   `MCP_HTTP_HOST=0.0.0.0` from silently exposing Home Assistant control.
3. **DNS-rebinding protection** — always on. Only the exact bind address is an
   allowed `Host`/`Origin` by default (override with `MCP_ALLOWED_HOSTS` /
   `MCP_ALLOWED_ORIGINS`). A forged `Host` header is rejected with **HTTP 421**.
4. **Bearer-token auth** — optional via `MCP_AUTH_TOKEN` (required for any
   non-loopback bind, per the gate above). Compared in constant time. Enforced on
   HTTP requests; non-HTTP ASGI scopes (e.g. websocket) are **denied outright**
   rather than allowed to bypass the check (fail-closed).

### Tool-call security (both transports)

5. **Rate limiting** — every tool call passes a per-client token-bucket limiter
   (`MCP_RATE_LIMIT_RPM`, default 120; `MCP_RATE_LIMIT_BURST`, default 20), keyed
   per MCP session (HTTP) or per process (stdio). Over-limit calls return
   `{"error": "rate_limited", ...}` and never reach Home Assistant — protecting
   the HA instance from a runaway agent loop.
6. **Input validation** — any tool that interpolates a caller-supplied identifier
   into a Home Assistant REST path, or mutates state, is validated *before* the
   HA request. Identifiers (`domain`, `service`, `event_type`, `entity_id`,
   automation/script config ids) are checked for path-safety — no `/`, no `..`,
   no control characters — so a value cannot escape its intended endpoint.
   Free-form payloads (`service_data`, `attributes`, configs, templates) are
   bounded for nesting depth, string length, and NUL bytes. Invalid input returns
   `{"error": "validation_failed", ...}`. Read-only tools without an injected path
   component are unconstrained; validation never rejects input HA would accept.

### Two-tier tool model

Tools fall into two privilege tiers, and the project's rule is that **an AI agent
gets only what it is explicitly authorized to access**:

- **Tier 1 — read / observability** (`get_*`, `search_entities`, history,
  logbook, registries): no state change; low risk.
- **Tier 2 — control / mutating** (`call_service`, `set_state`, `delete_state`,
  `fire_event`, automation & script CRUD, `restart`/`stop` Home Assistant): these
  change device or system state and are the focus of input validation.

By policy, **no tool permits arbitrary code execution on the Home Assistant
host**, and tools that would expose the isolated camera network to agents are not
added without explicit review.

### Secrets handling

- The Home Assistant long-lived token and any `MCP_AUTH_TOKEN` are read from the
  environment / `.env` only — never hardcoded, never written to logs. Entity
  state values that may contain PII are not logged.
- `.env` is the development fallback (keep it `chmod 600`; it is gitignored and
  dockerignored, never committed or baked into an image).
- For production deployments, a secrets manager with per-service scoped tokens is
  recommended so no container can read another service's secrets.

## Hardening checklist (non-loopback / cross-VLAN deployment)

- [ ] Set a strong random `MCP_AUTH_TOKEN` and an explicit `MCP_ALLOWED_HOSTS`.
- [ ] Keep the `Host`/`Origin` allowlists as tight as possible.
- [ ] Use a **least-privilege** Home Assistant token (only the scopes you need).
- [ ] Restrict network reachability to the MCP port (firewall to the HA host only).
- [ ] Tune `MCP_RATE_LIMIT_*` to your expected client load.
