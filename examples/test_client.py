#!/usr/bin/env python3
"""
Test client for the Weather MCP Server with Auth Guard.

This script demonstrates how different authentication levels access different tools.
"""

import asyncio
import json
import subprocess
import time
from typing import Dict, Any

import httpx


class MCPTestClient:
    """Simple test client for MCP servers."""
    
    def __init__(self, api_key: str, role: str):
        """Initialize test client with API key and role."""
        self.api_key = api_key
        self.role = role
        self.headers = {
            "X-API-Key": api_key,
            "X-User-Roles": role,
            "X-User-ID": f"test_user_{role}",
            "X-Agent-ID": f"test_agent_{role}",
            "Content-Type": "application/json"
        }
    
    async def test_list_tools(self) -> Dict[str, Any]:
        """Test listing available tools."""
        print(f"\n🔍 [{self.role.upper()}] Testing tool listing...")
        
        # For this demo, we'll simulate the MCP call
        # In a real scenario, you'd use the MCP client library
        
        print(f"   Using API key: {self.api_key}")
        print(f"   User role: {self.role}")
        
        # Simulate what tools would be visible based on policies
        if self.role == "admin":
            tools = ["get_mars_weather", "get_jupiter_weather", "get_saturn_weather", "get_venus_weather"]
        elif self.role == "user":
            tools = ["get_mars_weather", "get_venus_weather", "get_jupiter_weather"]  # Can list but not call Jupiter
        elif self.role == "intern":
            tools = ["get_jupiter_weather"]  # Can only list Jupiter
        else:
            tools = []
        
        print(f"   ✅ Visible tools: {tools}")
        return {"tools": tools}
    
    async def test_call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Test calling a specific tool."""
        print(f"\n🛠️  [{self.role.upper()}] Testing tool call: {tool_name}")
        print(f"   Arguments: {kwargs}")
        
        # Simulate authorization check based on policies
        success = False
        message = ""
        
        if self.role == "admin":
            # Admins can call everything
            success = True
            message = f"Admin access granted to {tool_name}"
        
        elif self.role == "user":
            # Users can call Mars and Venus
            if tool_name in ["get_mars_weather", "get_venus_weather"]:
                success = True
                message = f"User access granted to {tool_name}"
            else:
                success = False
                message = f"User access denied to {tool_name}"
        
        elif self.role == "intern":
            # Interns can only call Jupiter at night
            if tool_name == "get_jupiter_weather" and kwargs.get("time") == "night":
                success = True
                message = f"Intern access granted to {tool_name} at night"
            else:
                success = False
                message = f"Intern access denied to {tool_name} (wrong conditions)"
        
        if success:
            print(f"   ✅ {message}")
            # Simulate successful weather response
            return {
                "success": True,
                "result": f"Weather data for {tool_name} with args {kwargs}",
                "message": message
            }
        else:
            print(f"   ❌ {message}")
            return {
                "success": False,
                "error": "Access denied",
                "message": message
            }


async def run_tests():
    """Run comprehensive tests for different user roles."""
    print("🚀 MCP Auth Guard Demo - Weather Service Testing")
    print("=" * 60)
    
    # Test clients for different roles
    test_users = [
        ("demo-key-admin", "admin"),
        ("demo-key-user", "user"),
        ("demo-key-intern", "intern"),
    ]
    
    for api_key, role in test_users:
        print(f"\n👤 Testing as: {role.upper()}")
        print("-" * 40)
        
        client = MCPTestClient(api_key, role)
        
        # Test tool listing
        await client.test_list_tools()
        
        # Test various tool calls
        test_cases = [
            ("get_mars_weather", {"time": "day"}),
            ("get_venus_weather", {"time": "night"}),
            ("get_jupiter_weather", {"time": "day"}),
            ("get_jupiter_weather", {"time": "night"}),
            ("get_saturn_weather", {"time": "day"}),
        ]
        
        for tool_name, args in test_cases:
            await client.test_call_tool(tool_name, **args)
            time.sleep(0.1)  # Small delay for readability
    
    print("\n" + "=" * 60)
    print("🎯 Key Policy Demonstrations:")
    print("   • Admins: Full access to all tools")
    print("   • Users: Can access Mars/Venus, list Jupiter but not call it")
    print("   • Interns: Can only call Jupiter weather at night")
    print("   • Saturn: Blocked for non-admins (safety policy)")
    print("\n📝 Check the weather_policies.yaml file to see how these rules are defined!")


if __name__ == "__main__":
    asyncio.run(run_tests())
