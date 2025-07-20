"""Utility functions for creating and configuring middleware."""

from pathlib import Path
from typing import List, Optional, Union

from .auth_guard import AuthGuardMiddleware
from ..schemas.auth import AuthConfig, AuthMethod
from ..schemas.policy import PolicyConfig
from ..policy.loader import PolicyLoader


def create_middleware(
    auth_method: AuthMethod = AuthMethod.NONE,
    policies: Optional[Union[List[PolicyConfig], str, Path]] = None,
    jwt_secret: Optional[str] = None,
    api_keys: Optional[List[str]] = None,
    enable_audit_logging: bool = True,
    **kwargs
) -> AuthGuardMiddleware:
    """
    Create an AuthGuardMiddleware with simplified configuration.
    
    Args:
        auth_method: Authentication method to use
        policies: Policy configurations, file path, or directory path
        jwt_secret: JWT secret for JWT authentication
        api_keys: List of valid API keys for API key authentication
        enable_audit_logging: Whether to enable audit logging
        **kwargs: Additional AuthConfig parameters
        
    Returns:
        Configured AuthGuardMiddleware instance
    """
    # Create auth config
    auth_config = AuthConfig(
        method=auth_method,
        jwt_secret=jwt_secret,
        api_keys=api_keys,
        **kwargs
    )
    
    return AuthGuardMiddleware(
        auth_config=auth_config,
        policies=policies,
        enable_audit_logging=enable_audit_logging
    )


def create_jwt_middleware(
    jwt_secret: str,
    policies: Union[List[PolicyConfig], str, Path],
    jwt_algorithm: str = "HS256",
    jwt_audience: Optional[str] = None,
    jwt_issuer: Optional[str] = None,
    required_claims: Optional[List[str]] = None,
    **kwargs
) -> AuthGuardMiddleware:
    """
    Create middleware with JWT authentication.
    
    Args:
        jwt_secret: JWT signing secret
        policies: Policy configurations
        jwt_algorithm: JWT algorithm (default: HS256)
        jwt_audience: Expected JWT audience
        jwt_issuer: Expected JWT issuer
        required_claims: Required JWT claims
        **kwargs: Additional configuration
        
    Returns:
        AuthGuardMiddleware with JWT auth
    """
    return create_middleware(
        auth_method=AuthMethod.JWT,
        policies=policies,
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm,
        jwt_audience=jwt_audience,
        jwt_issuer=jwt_issuer,
        required_claims=required_claims or [],
        **kwargs
    )


def create_api_key_middleware(
    api_keys: List[str],
    policies: Union[List[PolicyConfig], str, Path],
    api_key_header: str = "X-API-Key",
    **kwargs
) -> AuthGuardMiddleware:
    """
    Create middleware with API key authentication.
    
    Args:
        api_keys: List of valid API keys
        policies: Policy configurations
        api_key_header: Header name for API key
        **kwargs: Additional configuration
        
    Returns:
        AuthGuardMiddleware with API key auth
    """
    return create_middleware(
        auth_method=AuthMethod.API_KEY,
        policies=policies,
        api_keys=api_keys,
        api_key_header=api_key_header,
        **kwargs
    )


def create_header_middleware(
    policies: Union[List[PolicyConfig], str, Path],
    header_mapping: Optional[dict] = None,
    **kwargs
) -> AuthGuardMiddleware:
    """
    Create middleware with header-based authentication.
    
    Args:
        policies: Policy configurations
        header_mapping: Header to attribute mapping
        **kwargs: Additional configuration
        
    Returns:
        AuthGuardMiddleware with header-based auth
    """
    return create_middleware(
        auth_method=AuthMethod.HEADER_BASED,
        policies=policies,
        header_mapping=header_mapping,
        **kwargs
    )


def create_no_auth_middleware(
    policies: Union[List[PolicyConfig], str, Path],
    **kwargs
) -> AuthGuardMiddleware:
    """
    Create middleware with no authentication (policy-only).
    
    Args:
        policies: Policy configurations
        **kwargs: Additional configuration
        
    Returns:
        AuthGuardMiddleware with no authentication
    """
    return create_middleware(
        auth_method=AuthMethod.NONE,
        policies=policies,
        **kwargs
    )


def load_policies_from_yaml(file_or_dir: Union[str, Path]) -> List[PolicyConfig]:
    """
    Load policies from YAML file or directory.
    
    Args:
        file_or_dir: Path to YAML file or directory containing YAML files
        
    Returns:
        List of PolicyConfig objects
    """
    path = Path(file_or_dir)
    
    if path.is_file():
        return [PolicyLoader.load_from_file(path)]
    elif path.is_dir():
        return PolicyLoader.load_from_directory(path)
    else:
        raise ValueError(f"Path does not exist: {path}")
