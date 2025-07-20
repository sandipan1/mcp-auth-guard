# Getting Started with MCP Auth Guard

This guide will help you get started with MCP Auth Guard to secure your MCP servers with intuitive authorization policies.

## Installation

Install MCP Auth Guard using pip:

```bash
pip install mcp-auth-guard
```

For development or to try the examples:

```bash
git clone https://github.com/your-org/mcp-auth-guard.git
cd mcp-auth-guard
pip install -e .
```

## Basic Concepts

MCP Auth Guard provides three main components:

1. **Authentication**: Verify who is making the request (JWT, API keys, headers)
2. **Policies**: Define what users can do (YAML-based rules)
3. **Middleware**: Integrate with your FastMCP server (seamless integration)

## Your First Secured Server

Let's create a simple MCP server with authorization:

### 1. Create Your MCP Server

```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("My Secure Server")

@mcp.tool()
def get_public_data() -> str:
    """Get public information."""
    return "This is public data"

@mcp.tool() 
def get_private_data() -> str:
    """Get sensitive information."""
    return "This is sensitive data"

@mcp.tool()
def admin_action(command: str) -> str:
    """Administrative command."""
    return f"Executed admin command: {command}"
```

### 2. Create Authorization Policies

Create `policies.yaml`:

```yaml
name: "my_service_auth"
description: "Authorization for my service"
default_effect: "deny"

rules:
  # Public data access for everyone
  - name: "public_access"
    effect: "allow"
    agents:
      roles: ["*"]  # Any role
    tools:
      names: ["get_public_data"]
    actions: ["list", "call"]
    
  # Private data for authenticated users
  - name: "user_private_access"
    effect: "allow"
    agents:
      roles: ["user", "admin"]
    tools:
      names: ["get_private_data"]
    actions: ["list", "call"]
    
  # Admin actions only for admins
  - name: "admin_only"
    effect: "allow"
    agents:
      roles: ["admin"]
    tools:
      patterns: ["admin_*"]
    actions: ["list", "call"]
```

### 3. Add Authentication & Authorization

```python
# server.py (continued)
from mcp_auth_guard import create_api_key_middleware

# Add Auth Guard middleware
auth_middleware = create_api_key_middleware(
    api_keys=["user-key-123", "admin-key-456"],
    policies="./policies.yaml",
    enable_audit_logging=True
)

mcp.add_middleware(auth_middleware)

# Run the server
if __name__ == "__main__":
    import asyncio
    asyncio.run(mcp.run())
```

### 4. Test Your Server

Create a test client:

```python
# test.py
import asyncio
from mcp_auth_guard.schemas.auth import AuthContext, AuthMethod
from mcp_auth_guard.schemas.resource import ToolResource, ResourceContext
from mcp_auth_guard.policy import PolicyEngine, PolicyLoader

async def test_authorization():
    # Load your policy
    policy = PolicyLoader.load_from_file("policies.yaml")
    engine = PolicyEngine([policy])
    
    # Test as regular user
    user_context = AuthContext(
        user_id="alice",
        roles=["user"],
        authenticated=True,
        auth_method=AuthMethod.API_KEY
    )
    
    # Test accessing public data
    resource = ResourceContext(
        resource_type="tool",
        resource=ToolResource(name="get_public_data"),
        action="call",
        method="tools/call"
    )
    
    decision = await engine.evaluate(user_context, resource)
    print(f"User accessing public data: {decision.allowed}")  # Should be True
    
    # Test accessing admin action
    admin_resource = ResourceContext(
        resource_type="tool", 
        resource=ToolResource(name="admin_action"),
        action="call",
        method="tools/call"
    )
    
    decision = await engine.evaluate(user_context, admin_resource)
    print(f"User accessing admin action: {decision.allowed}")  # Should be False

asyncio.run(test_authorization())
```

## Authentication Methods

### API Key Authentication

Simple and effective for service-to-service communication:

