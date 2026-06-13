#!/usr/bin/env python3
"""
Test script for Home Assistant MCP server tool interfaces
Tests the MCP tool definitions and basic functionality without requiring HA connection
"""

import asyncio
import json
import sys
import os
from typing import List, Dict, Any

# Add parent directory to path to import server module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import server, handle_list_tools

async def test_mcp_server_tools():
    """Test that all new tools are properly defined in the MCP server"""
    
    print("=" * 60)
    print("Testing Home Assistant MCP Server - Tool Definitions")
    print("=" * 60)
    
    # Test that we can list tools
    try:
        tools = await handle_list_tools()
        print(f"✅ Successfully loaded {len(tools)} tools")
        print()
        
        # New feature categories we added
        new_feature_tools = {
            "Area Management": [
                "get_areas", "create_area", "update_area", "delete_area", "get_entities_by_area"
            ],
            "Device Management": [
                "get_devices", "get_device", "update_device"  
            ],
            "System Management": [
                "restart_homeassistant", "stop_homeassistant", "check_config_valid", 
                "get_system_health", "get_supervisor_info", "get_system_info"
            ],
            "Integration Management": [
                "get_integrations", "reload_integration", "disable_integration",
                "enable_integration", "delete_integration", "get_integration_info"
            ],
            "Notification Services": [
                "send_notification", "get_notification_services", "dismiss_notification"
            ],
            "Entity Registry Management": [
                "get_entity_registry", "update_entity_registry", "enable_entity", "disable_entity"
            ]
        }
        
        # Create a set of all available tool names
        available_tools = {tool.name for tool in tools}
        
        # Test each category
        total_expected = 0
        total_found = 0
        
        for category, expected_tools in new_feature_tools.items():
            print(f"📋 {category}")
            print("-" * 40)
            
            category_found = 0
            for tool_name in expected_tools:
                total_expected += 1
                if tool_name in available_tools:
                    print(f"  ✅ {tool_name}")
                    category_found += 1
                    total_found += 1
                else:
                    print(f"  ❌ {tool_name} - MISSING")
            
            print(f"  📊 {category}: {category_found}/{len(expected_tools)} tools found")
            print()
        
        # Print summary
        print("=" * 60)
        print("TOOL DEFINITION SUMMARY")
        print("=" * 60)
        print(f"Expected new tools: {total_expected}")
        print(f"Found new tools: {total_found}")
        print(f"Success rate: {(total_found/total_expected)*100:.1f}%")
        
        if total_found == total_expected:
            print("🎉 All new feature tools are properly defined!")
        else:
            print(f"⚠️  Missing {total_expected - total_found} tools")
        
        print()
        print("=" * 60)
        print("DETAILED TOOL INSPECTION")
        print("=" * 60)
        
        # Show details for a few key new tools
        key_tools_to_inspect = ["get_areas", "get_devices", "get_integrations", "send_notification"]
        
        for tool_name in key_tools_to_inspect:
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                print(f"🔍 {tool_name}:")
                print(f"  Description: {tool.description}")
                print(f"  Required params: {tool.inputSchema.get('required', [])}")
                print(f"  Properties: {list(tool.inputSchema.get('properties', {}).keys())}")
            else:
                print(f"❌ {tool_name}: Not found")
            print()
        
    except Exception as e:
        print(f"❌ Failed to load tools: {str(e)}")
        return False
    
    return total_found == total_expected

async def test_tool_schemas():
    """Test that tool schemas are properly structured"""
    
    print("=" * 60)
    print("Testing Tool Schema Validation")
    print("=" * 60)
    
    try:
        tools = await handle_list_tools()
        
        schema_issues = []
        
        for tool in tools:
            # Check basic required fields
            if not tool.name:
                schema_issues.append(f"Tool missing name: {tool}")
            if not tool.description:
                schema_issues.append(f"Tool {tool.name} missing description")
            if not hasattr(tool, 'inputSchema') or not tool.inputSchema:
                schema_issues.append(f"Tool {tool.name} missing inputSchema")
            
            # Check schema structure for new tools
            if tool.inputSchema and isinstance(tool.inputSchema, dict):
                if 'type' not in tool.inputSchema:
                    schema_issues.append(f"Tool {tool.name} schema missing 'type'")
                if 'properties' not in tool.inputSchema:
                    schema_issues.append(f"Tool {tool.name} schema missing 'properties'")
                # 'required' is OPTIONAL in JSON Schema: a tool with no mandatory
                # params correctly omits it, so its absence is not an error. Only
                # validate it when present — it must be a list of declared properties.
                required = tool.inputSchema.get('required')
                if required is not None:
                    if not isinstance(required, list):
                        schema_issues.append(f"Tool {tool.name} schema 'required' must be a list")
                    else:
                        props = tool.inputSchema.get('properties', {}) or {}
                        for field in required:
                            if field not in props:
                                schema_issues.append(
                                    f"Tool {tool.name} 'required' names undeclared property '{field}'"
                                )
        
        if schema_issues:
            print(f"❌ Found {len(schema_issues)} schema issues:")
            for issue in schema_issues:
                print(f"  - {issue}")
            return False
        else:
            print(f"✅ All {len(tools)} tools have valid schemas")
            return True
    
    except Exception as e:
        print(f"❌ Schema validation failed: {str(e)}")
        return False

async def main():
    """Run all MCP server tests"""
    
    print("Starting MCP Server Tool Tests...")
    print()
    
    # Test 1: Tool definitions
    tools_ok = await test_mcp_server_tools()
    print()
    
    # Test 2: Schema validation  
    schemas_ok = await test_tool_schemas()
    print()
    
    # Final result
    if tools_ok and schemas_ok:
        print("🎉 All MCP server tool tests passed!")
        print()
        print("Next steps:")
        print("1. Set up your Home Assistant connection:")
        print("   export HA_TOKEN='your_long_lived_access_token'")
        print("   export HA_URL='http://your-ha-instance:8123'")
        print("2. Run: python test_new_features.py")
        print("3. Or test via MCP client integration")
        return True
    else:
        print("❌ Some MCP server tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
