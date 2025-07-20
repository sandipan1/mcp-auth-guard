#!/usr/bin/env python3
"""
Real test client for the Weather MCP Server with Auth Guard.

This script uses the actual FastMCP Client to connect to and test the weather server
with different authentication levels and policies.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

from fastmcp import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport, SSETransport


class WeatherMCPTestClient:
    """Real MCP test client using FastMCP Client with configurable transport."""
    
    def __init__(self, api_key: str, role: str, transport_type: str = "stdio", server_url: str = None):
        """Initialize test client with API key and role.
        
        Args:
            api_key: API key for authentication
            role: User role (admin, user, intern)
            transport_type: Transport type ("stdio", "http", "sse")
            server_url: URL for HTTP/SSE transports (e.g., "https://api.example.com/mcp")
        """
        self.api_key = api_key
        self.role = role
        self.transport_type = transport_type.lower()
        self.server_url = server_url
        self.server_script = Path(__file__).parent / "weather_server.py"
        
        # Set up environment variables for STDIO transport
        # These environment variables are converted to headers by FastMCP
        self.server_env = {
            "MCP_X_API_KEY": api_key,
            "MCP_X_USER_ROLES": role,
            "MCP_X_USER_ID": f"test_user_{role}",
            "MCP_X_AGENT_ID": f"test_agent_{role}",
        }
        
        # Set up HTTP headers for HTTP/SSE transports
        self.http_headers = {
            "X-API-Key": api_key,
            "X-User-Roles": role,
            "X-User-ID": f"test_user_{role}",
            "X-Agent-ID": f"test_agent_{role}",
            "Content-Type": "application/json"
        }
    
    async def create_client(self) -> Client:
        """Create a FastMCP client connected to the weather server."""
        if self.transport_type == "stdio":
            # STDIO transport: pass auth via environment variables
            transport = StdioTransport(
                command="python",
                args=[str(self.server_script)],
                env=self.server_env
            )
            return Client(transport)
            
        elif self.transport_type == "http":
            # HTTP transport: pass auth via HTTP headers
            if not self.server_url:
                raise ValueError("server_url is required for HTTP transport")
            transport = StreamableHttpTransport(
                url=self.server_url,
                headers=self.http_headers
            )
            return Client(transport)
            
        elif self.transport_type == "sse":
            # SSE transport: pass auth via HTTP headers
            if not self.server_url:
                raise ValueError("server_url is required for SSE transport")
            transport = SSETransport(
                url=self.server_url,
                headers=self.http_headers
            )
            return Client(transport)
            
        else:
            raise ValueError(f"Unsupported transport type: {self.transport_type}. Use 'stdio', 'http', or 'sse'")
    
    async def test_list_tools(self, client: Client) -> List[Dict[str, Any]]:
        """Test listing available tools."""
        print(f"\n🔍 [{self.role.upper()}] Testing tool listing...")
        print(f"   Transport: {self.transport_type}")
        print(f"   Using API key: {self.api_key}")
        print(f"   User role: {self.role}")
        if self.server_url:
            print(f"   Server URL: {self.server_url}")
        
        try:
            tools_response = await client.list_tools()
            # Handle both list and ListToolsResult formats
            if hasattr(tools_response, 'tools'):
                tools = [tool.name for tool in tools_response.tools]
            else:
                tools = [tool.name for tool in tools_response]
            print(f"   ✅ Visible tools: {tools}")
            return tools
        except Exception as e:
            print(f"   ❌ Error listing tools: {e}")
            return []
    
    async def test_call_tool(self, client: Client, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Test calling a specific tool."""
        print(f"\n🛠️  [{self.role.upper()}] Testing tool call: {tool_name}")
        print(f"   Arguments: {kwargs}")
        
        try:
            result = await client.call_tool(tool_name, kwargs)
            print(f"   ✅ Success: {result.data}")
            return {
                "success": True,
                "result": result.data,
                "message": f"Tool {tool_name} executed successfully"
            }
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Tool {tool_name} failed"
            }
    
    async def test_server_ping(self, client: Client) -> bool:
        """Test server connectivity."""
        print(f"\n📡 [{self.role.upper()}] Testing server connectivity...")
        
        try:
            await client.ping()
            print(f"   ✅ Server is reachable")
            return True
        except Exception as e:
            print(f"   ❌ Server ping failed: {e}")
            return False


async def run_comprehensive_tests(transport_type: str = "stdio", server_url: str = None):
    """Run comprehensive tests for different user roles using real MCP client."""
    print(f"🚀 Real MCP Auth Guard Demo - Weather Service Testing ({transport_type.upper()})")
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
        
        test_client = WeatherMCPTestClient(api_key, role, transport_type, server_url)
        
        try:
            client = await test_client.create_client()
            
            async with client:
                # Test server connectivity
                if not await test_client.test_server_ping(client):
                    print(f"   ⚠️  Skipping tests for {role} - server unreachable")
                    continue
                
                # Test tool listing
                available_tools = await test_client.test_list_tools(client)
                
                # Test various tool calls
                test_cases = [
                    ("get_mars_weather", {"time": "day"}),
                    ("get_venus_weather", {"time": "night"}),
                    ("get_jupiter_weather", {"time": "day"}),
                    ("get_jupiter_weather", {"time": "night"}),
                    ("get_saturn_weather", {"time": "day"}),
                ]
                
                for tool_name, args in test_cases:
                    # Only test tools that are available to this role
                    if tool_name in available_tools:
                        await test_client.test_call_tool(client, tool_name, **args)
                    else:
                        print(f"\n🛠️  [{role.upper()}] Skipping {tool_name} - not in available tools")
                    
                    await asyncio.sleep(0.1)  # Small delay for readability
        
        except Exception as e:
            print(f"   ❌ Failed to create client for {role}: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Key Policy Demonstrations:")
    print("   • Admins: Full access to all tools")
    print("   • Users: Can access Mars/Venus, limited Jupiter access")
    print("   • Interns: Can only call Jupiter weather under specific conditions")
    print("   • Saturn: Blocked for non-admins (safety policy)")
    print("\n📝 Check the weather_policies.yaml file to see how these rules are defined!")


