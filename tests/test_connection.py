#!/usr/bin/env python3
"""
Test script to verify Home Assistant connectivity and API access.

This script tests the core functionality of the Home Assistant MCP server
by connecting to your Home Assistant instance and performing basic operations.
"""

import asyncio
import json
import os
import sys
from server import HomeAssistantClient

async def test_connection():
    """Test connection to Home Assistant"""
    ha_url = os.getenv("HA_URL", "http://homeassistant.local:8123")
    ha_token = os.getenv("HA_TOKEN", "")
    
    if not ha_token:
        print("❌ HA_TOKEN environment variable not set")
        print("Please set your Home Assistant long-lived access token:")
        print("export HA_TOKEN='your_token_here'")
        return False
    
    print(f"🔗 Testing connection to {ha_url}")
    
    try:
        async with HomeAssistantClient(ha_url, ha_token) as client:
            # Test basic connectivity
            config = await client.get_config()
            print("✅ Successfully connected to Home Assistant!")
            print(f"   Version: {config.get('version', 'Unknown')}")
            print(f"   Location: {config.get('location_name', 'Unknown')}")
            print(f"   Time Zone: {config.get('time_zone', 'Unknown')}")
            
            # Test getting states
            states = await client.get_states()
            print(f"✅ Found {len(states)} entities")
            
            # Show a few example entities
            print("📋 Example entities:")
            for i, entity in enumerate(states[:5]):
                friendly_name = entity.get('attributes', {}).get('friendly_name', entity['entity_id'])
                print(f"   {entity['entity_id']}: {entity['state']} ({friendly_name})")
            
            if len(states) > 5:
                print(f"   ... and {len(states) - 5} more")
            
            # Test getting services
            services = await client.get_services()
            print(f"✅ Found {len(services)} service domains")
            
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🏠 Home Assistant MCP Server - Connection Test")
    print("=" * 50)
    
    success = await test_connection()
    
    if success:
        print("\n🎉 All tests passed! Your Home Assistant MCP server should work correctly.")
        print("\nTo use the MCP server:")
        print("1. Set your HA_TOKEN environment variable")
        print("2. Run: python server.py")
    else:
        print("\n💡 Please check your Home Assistant configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
