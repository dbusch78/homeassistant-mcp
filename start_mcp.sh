#!/bin/bash
# Home Assistant MCP Server - Startup script for Personas Studio / Claude agents
# Loads credentials from .env and starts the MCP server via stdio
cd "$(dirname "$0")"

# Load .env if present.
# Source with auto-export so quoted values, spaces, and #-comments survive
# (the old `export $(grep -v '^#' .env | xargs)` mangled all three).
if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi

# Validate required environment variables
if [ -z "$HA_URL" ] || [ -z "$HA_TOKEN" ]; then
    echo "Error: HA_URL and HA_TOKEN must be set in .env or as environment variables" >&2
    exit 1
fi

exec venv/bin/python server.py
