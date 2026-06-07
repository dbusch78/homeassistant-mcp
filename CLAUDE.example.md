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

## Git & GitHub Workflow
See CONTRIBUTING.md for branching strategy, commit standards,
PR workflow, and versioning policy.

## Before Any Work
Fetch and read:
- https://modelcontextprotocol.io/docs/
- https://www.home-assistant.io/docs/api/rest/
- https://developers.home-assistant.io/docs/api/websocket/