"""Header-based authentication (simple extraction)."""

import logging
from typing import Dict

from ..schemas.auth import AuthConfig, AuthContext, AuthMethod

logger = logging.getLogger(__name__)


class HeaderAuthenticator:
    """Handles header-based authentication."""
    
    def __init__(self, config: AuthConfig):
        """Initialize header authenticator."""
        self.config = config
        self.header_mapping = config.header_mapping or {
            "x-user-id": "user_id",
            "x-agent-id": "agent_id", 
            "x-user-roles": "roles"
        }
    
    async def authenticate(self, headers: Dict[str, str]) -> AuthContext:
        """
        Authenticate by extracting information from headers.
        
        Args:
            headers: HTTP headers
            
        Returns:
            AuthContext with header information
        """
        # Extract mapped information
        claims = {}
        for header_name, attr_name in self.header_mapping.items():
            value = headers.get(header_name.lower())
            if value:
                claims[attr_name] = value
        
        # Parse roles if present
        roles = []
        roles_str = claims.get("roles", "")
        if roles_str:
            roles = [role.strip() for role in roles_str.split(",") if role.strip()]
        
        user_id = claims.get("user_id", "unknown")
        agent_id = claims.get("agent_id", "unknown")
        
        return AuthContext(
            authenticated=bool(user_id and user_id != "unknown"),
            auth_method=AuthMethod.HEADER_BASED,
            user_id=user_id,
            roles=roles,
            claims=claims,
            agent_id=agent_id
        )
