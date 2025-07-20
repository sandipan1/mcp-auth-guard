"""API key-based authentication."""

import logging
from typing import Dict

from ..schemas.auth import AuthConfig, AuthContext, AuthMethod

logger = logging.getLogger(__name__)


class APIKeyAuthenticator:
    """Handles API key-based authentication."""
    
    def __init__(self, config: AuthConfig):
        """Initialize API key authenticator."""
        self.config = config
        if not config.api_keys:
            raise ValueError("API keys list is required for API key authentication")
        self.valid_keys = set(config.api_keys)
    
    async def authenticate(self, headers: Dict[str, str]) -> AuthContext:
        """
        Authenticate using API key from configured header.
        
        Args:
            headers: HTTP headers
            
        Returns:
            AuthContext with API key information
        """
        api_key = headers.get(self.config.api_key_header.lower())
        if not api_key:
            raise ValueError(f"Missing {self.config.api_key_header} header")
        
        if api_key not in self.valid_keys:
            raise ValueError("Invalid API key")
        
        # Extract additional information from headers
        user_id = headers.get("x-user-id", f"api_key_user_{hash(api_key) % 10000}")
        agent_id = headers.get("x-agent-id", "api_key_agent")
        roles = headers.get("x-user-roles", "").split(",") if headers.get("x-user-roles") else ["api_user"]
        
        return AuthContext(
            authenticated=True,
            auth_method=AuthMethod.API_KEY,
            user_id=user_id,
            roles=[role.strip() for role in roles if role.strip()],
            claims={"api_key": api_key},
            agent_id=agent_id
        )
