#!/usr/bin/env python3
"""
HTTP Client Example for Weather MCP Server with Auth Guard.

This demonstrates how to connect to the weather server using HTTP transport
with proper authentication headers and MCP configuration format.
"""

import asyncio
from fastmcp import Client

# MCP configuration for HTTP transport with authentication
config = {
    "mcpServers": {
        "weather_service": {
            "transport": "http",
            "url": "http://127.0.0.1:8000/mcp/",
            "headers": {
                "X-API-Key": "demo-key-admin",
                "X-User-Roles": "admin", 
                "X-User-ID": "prod_user",
                "X-Agent-ID": "prod_agent",
            }
        }
    }
}

client = Client(config,)

async def main():
    try:
        async with client:
            print("✅ Connected to HTTP server!")
            
            # List available tools
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            print(f"🛠️ Available tools: {tool_names}")
                
            # Try calling Mars weather
            if "get_mars_weather" in tool_names:
                result = await client.call_tool("get_mars_weather", {"time": "day"})
                print(f"🌡️ Mars weather: {result.data}")
            else:
                print("❌ Mars weather tool not available for this user role")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 To fix this:")
        print("1. Start the HTTP server in another terminal:")
        print("   cd mcp-auth-guard") 
        print("   python examples/weather_server.py")
        print("2. Then run this client script")
        print("3. Try different roles by changing X-User-Roles header:")
        print("   - admin: Full access to all tools")
        print("   - user: Limited access (Mars, Venus)")
        print("   - intern: Jupiter only at night")

if __name__ == "__main__":
    asyncio.run(main())