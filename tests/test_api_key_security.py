"""Tests for API key security and role validation."""

import pytest
from mcp_auth_guard.identity.api_key_auth import APIKeyAuthenticator
from mcp_auth_guard.schemas.auth import AuthConfig, AuthMethod


@pytest.fixture
def secure_config():
    """Config with API key to role mapping."""
    return AuthConfig(
        method=AuthMethod.API_KEY,
        api_keys=["admin-key", "user-key", "intern-key"],
        api_key_roles={
            "admin-key": ["admin"],
            "user-key": ["user"],
            "intern-key": ["intern"]
        }
    )


@pytest.fixture
def insecure_config():
    """Config without role mapping (insecure fallback)."""
    return AuthConfig(
        method=AuthMethod.API_KEY,
        api_keys=["test-key"]
    )


class TestAPIKeyRoleSecurity:
    """Test API key role security."""

    @pytest.mark.asyncio
    async def test_secure_role_mapping(self, secure_config):
        """Test that roles come from config mapping, not headers."""
        auth = APIKeyAuthenticator(secure_config)
        
        # Admin key gets admin role regardless of header
        headers = {
            "x-api-key": "admin-key",
            "x-user-roles": "user,intern"  # Try to claim lower roles
        }
        context = await auth.authenticate(headers)
        assert context.roles == ["admin"]
        
        # User key gets user role regardless of header
        headers = {
            "x-api-key": "user-key", 
            "x-user-roles": "admin"  # Try to escalate privileges
        }
        context = await auth.authenticate(headers)
        assert context.roles == ["user"]

    @pytest.mark.asyncio
    async def test_privilege_escalation_blocked(self, secure_config):
        """Test that privilege escalation via headers is blocked."""
        auth = APIKeyAuthenticator(secure_config)
        
        # Intern tries to claim admin role via header
        headers = {
            "x-api-key": "intern-key",
            "x-user-roles": "admin,user"  # Privilege escalation attempt
        }
        context = await auth.authenticate(headers)
        
        # Should only get intern role, not admin
        assert context.roles == ["intern"]
        assert "admin" not in context.roles
        assert "user" not in context.roles

    @pytest.mark.asyncio
    async def test_fallback_to_default_role(self, insecure_config):
        """Test fallback when no role mapping exists."""
        auth = APIKeyAuthenticator(insecure_config)
        
        headers = {
            "x-api-key": "test-key",
            "x-user-roles": "admin"  # Header ignored without mapping
        }
        context = await auth.authenticate(headers)
        
        # Should get default role, not header role
        assert context.roles == ["api_user"]

    @pytest.mark.asyncio
    async def test_unmapped_key_gets_default(self, secure_config):
        """Test that keys not in mapping get default role."""
        # Add an unmapped key to valid keys
        secure_config.api_keys.append("unmapped-key")
        auth = APIKeyAuthenticator(secure_config)
        
        headers = {
            "x-api-key": "unmapped-key",
            "x-user-roles": "admin"  # Try to escalate
        }
        context = await auth.authenticate(headers)
        
        # Should get default role since key not in mapping
        assert context.roles == ["api_user"]

    @pytest.mark.asyncio
    async def test_multiple_roles_per_key(self):
        """Test that API keys can have multiple roles."""
        config = AuthConfig(
            method=AuthMethod.API_KEY,
            api_keys=["multi-role-key"],
            api_key_roles={
                "multi-role-key": ["user", "moderator", "analyst"]
            }
        )
        auth = APIKeyAuthenticator(config)
        
        headers = {"x-api-key": "multi-role-key"}
        context = await auth.authenticate(headers)
        
        assert set(context.roles) == {"user", "moderator", "analyst"}
