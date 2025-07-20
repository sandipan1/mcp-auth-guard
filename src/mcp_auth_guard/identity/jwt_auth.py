"""JWT-based authentication."""

import logging
from typing import Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError

from ..schemas.auth import AuthConfig, AuthContext, AuthMethod

logger = logging.getLogger(__name__)


class JWTAuthenticator:
    """Handles JWT-based authentication."""
    
    def __init__(self, config: AuthConfig):
        """Initialize JWT authenticator."""
        self.config = config
        if not config.jwt_secret:
            raise ValueError("JWT secret is required for JWT authentication")
    
    async def authenticate(self, headers: Dict[str, str]) -> AuthContext:
        """
        Authenticate using JWT token from Authorization header.
        
        Args:
            headers: HTTP headers
            
        Returns:
            AuthContext with JWT claims
        """
        auth_header = headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise ValueError("Missing or invalid Authorization header")
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Decode and verify JWT
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                audience=self.config.jwt_audience,
                issuer=self.config.jwt_issuer,
            )
            
            # Validate required claims
            for claim in self.config.required_claims:
                if claim not in payload:
                    raise ValueError(f"Missing required claim: {claim}")
            
            # Extract user information
            user_id = payload.get("sub", payload.get("user_id"))
            roles = payload.get("roles", [])
            if isinstance(roles, str):
                roles = [roles]
            
            return AuthContext(
                authenticated=True,
                auth_method=AuthMethod.JWT,
                user_id=user_id,
                roles=roles,
                claims=payload,
                agent_id=headers.get("x-agent-id", payload.get("agent_id")),
                session_id=payload.get("session_id")
            )
            
        except InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise ValueError(f"Invalid JWT token: {e}")
