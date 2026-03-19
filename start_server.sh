#!/bin/bash
# Home Assistant MCP Server Startup Script
# Change to the directory where this script is located
cd "$(dirname "$0")"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Check if HA_TOKEN is set
if [ -z "$HA_TOKEN" ]; then
    echo "❌ HA_TOKEN environment variable is not set!"
    echo "Please set your Home Assistant long-lived access token:"
    echo "1. Copy .env.example to .env"
    echo "2. Edit .env and add your token"
    echo "3. Or export HA_TOKEN='your_token_here'"
    exit 1
fi

# Activate virtual environment and run server
echo "🏠 Starting Home Assistant MCP Server..."
echo "🔗 Connecting to: ${HA_URL:-http://homeassistant.local:8123}"

source venv/bin/activate
exec python server.py
