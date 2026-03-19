#!/bin/bash

echo "🏠 Setting up Home Assistant MCP Server..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📚 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Make scripts executable
chmod +x server.py
chmod +x start_server.sh

echo "✅ Setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Copy .env.example to .env and configure your Home Assistant settings"
echo "2. Test connectivity with: python test_connection.py"
echo "3. Start the MCP server with: ./start_server.sh"
echo "4. Or integrate with Warp using the mcp_config.json"