```python
from mcp_auth_guard import create_api_key_middleware

middleware = create_api_key_middleware(
    api_keys=["key1", "key2", "admin-key"],
    policies="./policies.yaml"
)

# Clients send: X-API-Key: key1
# Plus optional: X-User-Roles: admin,user
```

### JWT Authentication

For more sophisticated authentication with claims:

```python
from mcp_auth_guard import create_jwt_middleware

middleware = create_jwt_middleware(
    jwt_secret="your-secret-key",
    policies="./policies.yaml",
    required_claims=["sub", "role"]
)

# Clients send: Authorization: Bearer <jwt-token>
```

### Header-based Authentication

Extract user info directly from headers:

```python
from mcp_auth_guard import create_header_middleware

middleware = create_header_middleware(
    policies="./policies.yaml",
    header_mapping={
        "x-user-id": "user_id",
        "x-user-roles": "roles",
        "x-session-id": "session_id"
    }
)
```

## Policy Language Basics

### Agent Matching

Control who can access what:

```yaml
agents:
  user_id: ["alice", "bob"]           # Specific users
  roles: ["admin", "user"]            # User roles
  agent_id: ["claude", "assistant"]   # Agent IDs
  patterns: ["admin_*", "*_service"]  # Wildcard matching
```

### Tool Matching

Define which tools the rule applies to:

```yaml
tools:
  names: ["get_weather", "send_email"]    # Exact names
  patterns: ["get_*", "*_admin"]          # Patterns
  namespaces: ["weather", "admin"]        # Namespaces
  tags: ["safe", "public"]               # Tool tags
```

### Actions

Specify what actions are allowed:

```yaml
actions: ["list", "call"]  # List tools and call them
actions: ["list"]          # Only list, not call
actions: ["*"]             # All actions
```

### Conditions

Add fine-grained conditional logic:

```yaml
conditions:
  # Check tool arguments
  - field: "tool.args.readonly"
    operator: "equals"
    value: true
    
  # Check user attributes
  - field: "user.roles"
    operator: "in"
    value: ["admin", "moderator"]
    
  # Pattern matching
  - field: "tool.name"
    operator: "regex"
    value: "^safe_.*"
```

## CLI Tools

MCP Auth Guard includes helpful CLI tools:

```bash
# Validate a policy file
mcp-auth validate policies.yaml

# Get policy information
mcp-auth info policies.yaml

# Test authorization
mcp-auth test policies.yaml --user alice --roles user --tool get_data

# Create a new policy template
mcp-auth create my_service --output my_policy.yaml

# Format/clean up a policy file
mcp-auth format policies.yaml
```

## Next Steps

- Explore the [complete weather service example](../examples/)
- Learn about [advanced policy features](policy-reference.md)
- Check out [different authentication methods](authentication.md)
- Read the [API reference](api-reference.md)

## Common Patterns

### Role-based Access Control

```yaml
rules:
  - name: "admin_full_access"
    effect: "allow"
    agents:
      roles: ["admin"]
    tools:
      patterns: ["*"]
    
  - name: "user_read_only"
    effect: "allow"
    agents:
      roles: ["user"]
    tools:
      patterns: ["get_*", "list_*"]
```

### Time-based Access

```yaml
rules:
  - name: "business_hours_only"
    effect: "allow"
    agents:
      roles: ["employee"]
    tools:
      patterns: ["work_*"]
    conditions:
      - field: "request.timestamp"
        operator: "gt"
        value: "09:00"
      - field: "request.timestamp"
        operator: "lt"  
        value: "17:00"
```

### Environment-based Access

```yaml
rules:
  - name: "production_admins_only"
    effect: "allow" 
    agents:
      roles: ["admin"]
    tools:
      tags: ["production"]
    conditions:
      - field: "user.claims.environment"
        operator: "equals"
        value: "production"
```

Ready to secure your MCP server? Start with the example above and customize it for your needs!
