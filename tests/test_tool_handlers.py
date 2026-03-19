#!/usr/bin/env python3
"""
Mock integration test for Home Assistant MCP server tool handlers
Tests that tool handlers can be called without needing real HA connection
"""

import asyncio
import json
import sys
import os
from unittest.mock import patch, AsyncMock
from typing import Dict, Any, List

# Add parent directory to path to import server module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import handle_call_tool, HomeAssistantClient

async def test_tool_handlers():
    """Test that tool handlers work correctly with mocked HA client"""
    
    print("=" * 60)
    print("Testing Home Assistant MCP Server - Tool Handlers")
    print("=" * 60)
    
    # Mock HomeAssistant responses for different tool categories
    mock_responses = {
        # Area Management
        "get_areas": [
            {"area_id": "living_room", "name": "Living Room", "aliases": ["lounge"]},
            {"area_id": "bedroom", "name": "Bedroom", "aliases": []}
        ],
        "create_area": {"area_id": "test_area", "name": "Test Area"},
        
        # Device Management  
        "get_devices": [
            {"id": "device1", "name": "Test Device", "area_id": "living_room"},
            {"id": "device2", "name": "Another Device", "area_id": "bedroom"}
        ],
        "get_device": {"id": "device1", "name": "Test Device", "area_id": "living_room"},
        
        # System Management
        "get_system_health": {"status": "ok", "components": {"core": {"status": "ok"}}},
        "get_system_info": {"version": "2024.1.0", "installation_type": "Home Assistant OS"},
        "check_config_valid": {"result": "valid", "errors": []},
        "get_supervisor_info": {"version": "2024.01.1", "channel": "stable"},
        
        # Integration Management
        "get_integrations": [
            {"entry_id": "integration1", "domain": "hue", "title": "Philips Hue"},
            {"entry_id": "integration2", "domain": "mqtt", "title": "MQTT"}
        ],
        "get_integration_info": {"entry_id": "integration1", "domain": "hue", "title": "Philips Hue"},
        
        # Notification Services
        "get_notification_services": ["persistent_notification", "mobile_app_phone"],
        "send_notification": [{"success": True}],
        
        # Entity Registry
        "get_entity_registry": [
            {"entity_id": "light.living_room", "name": "Living Room Light", "area_id": "living_room"},
            {"entity_id": "sensor.temperature", "name": "Temperature", "area_id": "bedroom"}
        ]
    }
    
    # Test cases - tool name and arguments
    test_cases = [
        # Area Management Tests
        ("get_areas", {}),
        ("create_area", {"name": "Test Area", "aliases": ["test"]}),
        
        # Device Management Tests  
        ("get_devices", {}),
        ("get_device", {"device_id": "device1"}),
        
        # System Management Tests (safe ones only)
        ("get_system_health", {}),
        ("get_system_info", {}),
        ("check_config_valid", {}),
        ("get_supervisor_info", {}),
        
        # Integration Management Tests
        ("get_integrations", {}),
        ("get_integration_info", {"config_entry_id": "integration1"}),
        
        # Notification Services Tests
        ("get_notification_services", {}),
        ("send_notification", {"message": "Test message", "title": "Test"}),
        
        # Entity Registry Tests
        ("get_entity_registry", {}),
    ]
    
    results = {}
    
    # Mock both the HomeAssistantClient and the HA_TOKEN variable
    with patch('server.HA_TOKEN', 'mock_token_for_testing'), \
         patch('server.HomeAssistantClient') as MockClient:
        mock_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_instance
        
        # Configure mock responses
        for method, response in mock_responses.items():
            setattr(mock_instance, method, AsyncMock(return_value=response))
        
        # Test each tool handler
        for tool_name, arguments in test_cases:
            print(f"🔧 Testing {tool_name}...")
            
            try:
                result = await handle_call_tool(tool_name, arguments)
                
                # Parse the result
                if result and len(result) > 0:
                    response_text = result[0].text
                    response_data = json.loads(response_text)
                    
                    # Check if we got an error
                    if "error" in response_data:
                        print(f"  ❌ {tool_name}: {response_data['error']}")
                        results[tool_name] = {"status": "error", "error": response_data["error"]}
                    else:
                        print(f"  ✅ {tool_name}: Success")
                        results[tool_name] = {"status": "success", "data_type": type(response_data).__name__}
                else:
                    print(f"  ❌ {tool_name}: No result returned")
                    results[tool_name] = {"status": "error", "error": "No result returned"}
                    
            except Exception as e:
                print(f"  ❌ {tool_name}: Exception - {str(e)}")
                results[tool_name] = {"status": "error", "error": str(e)}
    
    # Clean up
    if "HA_TOKEN" in os.environ:
        del os.environ["HA_TOKEN"]
    
    # Print summary
    print()
    print("=" * 60)
    print("TOOL HANDLER TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results.values() if r["status"] == "success")
    total_tests = len(results)
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
    print()
    
    if successful_tests == total_tests:
        print("🎉 All tool handlers working correctly!")
        return True
    else:
        print("❌ Some tool handlers have issues:")
        for tool_name, result in results.items():
            if result["status"] != "success":
                print(f"  - {tool_name}: {result['error']}")
        return False

async def main():
    """Run the tool handler tests"""
    success = await test_tool_handlers()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
