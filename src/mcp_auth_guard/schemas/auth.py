"""Authentication schemas and models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuthMethod(str, Enum):
    """Supported authentication methods."""
    JWT = "jwt"
    API_KEY = "api_key"
    HEADER_BASED = "header_based"
    NONE = "none"


class AuthConfig(BaseModel):
    """Authentication configuration."""
    method: AuthMethod = Field(..., description="Authentication method to use")
    jwt_secret: Optional[str] = Field(None, description="JWT signing secret")
    jwt_algorithm: str = Field("HS256", description="JWT algorithm")
    jwt_audience: Optional[str] = Field(None, description="Expected JWT audience")
    jwt_issuer: Optional[str] = Field(None, description="Expected JWT issuer")
    
    api_key_header: str = Field("X-API-Key", description="Header name for API key")
    api_keys: Optional[List[str]] = Field(None, description="Valid API keys")
    
    header_mapping: Optional[Dict[str, str]] = Field(
        None, 
        description="Header to attribute mapping for header-based auth"
    )
    
    required_claims: List[str] = Field(
        default_factory=list,
        description="Required JWT claims"
    )


class AuthContext(BaseModel):
    """Authentication context for a request."""
    user_id: Optional[str] = Field(None, description="Authenticated user ID")
    roles: List[str] = Field(default_factory=list, description="User roles")
    claims: Dict[str, Any] = Field(default_factory=dict, description="JWT claims or metadata")
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    authenticated: bool = Field(False, description="Whether user is authenticated")
    auth_method: Optional[AuthMethod] = Field(None, description="Method used for authentication")
