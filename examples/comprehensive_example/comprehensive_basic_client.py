#!/usr/bin/env python3
"""
Basic HTTP client for comprehensive MCP server.

Simple demonstration of how to connect to the comprehensive server
and test different authorization levels.
"""

import asyncio
import httpx
import json


async def test_capability(server_url: str, api_key: str, method: str, params: dict, description: str):
    """Test a single MCP capability."""
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
    
    print(f"\n🧪 {description}")
    print(f"   Method: {method}")
    print(f"   API Key: {api_key}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{server_url}/mcp", headers=headers, json=payload)
            result = response.json()
            
            if "result" in result:
                print(f"   ✅ Success!")
                if method == "tools/call":
                    content = result["result"]["content"][0]["text"]
                    print(f"   📄 Result: {content}")
                elif method == "resources/read":
                    content = result["result"]["contents"][0]["text"] if result["result"]["contents"] else "No content"
                    print(f"   📄 Content: {content}")
                elif method == "prompts/get":
                    messages = result["result"]["messages"]
                    if messages:
                        print(f"   📄 Prompt: {messages[0]['content']['text']}")
                elif "list" in method:
                    items = result["result"].get("tools", result["result"].get("resources", result["result"].get("prompts", [])))
                    names = [item.get("name", item.get("uri", "unknown")) for item in items]
                    print(f"   📋 Available: {names}")
                    
            elif "error" in result:
                error = result['error']
                error_msg = error.get('message', str(error)) if isinstance(error, dict) else str(error)
                print(f"   ❌ Access denied: {error_msg}")
            else:
                print(f"   ⚠️  Unexpected response: {result}")
                
    except Exception as e:
        print(f"   💥 Request failed: {e}")


async def demo_authorization():
    """Demonstrate authorization across different roles."""
    server_url = "http://localhost:8000"
    
    print("🔒 Basic Authorization Demo")
    print("Testing comprehensive MCP server capabilities")
    print("=" * 50)
    
    # API Keys for different roles
    api_keys = {
        "admin": "admin-key-123",
        "analyst": "analyst-key-456",
        "user": "user-key-789", 
        "public": "public-key-000"
    }
    
    print(f"\n🌐 Server URL: {server_url}")
    print(f"🔑 API Keys: {list(api_keys.keys())}")
    
    # Test scenarios
    scenarios = [
        # Tools testing
        ("admin", "tools/list", {}, "Admin listing all tools"),
        ("admin", "tools/call", {"name": "delete_user", "arguments": {"user_id": "test123"}}, "Admin deleting user (dangerous operation)"),
        
        ("user", "tools/list", {}, "User listing available tools"),
        ("user", "tools/call", {"name": "get_user_info", "arguments": {"user_id": "test123"}}, "User getting user info (allowed)"),
        ("user", "tools/call", {"name": "delete_user", "arguments": {"user_id": "test123"}}, "User trying to delete user (should fail)"),
        
        ("public", "tools/call", {"name": "public_info"}, "Public user accessing public info"),
        
        # Resources testing
        ("admin", "resources/list", {}, "Admin listing all resources"),
        ("admin", "resources/read", {"uri": "admin://system"}, "Admin reading system config"),
        
        ("analyst", "resources/read", {"uri": "api://logs"}, "Analyst reading API logs"),
        ("analyst", "resources/read", {"uri": "admin://system"}, "Analyst trying to read admin config (should fail)"),
        
        ("user", "resources/read", {"uri": "user://profile"}, "User reading own profile"),
        ("user", "resources/read", {"uri": "admin://system"}, "User trying to read admin config (should fail)"),
        
        ("public", "resources/read", {"uri": "public://docs"}, "Public user reading public docs"),
        ("public", "resources/read", {"uri": "user://profile"}, "Public user trying to read private profile (should fail)"),
        
        # Prompts testing
        ("admin", "prompts/list", {}, "Admin listing all prompts"),
        ("admin", "prompts/get", {"name": "admin_report", "arguments": {"period": "Q1", "details": "summary"}}, "Admin using admin report prompt"),
        
        ("analyst", "prompts/get", {"name": "sql_analysis", "arguments": {"sql_query": "SELECT * FROM users"}}, "Analyst using SQL analysis prompt"),
        ("analyst", "prompts/get", {"name": "admin_report", "arguments": {"period": "Q1", "details": "test"}}, "Analyst trying admin prompt (should fail)"),
        
        ("user", "prompts/get", {"name": "user_query", "arguments": {"query": "How do I reset my password?"}}, "User using general query prompt"),
        ("user", "prompts/get", {"name": "sql_analysis", "arguments": {"sql_query": "SELECT 1"}}, "User trying SQL prompt (should fail)"),
    ]
    
    # Run test scenarios
    for role, method, params, description in scenarios:
        api_key = api_keys[role]
        await test_capability(server_url, api_key, method, params, description)
        await asyncio.sleep(0.1)  # Small delay between requests
    
    print(f"\n🎯 Demo Complete!")
    print("Key takeaways:")
    print("✅ Different roles have different access levels")
    print("✅ Admin has full access to tools, resources, and prompts") 
    print("✅ Analyst has data access but no admin privileges")
    print("✅ User has basic access to own resources")
    print("✅ Public has minimal access to public resources only")
    print("✅ Unauthorized access is properly blocked")


async def interactive_test():
    """Interactive testing mode."""
    server_url = "http://localhost:8000"
    
    api_keys = {
        "admin": "admin-key-123",
        "analyst": "analyst-key-456",
        "user": "user-key-789",
        "public": "public-key-000"
    }
    
    print("🔧 Interactive MCP Test Mode")
    print("=" * 30)
    print("Available roles:", list(api_keys.keys()))
    print("Available methods: tools/list, tools/call, resources/list, resources/read, prompts/list, prompts/get")
    print("Type 'quit' to exit")
    print()
    
    while True:
        try:
            # Get role
            role = input("Enter role (admin/analyst/user/public): ").strip().lower()
            if role == "quit":
                break
            if role not in api_keys:
                print("Invalid role!")
                continue
                
            # Get method
            method = input("Enter method (e.g., tools/list, tools/call): ").strip()
            if method == "quit":
                break
                
            # Get parameters (optional)
            params_str = input("Enter params as JSON (or press Enter for {}): ").strip()
            if params_str == "quit":
                break
                
            params = {}
            if params_str:
                try:
                    params = json.loads(params_str)
                except json.JSONDecodeError:
                    print("Invalid JSON! Using empty params.")
            
            # Make the request
            api_key = api_keys[role]
            await test_capability(server_url, api_key, method, params, f"{role} calling {method}")
            print()
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            print("\nExiting...")
            break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_test())
    else:
        asyncio.run(demo_authorization())
