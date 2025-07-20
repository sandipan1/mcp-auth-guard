"""Main authorization middleware for FastMCP servers."""

import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
from mcp import types

from ..identity import IdentityManager
from ..policy import PolicyEngine, PolicyLoader
from ..schemas.auth import AuthConfig, AuthMethod
from ..schemas.policy import PolicyConfig
from ..schemas.resource import ToolResource, ResourceContext
from ..schemas.response import DecisionReason

logger = logging.getLogger(__name__)


class AuthGuardMiddleware(Middleware):
    """
    Main authorization middleware for MCP servers.
    
    Provides comprehensive authorization with:
    - Multiple authentication methods (JWT, API key, header-based)
    - YAML-based policy configuration
    - Type-safe policy building
    - Real-time policy evaluation
    - Audit logging
    """
    
    def __init__(
        self,
        auth_config: Optional[AuthConfig] = None,
        policies: Optional[Union[List[PolicyConfig], str, Path]] = None,
        enable_audit_logging: bool = True,
    ):
        """
        Initialize the Auth Guard middleware.
        
        Args:
            auth_config: Authentication configuration. If None, uses no auth.
            policies: Policy configurations, file path, or directory path
            enable_audit_logging: Whether to enable audit logging
        """
        # Set up authentication
        self.auth_config = auth_config or AuthConfig(method=AuthMethod.NONE)
        self.identity_manager = IdentityManager(self.auth_config)
        
        # Load policies
        self.policies = self._load_policies(policies or [])
        self.policy_engine = PolicyEngine(self.policies)
        
        # Configuration
        self.enable_audit_logging = enable_audit_logging
        
        logger.info(
            f"Auth Guard middleware initialized with {len(self.policies)} policies, "
            f"auth method: {self.auth_config.method}"
        )
    
    def _load_policies(
        self, 
        policies: Union[List[PolicyConfig], str, Path]
    ) -> List[PolicyConfig]:
        """Load policies from various sources."""
        if isinstance(policies, (str, Path)):
            path = Path(policies)
            if path.is_file():
                return [PolicyLoader.load_from_file(path)]
            elif path.is_dir():
                return PolicyLoader.load_from_directory(path)
            else:
                raise ValueError(f"Policy path does not exist: {path}")
        elif isinstance(policies, list):
            return policies
        else:
            raise ValueError("Policies must be a list, file path, or directory path")
    
    async def _authenticate_request(self) -> tuple:
        """Authenticate the current request."""
        headers = get_http_headers()
        
        # Convert headers to lowercase for case-insensitive lookup
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        auth_context = await self.identity_manager.authenticate(headers_lower)
        
        if self.enable_audit_logging:
            if auth_context.authenticated:
                logger.info(
                    f"Authenticated user: {auth_context.user_id} "
                    f"(method: {auth_context.auth_method})"
                )
            else:
                logger.warning(f"Authentication failed for request")
        
        return auth_context, headers_lower
    
    def _extract_tool_resource(self, context: MiddlewareContext, component) -> ToolResource:
        """Extract tool resource information from MCP context."""
        # Get tool arguments if available
        arguments = {}
        if hasattr(context.message, 'arguments') and context.message.arguments:
            arguments = context.message.arguments
        
        # Extract namespace from component if available
        namespace = getattr(component, 'namespace', None)
        version = getattr(component, 'version', None)
        description = getattr(component, 'description', None)
        tags = getattr(component, 'tags', [])
        
        return ToolResource(
            name=component.name,
            namespace=namespace,
            version=version,
            description=description,
            tags=tags,
            arguments=arguments,
            metadata={}
        )
    
    def _create_resource_context(
        self, 
        context: MiddlewareContext, 
        component,
        action: str
    ) -> ResourceContext:
        """Create resource context for authorization."""
        tool_resource = self._extract_tool_resource(context, component)
        
        # Determine resource type from method
        method_parts = context.method.split("/")
        resource_type = method_parts[0] if method_parts else "unknown"
        
        # Handle timestamp conversion from datetime to float
        timestamp = getattr(context, 'timestamp', None)
        if timestamp is not None and hasattr(timestamp, 'timestamp'):
            # Convert datetime to float timestamp
            timestamp = timestamp.timestamp()
        
        return ResourceContext(
            resource_type=resource_type,
            resource=tool_resource,
            action=action,
            method=context.method,
            request_id=getattr(context, 'request_id', None),
            timestamp=timestamp
        )
    
    async def _authorize_request(
        self, 
        context: MiddlewareContext, 
        component,
        action: str
    ):
        """Authorize a request and raise error if denied."""
        auth_context, headers = await self._authenticate_request()
        resource_context = self._create_resource_context(context, component, action)
        
        # Evaluate authorization
        decision = await self.policy_engine.evaluate(auth_context, resource_context)
        
        # Log the decision
        if self.enable_audit_logging:
            log_msg = (
                f"Authorization {('ALLOWED' if decision.allowed else 'DENIED')} - "
                f"User: {auth_context.user_id}, Tool: {component.name}, "
                f"Action: {action}, Reason: {decision.reason}"
            )
            
            if decision.matched_rule:
                log_msg += f", Rule: {decision.matched_rule}"
            
            if decision.allowed:
                logger.info(log_msg)
            else:
                logger.warning(log_msg)
        
        # Raise error if access denied
        if not decision.allowed:
            error_msg = decision.message or f"Access denied: {decision.reason}"
            raise ToolError(error_msg)
    
    async def _filter_components(
        self,
        context: MiddlewareContext,
        components: List,
        action: str
    ) -> List:
        """Filter components based on authorization."""
        if not components:
            return []
        
        auth_context, headers = await self._authenticate_request()
        authorized_components = []
        
        for component in components:
            try:
                resource_context = self._create_resource_context(context, component, action)
                decision = await self.policy_engine.evaluate(auth_context, resource_context)
                
                if decision.allowed:
                    authorized_components.append(component)
                
                if self.enable_audit_logging:
                    result = "ALLOWED" if decision.allowed else "FILTERED"
                    logger.debug(
                        f"Component {result} - Tool: {component.name}, "
                        f"User: {auth_context.user_id}, Reason: {decision.reason}"
                    )
                    
            except Exception as e:
                logger.error(f"Error evaluating component {component.name}: {e}")
                # Exclude component on error (fail secure)
        
        return authorized_components
    
    # FastMCP middleware hooks
    
    async def on_call_tool(
        self,
        context: MiddlewareContext[types.CallToolRequestParams],
        call_next: CallNext[types.CallToolRequestParams, types.CallToolResult],
    ) -> types.CallToolResult:
        """Authorize tool execution."""
        tool = await context.fastmcp_context.fastmcp.get_tool(context.message.name)
        await self._authorize_request(context, tool, "call")
        return await call_next(context)
    
    async def on_read_resource(
        self,
        context: MiddlewareContext[types.ReadResourceRequestParams],
        call_next: CallNext[types.ReadResourceRequestParams, types.ReadResourceResult],
    ) -> types.ReadResourceResult:
        """Authorize resource reading."""
        resource = await context.fastmcp_context.fastmcp.get_resource(context.message.uri)
        await self._authorize_request(context, resource, "read")
        return await call_next(context)
    
    async def on_get_prompt(
        self,
        context: MiddlewareContext[types.GetPromptRequestParams],
        call_next: CallNext[types.GetPromptRequestParams, types.GetPromptResult],
    ) -> types.GetPromptResult:
        """Authorize prompt access."""
        prompt = await context.fastmcp_context.fastmcp.get_prompt(context.message.name)
        await self._authorize_request(context, prompt, "get")
        return await call_next(context)
    
    async def on_list_tools(
        self,
        context: MiddlewareContext[types.ListToolsRequest],
        call_next: CallNext[types.ListToolsRequest, list],
    ) -> list:
        """Filter tools based on authorization."""
        tools = await call_next(context)
        return await self._filter_components(context, tools, "list")
    
    async def on_list_resources(
        self,
        context: MiddlewareContext[types.ListResourcesRequest],
        call_next: CallNext[types.ListResourcesRequest, list],
    ) -> list:
        """Filter resources based on authorization."""
        resources = await call_next(context)
        return await self._filter_components(context, resources, "list")
    
    async def on_list_prompts(
        self,
        context: MiddlewareContext[types.ListPromptsRequest],
        call_next: CallNext[types.ListPromptsRequest, list],
    ) -> list:
        """Filter prompts based on authorization."""
        prompts = await call_next(context)
        return await self._filter_components(context, prompts, "list")
    
    # Management methods
    
    def add_policy(self, policy: PolicyConfig):
        """Add a new policy at runtime."""
        self.policies.append(policy)
        self.policy_engine.add_policy(policy)
        logger.info(f"Added policy: {policy.name}")
    
    def remove_policy(self, policy_name: str) -> bool:
        """Remove a policy by name."""
        for i, policy in enumerate(self.policies):
            if policy.name == policy_name:
                del self.policies[i]
                break
        
        return self.policy_engine.remove_policy(policy_name)
    
    def reload_policies(self, policies: Union[List[PolicyConfig], str, Path]):
        """Reload policies from source."""
        new_policies = self._load_policies(policies)
        self.policies = new_policies
        self.policy_engine = PolicyEngine(self.policies)
        logger.info(f"Reloaded {len(new_policies)} policies")
    
    def get_policy_names(self) -> List[str]:
        """Get list of all policy names."""
        return [p.name for p in self.policies]
