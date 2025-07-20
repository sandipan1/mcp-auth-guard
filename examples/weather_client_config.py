#!/usr/bin/env python3
"""
Example MCP configuration for connecting to the Weather MCP Server with Auth Guard.

This demonstrates how to configure MCP clients using the standard MCP config format
with environment variables for authentication and role management.
"""

import asyncio
import os
from pathlib import Path
from fastmcp import Client


def create_weather_config(role: str = "user", transport: str = "stdio", server_url: str = None) -> dict:
    """
    Create MCP configuration for weather service with authentication.
    
    Args:
        role: User role ("admin", "user", or "intern")
        transport: Transport type ("stdio", "http", "sse")
        server_url: URL for HTTP/SSE transports (required for http/sse)
        
    Returns:
        MCP configuration dictionary
    """
    # Map roles to API keys
    api_keys = {
        "admin": "demo-key-admin",
        "user": "demo-key-user", 
        "intern": "demo-key-intern"
    }
    
    if role not in api_keys:
        raise ValueError(f"Invalid role: {role}. Must be one of: {list(api_keys.keys())}")
    
    if transport.lower() == "stdio":
        # STDIO: Client launches server as subprocess
        server_script = Path(__file__).parent / "weather_server.py"
        config = {
            "mcpServers": {
                "weather_service": {
                    "transport": "stdio",
                    "command": "python",
                    "args": [str(server_script)],
                    # Environment variables for authentication
                    "env": {
                        "MCP_X_API_KEY": api_keys[role],
                        "MCP_X_USER_ROLES": role,
                        "MCP_X_USER_ID": f"user_{role}",
                        "MCP_X_AGENT_ID": f"agent_{role}",
                        "DEBUG": "true"
                    },
                    "cwd": str(Path(__file__).parent),
                    "tools": {}
                }
            }
        }
        
    elif transport.lower() == "http":
        # HTTP: Client connects to existing server
        if not server_url:
            raise ValueError("server_url is required for HTTP transport")
        config = {
            "mcpServers": {
                "weather_service": {
                    "transport": "http",
                    "url": server_url,
                    # HTTP headers for authentication
                    "headers": {
                        "X-API-Key": api_keys[role],
                        "X-User-Roles": role,
                        "X-User-ID": f"user_{role}",
                        "X-Agent-ID": f"agent_{role}",
                        "Content-Type": "application/json"
                    }
                }
            }
        }
        
    elif transport.lower() == "sse":
        # SSE: Client connects to existing server
        if not server_url:
            raise ValueError("server_url is required for SSE transport")
        config = {
            "mcpServers": {
                "weather_service": {
                    "transport": "sse",
                    "url": server_url,
                    # HTTP headers for authentication
                    "headers": {
                        "X-API-Key": api_keys[role],
                        "X-User-Roles": role,
                        "X-User-ID": f"user_{role}",
                        "X-Agent-ID": f"agent_{role}",
                        "Content-Type": "application/json"
                    }
                }
            }
        }
        
    else:
        raise ValueError(f"Unsupported transport: {transport}. Use 'stdio', 'http', or 'sse'")
    
    return config


def create_multi_role_config() -> dict:
    """
    Create MCP configuration with multiple weather servers for different roles.
    
    This allows you to connect to the same service with different authentication
    levels simultaneously.
    """
    server_script = Path(__file__).parent / "weather_server.py"
    
    config = {
        "mcpServers": {
            "weather_admin": {
                "transport": "stdio",
                "command": "python", 
                "args": [str(server_script)],
                "env": {
                    "MCP_X_API_KEY": "demo-key-admin",
                    "MCP_X_USER_ROLES": "admin",
                    "MCP_X_USER_ID": "admin_user",
                    "MCP_X_AGENT_ID": "admin_agent"
                }
            },
            "weather_user": {
                "transport": "stdio",
                "command": "python",
                "args": [str(server_script)],
                "env": {
                    "MCP_X_API_KEY": "demo-key-user", 
                    "MCP_X_USER_ROLES": "user",
                    "MCP_X_USER_ID": "regular_user",
                    "MCP_X_AGENT_ID": "user_agent"
                }
            },
            "weather_intern": {
                "transport": "stdio",
                "command": "python",
                "args": [str(server_script)],
                "env": {
                    "MCP_X_API_KEY": "demo-key-intern",
                    "MCP_X_USER_ROLES": "intern", 
                    "MCP_X_USER_ID": "intern_user",
                    "MCP_X_AGENT_ID": "intern_agent"
                }
            }
        }
    }
    
    return config


