# HA-MCP Project -- Claude Code Context

## Purpose
This project deploys and extends an MCP server that gives AI agents
full programmatic access to Home Assistant via REST API and WebSocket.

## Home Assistant Instance
- Host: YOUR_HA_IP:8123 (set in .env as HA_HOST)
- Version: YOUR_HA_VERSION

## Network Architecture
Document your network segmentation here.
Example: VLANs for Primary, IoT, Cameras, AI infrastructure.

## Core Philosophy
- Local control preferred over cloud
- Privacy first
- Security by default -- least privilege

## Development Standards
- Python virtual environment always (never system Python)
- All secrets via .env, never hardcoded
- See CONTRIBUTING.md for full standards

## Secrets Management

### Core Rule
Each MCP server is the sole owner of its secrets. Secrets are passed via
per-process environment only, never shared across MCP boundaries, never
logged, never written to disk outside the process's own secret store.

### Development / Simple Deployment (.env fallback)
A local .env file is acceptable for development or single-user deployments:
- chmod 600, owned by the process user
- Never committed (enforced via .gitignore)
- Never shared between containers or processes
- Never baked into a Docker image (add .env to .dockerignore)

### Hard Rules (no exceptions)
- Never hardcode secrets in source code or Dockerfiles
- Never log token values, API keys, or entity state values containing PII
- Never use a shared .env across multiple MCP containers or processes

## Git & GitHub Workflow
See CONTRIBUTING.md for branching strategy, commit standards,
PR workflow, and versioning policy.

### Documentation Currency Rule
README.md must be updated in the same PR as any change that affects:
- Available tools (added, removed, or behavior changed)
- Transport options or configuration
- Security model or deployment requirements
- Environment variables (new, removed, or changed defaults)
- Installation or setup steps

The README must always reflect what the current code actually does.
A feature is not complete until the README documents it.
CHANGELOG.md records history; README.md reflects present state.
Both must be updated together on every feature/fix/security PR.

### Document Review Protocol
When drafting any document that requires review before committing (SECURITY.md,
CONTRIBUTING.md, release notes, or any other public-facing file), always:
1. Write the draft to a _draft_<filename> temp file first
2. Present the file for review via the file path, not console output
3. On approval, move to the final path and commit
4. Delete or gitignore the temp file after committing

Console output is ephemeral and loses context in long sessions. Never present
a document for review by printing it to the console.

## Before Any Work
Fetch and read:
- https://modelcontextprotocol.io/docs/
- https://www.home-assistant.io/docs/api/rest/
- https://developers.home-assistant.io/docs/api/websocket/