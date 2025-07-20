"""Identity manager for handling authentication."""

import logging
from typing import Dict, Optional

from ..schemas.auth import AuthConfig, AuthContext, AuthMethod
from .jwt_auth import JWTAuthenticator
from .api_key_auth import APIKeyAuthenticator
from .header_auth import HeaderAuthenticator

logger = logging.getLogger(__name__)


class IdentityManager:
    """Manages authentication for MCP requests."""
    
    def __init__(self, config: AuthConfig):
        """Initialize the identity manager with authentication config."""
        self.config = config
        self._authenticator = self._create_authenticator()
    
    def _create_authenticator(self):
        """Create the appropriate authenticator based on config."""
        if self.config.method == AuthMethod.JWT:
            return JWTAuthenticator(self.config)
        elif self.config.method == AuthMethod.API_KEY:
            return APIKeyAuthenticator(self.config)
        elif self.config.method == AuthMethod.HEADER_BASED:
            return HeaderAuthenticator(self.config)
        elif self.config.method == AuthMethod.NONE:
            return None
        else:
            raise ValueError(f"Unsupported auth method: {self.config.method}")
    
    async def authenticate(self, headers: Dict[str, str]) -> AuthContext:
        """
        Authenticate a request based on headers.
        
        Args:
            headers: HTTP headers from the request
            
        Returns:
            AuthContext with authentication information
        """
        if self._authenticator is None:
            # No authentication required
            return AuthContext(
                authenticated=True,
                auth_method=AuthMethod.NONE,
                user_id="anonymous",
                agent_id=headers.get("x-agent-id", "unknown")
            )
        
        try:
            return await self._authenticator.authenticate(headers)
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            return AuthContext(
                authenticated=False,
                auth_method=self.config.method
            )
    
    def is_authentication_required(self) -> bool:
        """Check if authentication is required."""
        return self.config.method != AuthMethod.NONE