def create_production_config() -> dict:
    """
    Create production-ready MCP configuration using environment variables.
    
    This reads authentication from environment variables for security.
    """
    server_script = Path(__file__).parent / "weather_server.py"
    
    config = {
        "mcpServers": {
            "weather_service": {
                "transport": "stdio",
                "command": "python",
                "args": [str(server_script)],
                "env": {
                    # Read from environment variables
                    "MCP_X_API_KEY": os.getenv("WEATHER_API_KEY", "demo-key-user"),
                    "MCP_X_USER_ROLES": os.getenv("WEATHER_USER_ROLE", "user"),
                    "MCP_X_USER_ID": os.getenv("WEATHER_USER_ID", "default_user"),
                    "MCP_X_AGENT_ID": os.getenv("WEATHER_AGENT_ID", "default_agent"),
                    # Pass through other environment variables
                    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
                    "DEBUG": os.getenv("DEBUG", "false")
                }
            }
        }
    }
    
    return config


async def test_config_example(transport: str = "stdio", server_url: str = None):
    """Test the MCP configuration with the weather service."""
    print(f"🌍 Testing Weather Service MCP Configuration ({transport.upper()})")
    print("=" * 60)
    
    # Test different role configurations
    roles = ["admin", "user", "intern"]
    
    for role in roles:
        print(f"\n👤 Testing configuration for role: {role.upper()}")
        print("-" * 40)
        
        try:
            # Create configuration for this role
            config = create_weather_config(role, transport, server_url)
            
            # Create client with the configuration
            client = Client(config)
            
            async with client:
                # Test connectivity
                await client.ping()
                print(f"   ✅ Connected to weather service as {role}")
                
                # List available tools (namespaced by server)
                tools = await client.list_tools()
                if hasattr(tools, 'tools'):
                    tool_names = [tool.name for tool in tools.tools]
                else:
                    tool_names = [tool.name for tool in tools]
                
                print(f"   🛠️  Available tools: {tool_names}")
                
                # Try calling a tool (if any available)
                if tool_names:
                    try:
                        # Tools are prefixed with server name when using config
                        first_tool = tool_names[0]
                        if not first_tool.startswith("weather_service_"):
                            first_tool = f"weather_service_{first_tool}"
                        
                        result = await client.call_tool(first_tool, {"time": "day"})
                        print(f"   🌡️  Tool result: {result.data}")
                    except Exception as e:
                        print(f"   ⚠️  Tool call failed: {e}")
                        
        except Exception as e:
            print(f"   ❌ Failed to test {role}: {e}")
        
        await asyncio.sleep(0.1)
    
    print("\n" + "=" * 60)
    print("📋 Configuration Examples:")
    print("   • Single role: create_weather_config('admin')")
    print("   • Multi-role: create_multi_role_config()")
    print("   • Production: create_production_config()")


def print_example_configs():
    """Print example configurations for documentation."""
    print("🔧 MCP Configuration Examples for Weather Service")
    print("=" * 60)
    
    print("\n1️⃣  STDIO TRANSPORT (Client launches server):")
    print("-" * 30)
    config_stdio = create_weather_config("user", "stdio")
    import json
    print(json.dumps(config_stdio, indent=2))
    
    print("\n2️⃣  HTTP TRANSPORT (Client connects to existing server):")
    print("-" * 30)
    config_http = create_weather_config("user", "http", "http://localhost:8000/mcp")
    print(json.dumps(config_http, indent=2))
    
    print("\n3️⃣  SSE TRANSPORT (Client connects to existing server):")
    print("-" * 30)
    config_sse = create_weather_config("user", "sse", "http://localhost:8000/sse")
    print(json.dumps(config_sse, indent=2))
    
    print("\n4️⃣  MULTI-ROLE CONFIGURATION (STDIO):")
    print("-" * 30)
    multi_config = create_multi_role_config()
    print(json.dumps(multi_config, indent=2))
    
    print("\n5️⃣  PRODUCTION CONFIGURATION (Environment variables):")
    print("-" * 30)
    prod_config = create_production_config()
    print(json.dumps(prod_config, indent=2))
    
    print("\n📝 Usage Notes:")
    print("   • STDIO: Client launches server subprocess (local development)")
    print("   • HTTP/SSE: Client connects to existing server (production)")
    print("   • Available roles: admin, user, intern")
    print("   • API keys: demo-key-admin, demo-key-user, demo-key-intern")
    print("   • Tools are namespaced: weather_service_get_mars_weather")
    print("\n🚀 To start HTTP/SSE server:")
    print("   python -m fastmcp.cli run weather_server.py --transport http --port 8000")
    print("   python -m fastmcp.cli run weather_server.py --transport sse --port 8000")


