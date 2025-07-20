#!/usr/bin/env python3
"""
HTTP Client Role Demo for Weather MCP Server with Auth Guard.

This demonstrates how different user roles have different access levels
when connecting via HTTP transport.
"""

import asyncio
from fastmcp import Client

async def test_role(role_name: str, api_key: str):
    """Test a specific user role with HTTP transport."""
    config = {
        "mcpServers": {
            "weather_service": {
                "transport": "http",
                "url": "http://127.0.0.1:8000/mcp/",
                "headers": {
                    "X-API-Key": api_key,
                    "X-User-Roles": role_name,
                    "X-User-ID": f"demo_{role_name}",
                    "X-Agent-ID": f"client_{role_name}",
                }
            }
        }
    }
    
    client = Client(config)
    
    print(f"\n👤 Testing role: {role_name.upper()}")
    print("-" * 40)
    
    try:
        async with client:
            # List available tools
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            print(f"🛠️ Available tools: {tool_names}")
            
            # Test calling tools
            test_tools = [
                ("get_mars_weather", {"time": "day"}),
                ("get_venus_weather", {"time": "day"}), 
                ("get_jupiter_weather", {"time": "day"}),
                ("get_jupiter_weather", {"time": "night"}),
                ("get_saturn_weather", {"time": "day"}),
            ]
            
            for tool_name, args in test_tools:
                if tool_name in tool_names:
                    time_str = f" ({args['time']})" if args.get('time') != 'day' else ""
                    try:
                        result = await client.call_tool(tool_name, args)
                        print(f"   ✅ {tool_name}{time_str}: {result.data[:60]}...")
                    except Exception as e:
                        print(f"   ❌ {tool_name}{time_str}: {e}")
                        
    except Exception as e:
        print(f"❌ Connection failed for {role_name}: {e}")

async def main():
    """Test all user roles via HTTP transport."""
    print("🌐 HTTP Transport Role-Based Authorization Demo")
    print("=" * 60)
    print("🚀 Make sure the server is running: python examples/weather_server.py")
    print()
    
    # Test different roles
    roles = [
        ("admin", "demo-key-admin"),
        ("user", "demo-key-user"), 
        ("intern", "demo-key-intern"),
    ]
    
    for role_name, api_key in roles:
        await test_role(role_name, api_key)
        await asyncio.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("📋 Policy Summary:")
    print("   • Admin: Full access to all planetary weather")
    print("   • User: Mars & Venus access, Jupiter visible but not callable")
    print("   • Intern: Jupiter access only at night (safety protocol)")
    print("   • Saturn: Restricted to admins only (radiation hazard)")
    print()
    print("🔗 Transport: HTTP with header-based authentication")
    print("📜 Policies: Defined in weather_policies.yaml")

if __name__ == "__main__":
    asyncio.run(main())