async def test_single_role(role: str = "admin", transport_type: str = "stdio", server_url: str = None):
    """Test a single role for debugging purposes."""
    api_keys = {
        "admin": "demo-key-admin",
        "user": "demo-key-user", 
        "intern": "demo-key-intern"
    }
    
    if role not in api_keys:
        print(f"Unknown role: {role}. Available: {list(api_keys.keys())}")
        return
    
    api_key = api_keys[role]
    test_client = WeatherMCPTestClient(api_key, role, transport_type, server_url)
    
    print(f"🧪 Testing single role: {role.upper()}")
    print("-" * 30)
    
    try:
        client = await test_client.create_client()
        
        async with client:
            # Test connectivity
            await test_client.test_server_ping(client)
            
            # List tools
            tools = await test_client.test_list_tools(client)
            
            # Test one tool call
            if tools:
                await test_client.test_call_tool(client, tools[0], time="day")
    
    except Exception as e:
        print(f"❌ Error testing {role}: {e}")


async def test_http_example():
    """Example test using HTTP transport."""
    print("📡 Testing HTTP Transport Example")
    print("-" * 40)
    
    # Example usage with HTTP transport
    # Note: You would need a running HTTP server for this to work
    server_url = "https://api.example.com/mcp"  # Replace with actual server URL
    
    test_client = WeatherMCPTestClient(
        api_key="demo-key-admin",
        role="admin", 
        transport_type="http",
        server_url=server_url
    )
    
    print(f"📋 HTTP Transport Configuration:")
    print(f"   • URL: {server_url}")
    print(f"   • Headers: {test_client.http_headers}")
    print(f"   • Authentication: X-API-Key header")
    
    # Note: This would fail unless there's actually a server running
    # It's here to show the configuration pattern


async def test_sse_example():
    """Example test using SSE transport."""
    print("📡 Testing SSE Transport Example")
    print("-" * 40)
    
    # Example usage with SSE transport
    # Note: You would need a running SSE server for this to work
    server_url = "https://api.example.com/sse"  # Replace with actual server URL
    
    test_client = WeatherMCPTestClient(
        api_key="demo-key-user",
        role="user",
        transport_type="sse", 
        server_url=server_url
    )
    
    print(f"📋 SSE Transport Configuration:")
    print(f"   • URL: {server_url}")
    print(f"   • Headers: {test_client.http_headers}")
    print(f"   • Authentication: X-API-Key header")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Run comprehensive tests with STDIO
        asyncio.run(run_comprehensive_tests())
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg in ["admin", "user", "intern"]:
            # Test single role with STDIO
            asyncio.run(test_single_role(arg))
        elif arg == "http":
            # Show HTTP transport example
            asyncio.run(test_http_example())
        elif arg == "sse":
            # Show SSE transport example
            asyncio.run(test_sse_example())
        else:
            print("Usage: python real_test_client.py [admin|user|intern|http|sse] [server_url]")
    elif len(sys.argv) == 3:
        role_or_transport = sys.argv[1]
        url_or_transport = sys.argv[2]
        
        if role_or_transport in ["admin", "user", "intern"] and url_or_transport in ["http", "sse"]:
            print(f"Usage: python real_test_client.py {role_or_transport} {url_or_transport} <server_url>")
        elif role_or_transport in ["http", "sse"]:
            # Test with HTTP/SSE transport
            server_url = url_or_transport
            asyncio.run(run_comprehensive_tests(role_or_transport, server_url))
        else:
            print("Usage: python real_test_client.py [admin|user|intern] [http|sse] <server_url>")
    elif len(sys.argv) == 4:
        role = sys.argv[1]
        transport_type = sys.argv[2] 
        server_url = sys.argv[3]
        
        if role in ["admin", "user", "intern"] and transport_type in ["http", "sse"]:
            # Test specific role with HTTP/SSE transport
            asyncio.run(test_single_role(role, transport_type, server_url))
        else:
            print("Usage: python real_test_client.py [admin|user|intern] [http|sse] <server_url>")
    else:
        print("Usage:")
        print("  python real_test_client.py                           # Test all roles with STDIO")
        print("  python real_test_client.py [admin|user|intern]       # Test single role with STDIO")
        print("  python real_test_client.py [http|sse] <server_url>   # Test all roles with HTTP/SSE")
        print("  python real_test_client.py [role] [http|sse] <url>   # Test single role with HTTP/SSE")