async def test_production_setup():
    """Test production configuration with environment variables."""
    print("\n🏭 Testing Production Configuration")
    print("-" * 40)
    
    # Set example environment variables
    os.environ["WEATHER_API_KEY"] = "demo-key-admin"
    os.environ["WEATHER_USER_ROLE"] = "admin"
    os.environ["WEATHER_USER_ID"] = "prod_admin"
    os.environ["WEATHER_AGENT_ID"] = "prod_agent"
    
    config = create_production_config()
    client = Client(config)
    
    try:
        async with client:
            await client.ping()
            print("   ✅ Production configuration works!")
            
            tools = await client.list_tools()
            if hasattr(tools, 'tools'):
                tool_count = len(tools.tools)
            else:
                tool_count = len(tools)
            print(f"   🛠️  Found {tool_count} available tools")
            
    except Exception as e:
        print(f"   ❌ Production test failed: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # Run full test with STDIO
        asyncio.run(test_config_example())
    elif len(sys.argv) == 2:
        if sys.argv[1] == "examples":
            print_example_configs()
        elif sys.argv[1] == "production":
            asyncio.run(test_production_setup())
        elif sys.argv[1] in ["admin", "user", "intern"]:
            # Test specific role with STDIO
            config = create_weather_config(sys.argv[1], "stdio")
            print(f"STDIO Configuration for {sys.argv[1]}:")
            import json
            print(json.dumps(config, indent=2))
        elif sys.argv[1] in ["http", "sse"]:
            print(f"Usage: python weather_client_config.py {sys.argv[1]} <server_url> [role]")
        else:
            print("Usage: python weather_client_config.py [examples|production|admin|user|intern|http|sse]")
    elif len(sys.argv) == 3:
        if sys.argv[1] in ["http", "sse"]:
            # Test with HTTP/SSE and URL
            transport = sys.argv[1]
            server_url = sys.argv[2]
            asyncio.run(test_config_example(transport, server_url))
        elif sys.argv[1] in ["admin", "user", "intern"] and sys.argv[2] in ["http", "sse"]:
            print(f"Usage: python weather_client_config.py {sys.argv[1]} {sys.argv[2]} <server_url>")
        else:
            print("Usage: python weather_client_config.py [transport] <server_url> or [role] [transport] <server_url>")
    elif len(sys.argv) == 4:
        role = sys.argv[1]
        transport = sys.argv[2] 
        server_url = sys.argv[3]
        
        if role in ["admin", "user", "intern"] and transport in ["http", "sse"]:
            # Test specific role with HTTP/SSE
            config = create_weather_config(role, transport, server_url)
            print(f"{transport.upper()} Configuration for {role}:")
            import json
            print(json.dumps(config, indent=2))
        else:
            print(f"Invalid arguments: role='{role}', transport='{transport}'")
            print("Usage: python weather_client_config.py [admin|user|intern] [http|sse] <server_url>")
    else:
        print("Usage:")
        print("  python weather_client_config.py                              # Test all roles (STDIO)")
        print("  python weather_client_config.py examples                     # Show config examples")
        print("  python weather_client_config.py [admin|user|intern]          # Generate STDIO config")
        print("  python weather_client_config.py [http|sse] <url>             # Test all roles (HTTP/SSE)")
        print("  python weather_client_config.py [role] [http|sse] <url>      # Generate HTTP/SSE config")
