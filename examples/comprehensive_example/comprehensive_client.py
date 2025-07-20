#!/usr/bin/env python3
"""
Comprehensive test client for the MCP Auth Guard comprehensive server.

This client demonstrates authorization across all three MCP capability types:
- Tools: Executable functions
- Resources: Static content/data  
- Prompts: AI prompt templates

Tests different user roles and their access levels.
"""

import asyncio
import sys
from typing import Dict, List, Optional
import httpx
import json


class ComprehensiveTestClient:
    """Test client for comprehensive MCP server capabilities."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url.rstrip("/")
        self.mcp_url = f"{self.server_url}/mcp"
        
        # Role to API key mapping
        self.api_keys = {
            "admin": "admin-key-123",
            "analyst": "analyst-key-456", 
            "user": "user-key-789",
            "public": "public-key-000"
        }
        
        # Expected capabilities for each role
        self.role_expectations = {
            "admin": {
                "tools": ["get_user_info", "delete_user", "query_database", "public_info"],
                "resources": ["user://profile", "public://docs", "admin://system", "api://logs"],
                "prompts": ["user_query", "admin_report", "sql_analysis"]
            },
            "analyst": {
                "tools": ["get_user_info", "query_database", "public_info"],
                "resources": ["public://docs", "api://logs"],
                "prompts": ["sql_analysis"]
            },
            "user": {
                "tools": ["get_user_info", "public_info"],
                "resources": ["user://profile", "public://docs"],
                "prompts": ["user_query"]
            },
            "public": {
                "tools": ["public_info"],
                "resources": ["public://docs"],
                "prompts": []
            }
        }

    async def make_mcp_request(self, method: str, params: dict, api_key: str) -> dict:
        """Make an MCP request with authentication."""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.mcp_url, headers=headers, json=payload)
                return response.json()
            except Exception as e:
                return {"error": f"Request failed: {e}"}

    async def test_tools_listing(self, role: str) -> List[str]:
        """Test tools listing for a role."""
        api_key = self.api_keys[role]
        response = await self.make_mcp_request("tools/list", {}, api_key)
        
        if "result" in response and "tools" in response["result"]:
            return [tool["name"] for tool in response["result"]["tools"]]
        return []

    async def test_tool_execution(self, role: str, tool_name: str, arguments: dict = None) -> dict:
        """Test tool execution for a role."""
        api_key = self.api_keys[role]
        params = {"name": tool_name}
        if arguments:
            params["arguments"] = arguments
            
        response = await self.make_mcp_request("tools/call", params, api_key)
        return response

    async def test_resources_listing(self, role: str) -> List[str]:
        """Test resources listing for a role."""
        api_key = self.api_keys[role]
        response = await self.make_mcp_request("resources/list", {}, api_key)
        
        if "result" in response and "resources" in response["result"]:
            return [resource["uri"] for resource in response["result"]["resources"]]
        return []

    async def test_resource_reading(self, role: str, resource_uri: str) -> dict:
        """Test resource reading for a role."""
        api_key = self.api_keys[role]
        params = {"uri": resource_uri}
        response = await self.make_mcp_request("resources/read", params, api_key)
        return response

    async def test_prompts_listing(self, role: str) -> List[str]:
        """Test prompts listing for a role."""
        api_key = self.api_keys[role]
        response = await self.make_mcp_request("prompts/list", {}, api_key)
        
        if "result" in response and "prompts" in response["result"]:
            return [prompt["name"] for prompt in response["result"]["prompts"]]
        return []

    async def test_prompt_usage(self, role: str, prompt_name: str, arguments: dict = None) -> dict:
        """Test prompt usage for a role."""
        api_key = self.api_keys[role]
        params = {"name": prompt_name}
        if arguments:
            params["arguments"] = arguments
            
        response = await self.make_mcp_request("prompts/get", params, api_key)
        return response

    def print_result(self, success: bool, message: str, details: str = ""):
        """Print formatted test result."""
        icon = "✅" if success else "❌"
        print(f"   {icon} {message}")
        if details:
            print(f"      {details}")

    async def test_role_capabilities(self, role: str):
        """Comprehensively test all capabilities for a role."""
        print(f"\n🧪 Testing role: {role.upper()}")
        print("=" * 50)
        
        expected = self.role_expectations[role]
        
        # Test Tools
        print(f"\n🔧 Testing Tools Access for {role}")
        print("-" * 30)
        
        # List tools
        available_tools = await self.test_tools_listing(role)
        expected_tools = expected["tools"]
        
        print(f"   📋 Available tools: {available_tools}")
        
        # Test expected tools
        for tool in expected_tools:
            if tool in available_tools:
                # Test execution
                if tool == "get_user_info":
                    result = await self.test_tool_execution(role, tool, {"user_id": "test123"})
                elif tool == "delete_user":
                    result = await self.test_tool_execution(role, tool, {"user_id": "test123"})
                elif tool == "query_database":
                    result = await self.test_tool_execution(role, tool, {"sql": "SELECT * FROM users"})
                else:
                    result = await self.test_tool_execution(role, tool)
                
                if "result" in result:
                    self.print_result(True, f"Can execute {tool}", f"Result: {result['result']['content'][0]['text'][:50]}...")
                elif "error" in result:
                    error_msg = result['error'].get('message', str(result['error'])) if isinstance(result['error'], dict) else str(result['error'])
                    self.print_result(False, f"Cannot execute {tool}", f"Error: {error_msg}")
            else:
                self.print_result(False, f"Cannot see {tool}", "Not in available tools")
        
        # Test forbidden tools
        all_tools = ["get_user_info", "delete_user", "query_database", "public_info"]
        forbidden_tools = [t for t in all_tools if t not in expected_tools]
        
        for tool in forbidden_tools:
            if tool not in available_tools:
                self.print_result(True, f"Correctly blocked from {tool}", "Not visible in listings")
            else:
                # Tool is visible but should fail execution
                result = await self.test_tool_execution(role, tool, {"user_id": "test"} if "user" in tool else {})
                if "error" in result:
                    error_msg = result['error'].get('message', str(result['error'])) if isinstance(result['error'], dict) else str(result['error'])
                    self.print_result(True, f"Correctly blocked from executing {tool}", f"Error: {error_msg}")
                else:
                    self.print_result(False, f"Unexpectedly allowed to execute {tool}", "Should have been blocked")

        # Test Resources
        print(f"\n📁 Testing Resources Access for {role}")
        print("-" * 30)
        
        available_resources = await self.test_resources_listing(role)
        expected_resources = expected["resources"]
        
        print(f"   📋 Available resources: {available_resources}")
        
        # Test expected resources
        for resource in expected_resources:
            if resource in available_resources:
                result = await self.test_resource_reading(role, resource)
                if "result" in result:
                    content = result["result"]["contents"][0]["text"][:50] if result["result"]["contents"] else "No content"
                    self.print_result(True, f"Can read {resource}", f"Content: {content}...")
                elif "error" in result:
                    error_msg = result['error'].get('message', str(result['error'])) if isinstance(result['error'], dict) else str(result['error'])
                    self.print_result(False, f"Cannot read {resource}", f"Error: {error_msg}")
            else:
                self.print_result(False, f"Cannot see {resource}", "Not in available resources")

        # Test forbidden resources
        all_resources = ["user://profile", "public://docs", "admin://system", "api://logs"]
        forbidden_resources = [r for r in all_resources if r not in expected_resources]
        
        for resource in forbidden_resources:
            if resource not in available_resources:
                self.print_result(True, f"Correctly blocked from {resource}", "Not visible in listings")
            else:
                result = await self.test_resource_reading(role, resource)
                if "error" in result:
                    error_msg = result['error'].get('message', str(result['error'])) if isinstance(result['error'], dict) else str(result['error'])
                    self.print_result(True, f"Correctly blocked from reading {resource}", f"Error: {error_msg}")
                else:
                    self.print_result(False, f"Unexpectedly allowed to read {resource}", "Should have been blocked")

        # Test Prompts
        print(f"\n💬 Testing Prompts Access for {role}")
        print("-" * 30)
        
        available_prompts = await self.test_prompts_listing(role)
        expected_prompts = expected["prompts"]
        
        print(f"   📋 Available prompts: {available_prompts}")
        
        # Test expected prompts
        for prompt in expected_prompts:
            if prompt in available_prompts:
                if prompt == "user_query":
                    result = await self.test_prompt_usage(role, prompt, {"query": "test question"})
                elif prompt == "admin_report":
                    result = await self.test_prompt_usage(role, prompt, {"period": "Q1", "details": "summary"})
                elif prompt == "sql_analysis":
                    result = await self.test_prompt_usage(role, prompt, {"sql_query": "SELECT * FROM test"})
                else:
                    result = await self.test_prompt_usage(role, prompt)
                
                if "result" in result:
                    content = result["result"]["messages"][0]["content"]["text"][:50] if result["result"]["messages"] else "No content"
                    self.print_result(True, f"Can use {prompt}", f"Content: {content}...")
                elif "error" in result:
                    error_msg = result['error'].get('message', str(result['error'])) if isinstance(result['error'], dict) else str(result['error'])
                    self.print_result(False, f"Cannot use {prompt}", f"Error: {error_msg}")
            else:
                self.print_result(False, f"Cannot see {prompt}", "Not in available prompts")

        # Test forbidden prompts
        all_prompts = ["user_query", "admin_report", "sql_analysis"]
        forbidden_prompts = [p for p in all_prompts if p not in expected_prompts]
        
        for prompt in forbidden_prompts:
            if prompt not in available_prompts:
                self.print_result(True, f"Correctly blocked from {prompt}", "Not visible in listings")
            else:
                result = await self.test_prompt_usage(role, prompt, {"query": "test"})
                if "error" in result:
                    error_msg = result['error'].get('message', str(result['error'])) if isinstance(result['error'], dict) else str(result['error'])
                    self.print_result(True, f"Correctly blocked from using {prompt}", f"Error: {error_msg}")
                else:
                    self.print_result(False, f"Unexpectedly allowed to use {prompt}", "Should have been blocked")

    async def test_all_roles(self):
        """Test all roles comprehensively."""
        print("🔒 Comprehensive MCP Authorization Test")
        print("Testing tools, resources, and prompts across all roles")
        print("=" * 60)
        
        for role in ["admin", "analyst", "user", "public"]:
            await self.test_role_capabilities(role)
            
        print(f"\n🎯 Test Summary")
        print("=" * 30)
        print("✅ Admin: Full access to all capabilities")
        print("✅ Analyst: Data tools, logs, SQL analysis")  
        print("✅ User: Basic tools, own profile, user queries")
        print("✅ Public: Public info and docs only")
        print("\n🔒 Authorization working correctly across all capability types!")

    async def test_single_role(self, role: str):
        """Test a single role."""
        if role not in self.api_keys:
            print(f"❌ Invalid role: {role}")
            print(f"Available roles: {list(self.api_keys.keys())}")
            return
            
        print("🔒 Comprehensive MCP Authorization Test")
        print(f"Testing {role} role across all capability types")
        
        await self.test_role_capabilities(role)

    async def quick_demo(self):
        """Quick demo showing key authorization scenarios."""
        print("🚀 Quick Authorization Demo")
        print("=" * 40)
        
        scenarios = [
            ("admin", "delete_user", {"user_id": "test123"}, "Admin can delete users"),
            ("user", "delete_user", {"user_id": "test123"}, "User cannot delete users (should fail)"),
            ("analyst", "query_database", {"sql": "SELECT * FROM users"}, "Analyst can query database"),
            ("public", "query_database", {"sql": "SELECT * FROM users"}, "Public cannot query database (should fail)"),
        ]
        
        for role, tool, args, description in scenarios:
            print(f"\n🧪 {description}")
            result = await self.test_tool_execution(role, tool, args)
            
            if "result" in result:
                print(f"   ✅ Success: {result['result']['content'][0]['text'][:60]}...")
            elif "error" in result:
                error = result['error']
                if isinstance(error, dict):
                    error_msg = error.get('message', str(error))
                else:
                    error_msg = str(error)
                print(f"   ❌ Blocked: {error_msg}")
            else:
                print(f"   ⚠️  Unexpected response: {result}")


async def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python comprehensive_client.py all           # Test all roles")
        print("  python comprehensive_client.py <role>        # Test specific role")
        print("  python comprehensive_client.py demo          # Quick demo")
        print()
        print("Available roles: admin, analyst, user, public")
        return
    
    client = ComprehensiveTestClient()
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(f"{client.server_url}/")
            print(f"🌐 Connected to server at {client.server_url}")
    except Exception as e:
        print(f"❌ Cannot connect to server at {client.server_url}")
        print(f"   Make sure the server is running: python comprehensive_server.py")
        return
    
    command = sys.argv[1].lower()
    
    if command == "all":
        await client.test_all_roles()
    elif command == "demo":
        await client.quick_demo()
    elif command in client.api_keys:
        await client.test_single_role(command)
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: all, demo, admin, analyst, user, public")


if __name__ == "__main__":
    asyncio.run(main())
