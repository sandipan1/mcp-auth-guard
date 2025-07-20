"""
MCP Auth Guard: Intuitive authorization middleware for MCP tools.

A modern, type-safe authorization system designed specifically for Model Context 
Protocol (MCP) servers with seamless FastMCP integration.
"""

from .middleware import AuthGuardMiddleware
from .middleware.utils import (
    create_api_key_middleware,
    create_jwt_middleware, 
    create_header_middleware,
    create_no_auth_middleware
)
from .policy import PolicyEngine, PolicyBuilder
from .identity import IdentityManager
from .schemas import PolicyConfig, AuthConfig, ToolResource
from .schemas.auth import AuthMethod

__version__ = "1.0.0"
__all__ = [
    "AuthGuardMiddleware",
    "create_api_key_middleware",
    "create_jwt_middleware",
    "create_header_middleware", 
    "create_no_auth_middleware",
    "PolicyEngine", 
    "PolicyBuilder",
    "IdentityManager",
    "AuthMethod",
    "PolicyConfig",
    "AuthConfig", 
    "ToolResource",
]
