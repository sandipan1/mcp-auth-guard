#!/usr/bin/env python3
"""
Comprehensive MCP Server demonstrating authorization for tools, resources, and prompts.

This example shows how MCP Auth Guard can secure all three types of MCP capabilities:
- Tools: Executable functions
- Resources: Static content/data
- Prompts: AI prompt templates
"""

import asyncio
from pathlib import Path
from fastmcp import FastMCP
from mcp_auth_guard import create_api_key_middleware

# Sample resource data
RESOURCES_DATA = {
    "user://profile": "User profile information - private data",
    "public://docs": "Public documentation - anyone can read",
    "admin://system": "System configuration - admin only",
    "api://logs": "API logs - admin and analyst access"
}

# Sample prompt templates
PROMPTS_DATA = {
    "user_query": {
        "description": "General user query template",
        "template": "Please help me with: {query}",
        "arguments": ["query"]
    },
    "admin_report": {
        "description": "Administrative report template", 
        "template": "Generate admin report for {period} with details: {details}",
        "arguments": ["period", "details"]
    },
    "sql_analysis": {
        "description": "SQL query analysis template",
        "template": "Analyze this SQL query for security issues: {sql_query}",
        "arguments": ["sql_query"]
    }
}


def create_comprehensive_server() -> FastMCP:
    """Create MCP server with tools, resources, and prompts."""
    mcp = FastMCP("Comprehensive Demo Server")

    # ========== TOOLS ==========
    
    @mcp.tool()
    def get_user_info(user_id: str) -> str:
        """Get user information (requires user+ access)."""
        return f"User info for {user_id}: John Doe, Role: Developer"

    @mcp.tool()
    def delete_user(user_id: str) -> str:
        """Delete a user account (requires admin access)."""
        return f"User {user_id} has been deleted"

    @mcp.tool() 
    def query_database(sql: str) -> str:
        """Execute database query (requires analyst+ access)."""
        return f"Query result: {sql} returned 42 rows"

    @mcp.tool()
    def public_info() -> str:
        """Get public information (no auth required)."""
        return "This is public information available to everyone"

    # ========== RESOURCES ==========
    
    @mcp.resource("user://profile")
    async def user_profile_resource():
        """User profile resource (private)."""
        return RESOURCES_DATA["user://profile"]

    @mcp.resource("public://docs")
    async def public_docs_resource():
        """Public documentation resource."""
        return RESOURCES_DATA["public://docs"]

    @mcp.resource("admin://system")
    async def admin_system_resource():
        """System configuration resource (admin only)."""
        return RESOURCES_DATA["admin://system"]

    @mcp.resource("api://logs")
    async def api_logs_resource():
        """API logs resource (admin/analyst)."""
        return RESOURCES_DATA["api://logs"]

    # ========== PROMPTS ==========
    
    @mcp.prompt("user_query")
    async def user_query_prompt(query: str):
        """General user query prompt."""
        return PROMPTS_DATA["user_query"]["template"].format(query=query)

    @mcp.prompt("admin_report")
    async def admin_report_prompt(period: str, details: str):
        """Administrative report prompt (admin only)."""
        return PROMPTS_DATA["admin_report"]["template"].format(period=period, details=details)

    @mcp.prompt("sql_analysis")
    async def sql_analysis_prompt(sql_query: str):
        """SQL analysis prompt (analyst+ access)."""
        return PROMPTS_DATA["sql_analysis"]["template"].format(sql_query=sql_query)

    return mcp


def create_auth_middleware():
    """Create comprehensive authorization middleware."""
    policy_file = Path(__file__).parent / "comprehensive_policies.yaml"
    
    return create_api_key_middleware(
        policies=policy_file,
        api_key_roles={
            "admin-key-123": ["admin"],
            "analyst-key-456": ["analyst"],
            "user-key-789": ["user"],
            "public-key-000": ["public"]
        },
        enable_audit_logging=True,
    )


if __name__ == "__main__":
    """Run the comprehensive demo server."""
    
    mcp = create_comprehensive_server()
    
    # Add Auth Guard middleware
    auth_middleware = create_auth_middleware()
    mcp.add_middleware(auth_middleware)
    
    print("🔒 Comprehensive MCP Server with Auth Guard starting...")
    print("📋 Available API keys:")
    print("   - admin-key-123   (admin access - full access)")
    print("   - analyst-key-456 (analyst access - data + queries)")
    print("   - user-key-789    (user access - basic functions)")
    print("   - public-key-000  (public access - public resources only)")
    print()
    print("🛠️  Available capabilities:")
    print("   Tools: get_user_info, delete_user, query_database, public_info")
    print("   Resources: user://profile, public://docs, admin://system, api://logs")
    print("   Prompts: user_query, admin_report, sql_analysis")
    print()
    print("🔒 Policies loaded from comprehensive_policies.yaml")
    print("📡 Server running on HTTP transport")

    asyncio.run(mcp.run(transport="http"))
