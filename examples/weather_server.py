#!/usr/bin/env python3
"""
Weather MCP Server with Auth Guard Example

This example demonstrates how to use MCP Auth Guard middleware to secure
an MCP server with intuitive YAML policies and multiple authentication methods.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from fastmcp import FastMCP
from mcp_auth_guard import AuthGuardMiddleware
from mcp_auth_guard.middleware.utils import create_api_key_middleware
from mcp_auth_guard.policy.loader import PolicyLoader


# Weather data for different planets
WEATHER_DATA = {
    "mars": {
        "day": "Clear red skies with dust storms in the northern hemisphere. Temperature: -60°C",
        "night": "Crystal clear view of Phobos and Deimos. Temperature: -125°C"
    },
    "jupiter": {
        "day": "Massive swirling storms with 400mph winds. Great Red Spot clearly visible.",
        "night": "Lightning storms illuminate the cloud bands. Auroras visible at the poles."
    },
    "saturn": {
        "day": "Hexagonal storm at north pole, ring shadows across the surface.",
        "night": "Ring system creates beautiful shadow patterns. Titan visible as bright dot."
    },
    "venus": {
        "day": "Thick sulfuric acid clouds, surface pressure 90x Earth. Temperature: 460°C",
        "night": "Same as day - no visibility through the dense atmosphere. Temperature: 460°C"
    }
}


def create_weather_server() -> FastMCP:
    """Create a FastMCP server with weather tools."""
    mcp = FastMCP("Planetary Weather Service")
    
    @mcp.tool()
    def get_mars_weather(time: str = "day") -> str:
        """Get current weather conditions on Mars.
        
        Args:
            time: Time of day ("day" or "night")
        """
        return WEATHER_DATA["mars"].get(time, WEATHER_DATA["mars"]["day"])
    
    @mcp.tool()
    def get_jupiter_weather(time: str = "day") -> str:
        """Get current weather conditions on Jupiter.
        
        Args:
            time: Time of day ("day" or "night")
        """
        return WEATHER_DATA["jupiter"].get(time, WEATHER_DATA["jupiter"]["day"])
    
    @mcp.tool()
    def get_saturn_weather(time: str = "day") -> str:
        """Get current weather conditions on Saturn.
        
        Args:
            time: Time of day ("day" or "night")
        """
        return WEATHER_DATA["saturn"].get(time, WEATHER_DATA["saturn"]["day"])
    
    @mcp.tool()
    def get_venus_weather(time: str = "day") -> str:
        """Get current weather conditions on Venus.
        
        Args:
            time: Time of day ("day" or "night")
        """
        return WEATHER_DATA["venus"].get(time, WEATHER_DATA["venus"]["day"])
    
    return mcp


def create_auth_middleware() -> AuthGuardMiddleware:
    """Create the Auth Guard middleware with policies."""
    # Load policies from YAML file
    policy_file = Path(__file__).parent / "weather_policies.yaml"
    
    return create_api_key_middleware(
        api_keys=["demo-key-admin", "demo-key-user", "demo-key-intern"],
        policies=policy_file,
        enable_audit_logging=True
    )




if __name__ == "__main__":
    """Run the weather server with authentication."""

    mcp = create_weather_server()
    
    # Add Auth Guard middleware
    auth_middleware = create_auth_middleware()
    mcp.add_middleware(auth_middleware)
    
    print("🌍 Weather MCP Server with Auth Guard starting...")
    print("📋 Available API keys:")
    print("   - demo-key-admin (full access)")
    print("   - demo-key-user (limited access)")  
    print("   - demo-key-intern (very restricted)")
    print()
    print("🔒 Policies loaded from weather_policies.yaml")
    print("📡 Server running on stdio transport")
    
    asyncio.run(mcp.run(transport="http"))
