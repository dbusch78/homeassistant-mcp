#!/usr/bin/env python3
"""
Test script for new Home Assistant MCP server features:
- Area/Device Management
- System Management  
- Integration Management
- Notification Services
- Entity Registry Management
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, List

# Add the parent directory to sys.path to import the server module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import HomeAssistantClient

# Configuration - these should be set as environment variables
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")

class FeatureTester:
    """Test class for new Home Assistant MCP features"""
    
    def __init__(self, ha_url: str, ha_token: str):
        self.ha_url = ha_url
        self.ha_token = ha_token
        self.test_results = {}
        
    async def run_all_tests(self):
        """Run all feature tests"""
        print("=" * 60)
        print("Testing Home Assistant MCP Server - New Features")
        print("=" * 60)
        
        if not self.ha_token:
            print("❌ HA_TOKEN not set. Please set your Home Assistant token.")
            return
        
        print(f"🏠 Testing against: {self.ha_url}")
        print()
        
        # Test categories
        test_categories = [
            ("Area Management", self.test_area_management),
            ("Device Management", self.test_device_management), 
            ("System Management", self.test_system_management),
            ("Integration Management", self.test_integration_management),
            ("Notification Services", self.test_notification_services),
            ("Entity Registry Management", self.test_entity_registry_management)
        ]
        
        for category_name, test_func in test_categories:
            print(f"📋 Testing {category_name}...")
            print("-" * 40)
            
            try:
                async with HomeAssistantClient(self.ha_url, self.ha_token) as client:
                    results = await test_func(client)
                    self.test_results[category_name] = results
                    self.print_results(category_name, results)
            except Exception as e:
                print(f"❌ Failed to test {category_name}: {str(e)}")
                self.test_results[category_name] = {"error": str(e)}
            
            print()
        
        # Print summary
        self.print_summary()
    
    async def test_area_management(self, client: HomeAssistantClient) -> Dict[str, Any]:
        """Test area management features"""
        results = {}
        
        try:
            # Test get_areas
            areas = await client.get_areas()
            results["get_areas"] = {
                "status": "success",
                "count": len(areas),
                "sample": areas[:2] if areas else []
            }
            print(f"✅ get_areas: Found {len(areas)} areas")
        except Exception as e:
            results["get_areas"] = {"status": "error", "error": str(e)}
            print(f"❌ get_areas failed: {str(e)}")
        
        try:
            # Test create_area (with a test area)
            test_area = await client.create_area("MCP_Test_Area", aliases=["test"])
            results["create_area"] = {"status": "success", "area_id": test_area.get("area_id")}
            print(f"✅ create_area: Created test area")
            
            # Clean up - delete the test area
            if "area_id" in test_area:
                await client.delete_area(test_area["area_id"])
                print("🧹 Cleaned up test area")
        except Exception as e:
            results["create_area"] = {"status": "error", "error": str(e)}
            print(f"❌ create_area failed: {str(e)}")
        
        return results
    
    async def test_device_management(self, client: HomeAssistantClient) -> Dict[str, Any]:
        """Test device management features"""
        results = {}
        
        try:
            # Test get_devices
            devices = await client.get_devices()
            results["get_devices"] = {
                "status": "success",
                "count": len(devices),
                "sample": devices[:2] if devices else []
            }
            print(f"✅ get_devices: Found {len(devices)} devices")
            
            # Test get_device for first device if available
            if devices:
                device_id = devices[0].get("id")
                if device_id:
                    device_info = await client.get_device(device_id)
                    results["get_device"] = {"status": "success", "device_name": device_info.get("name")}
                    print(f"✅ get_device: Retrieved device info")
                
        except Exception as e:
            results["get_devices"] = {"status": "error", "error": str(e)}
            print(f"❌ get_devices failed: {str(e)}")
        
        return results
    
    async def test_system_management(self, client: HomeAssistantClient) -> Dict[str, Any]:
        """Test system management features (non-destructive tests only)"""
        results = {}
        
        try:
            # Test get_system_health
            health = await client.get_system_health()
            results["get_system_health"] = {"status": "success", "available": "status" in health}
            print(f"✅ get_system_health: System health info retrieved")
        except Exception as e:
            results["get_system_health"] = {"status": "error", "error": str(e)}
            print(f"❌ get_system_health failed: {str(e)}")
        
        try:
            # Test get_system_info
            sys_info = await client.get_system_info()
            results["get_system_info"] = {"status": "success", "has_version": "version" in sys_info}
            print(f"✅ get_system_info: System info retrieved")
        except Exception as e:
            results["get_system_info"] = {"status": "error", "error": str(e)}
            print(f"❌ get_system_info failed: {str(e)}")
        
        try:
            # Test check_config_valid
            config_check = await client.check_config_valid()
            results["check_config_valid"] = {"status": "success", "valid": config_check.get("result") == "valid"}
            print(f"✅ check_config_valid: Configuration check completed")
        except Exception as e:
            results["check_config_valid"] = {"status": "error", "error": str(e)}
            print(f"❌ check_config_valid failed: {str(e)}")
        
        try:
            # Test get_supervisor_info (may not be available on all installations)
            supervisor = await client.get_supervisor_info()
            results["get_supervisor_info"] = {"status": "success", "available": "error" not in supervisor}
            if "error" in supervisor:
                print(f"ℹ️  get_supervisor_info: {supervisor['error']}")
            else:
                print(f"✅ get_supervisor_info: Supervisor info retrieved")
        except Exception as e:
            results["get_supervisor_info"] = {"status": "error", "error": str(e)}
            print(f"❌ get_supervisor_info failed: {str(e)}")
        
        return results
    
    async def test_integration_management(self, client: HomeAssistantClient) -> Dict[str, Any]:
        """Test integration management features"""
        results = {}
        
        try:
            # Test get_integrations
            integrations = await client.get_integrations()
            results["get_integrations"] = {
                "status": "success",
                "count": len(integrations),
                "sample_domains": [i.get("domain") for i in integrations[:3]]
            }
            print(f"✅ get_integrations: Found {len(integrations)} integrations")
            
            # Test get_integration_info for first integration if available
            if integrations:
                entry_id = integrations[0].get("entry_id")
                if entry_id:
                    integration_info = await client.get_integration_info(entry_id)
                    results["get_integration_info"] = {"status": "success", "domain": integration_info.get("domain")}
                    print(f"✅ get_integration_info: Retrieved integration details")
                
        except Exception as e:
            results["get_integrations"] = {"status": "error", "error": str(e)}
            print(f"❌ get_integrations failed: {str(e)}")
        
        return results
    
    async def test_notification_services(self, client: HomeAssistantClient) -> Dict[str, Any]:
        """Test notification services"""
        results = {}
        
        try:
            # Test get_notification_services
            services = await client.get_notification_services()
            results["get_notification_services"] = {
                "status": "success",
                "count": len(services),
                "services": services
            }
            print(f"✅ get_notification_services: Found {len(services)} notification services")
        except Exception as e:
            results["get_notification_services"] = {"status": "error", "error": str(e)}
            print(f"❌ get_notification_services failed: {str(e)}")
        
        try:
            # Test send_notification (persistent notification)
            notification = await client.send_notification(
                message="MCP Server test notification",
                title="Test from MCP"
            )
            results["send_notification"] = {"status": "success"}
            print(f"✅ send_notification: Sent test notification")
        except Exception as e:
            results["send_notification"] = {"status": "error", "error": str(e)}
            print(f"❌ send_notification failed: {str(e)}")
        
        return results
    
    async def test_entity_registry_management(self, client: HomeAssistantClient) -> Dict[str, Any]:
        """Test entity registry management"""
        results = {}
        
        try:
            # Test get_entity_registry
            registry = await client.get_entity_registry()
            results["get_entity_registry"] = {
                "status": "success",
                "count": len(registry),
                "sample": registry[:2] if registry else []
            }
            print(f"✅ get_entity_registry: Found {len(registry)} registered entities")
        except Exception as e:
            results["get_entity_registry"] = {"status": "error", "error": str(e)}
            print(f"❌ get_entity_registry failed: {str(e)}")
        
        return results
    
    def print_results(self, category: str, results: Dict[str, Any]):
        """Print test results for a category"""
        if "error" in results:
            print(f"❌ {category}: {results['error']}")
        else:
            success_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get("status") == "success")
            total_count = len(results)
            print(f"📊 {category}: {success_count}/{total_count} tests passed")
    
    def print_summary(self):
        """Print overall test summary"""
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_categories = len(self.test_results)
        successful_categories = 0
        
        for category, results in self.test_results.items():
            if "error" not in results:
                success_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get("status") == "success")
                total_tests = len(results)
                status = "✅" if success_count > 0 else "❌"
                print(f"{status} {category}: {success_count}/{total_tests} tests passed")
                if success_count > 0:
                    successful_categories += 1
            else:
                print(f"❌ {category}: Failed with error")
        
        print()
        print(f"Overall: {successful_categories}/{total_categories} categories had successful tests")
        
        if successful_categories == total_categories:
            print("🎉 All feature categories tested successfully!")
        elif successful_categories > 0:
            print("⚠️  Some features working, some may need attention")
        else:
            print("🚨 No features could be tested successfully - check configuration")

async def main():
    """Main test function"""
    if not HA_TOKEN:
        print("Please set your Home Assistant token:")
        print("export HA_TOKEN='your_home_assistant_token'")
        print("export HA_URL='http://your-homeassistant-url:8123'  # Optional")
        return
    
    tester = FeatureTester(HA_URL, HA_TOKEN)
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
