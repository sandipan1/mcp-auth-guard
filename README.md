# 🛡️ MCP Auth Guard

**Intuitive authorization middleware for MCP tools with type-safe policies**

A modern, developer-friendly authorization system designed specifically for [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers. Get fine-grained access control with simple YAML policies and seamless [FastMCP](https://gofastmcp.com/) integration.

## ✨ Key Features

- 🔐 **Multiple Auth Methods**: JWT, API keys, header-based, or no auth
- 📝 **Intuitive YAML Policies**: Easy-to-read, semantic policy definitions  
- 🎯 **Fine-grained Control**: Role-based, pattern-based, and conditional access
- ⚡ **Zero Latency**: In-process authorization with no external dependencies
- 🔍 **Comprehensive Auditing**: Detailed logging for security monitoring
- 🛠️ **Type-safe APIs**: Fluent policy builders with full type safety
- 🚀 **Developer-first**: Simple integration, great debugging experience

## 🚀 Quick Start

### Installation

```bash
pip install mcp-auth-guard
```

### Basic Usage

```python
from fastmcp import FastMCP
from mcp_auth_guard import create_api_key_middleware

# Create your MCP server
mcp = FastMCP("My Secure Server")

@mcp.tool()
def sensitive_operation(data: str) -> str:
    """A tool that needs authorization."""
    return f"Processing: {data}"

# Add Auth Guard middleware
auth_middleware = create_api_key_middleware(
    api_keys=["secret-key-123"],
    policies="./policies.yaml"
)
mcp.add_middleware(auth_middleware)

# Run your server
await mcp.run()
```

### Simple Policy Configuration

Create `policies.yaml`:

```yaml
name: "my_service_policy"
default_effect: "deny"

rules:
  - name: "admin_access"
    effect: "allow"
    agents:
      roles: ["admin"]
    tools:
      patterns: ["*"]  # All tools
    actions: ["list", "call"]

  - name: "user_limited_access"
    effect: "allow"
    agents:
      roles: ["user"]
    tools:
      names: ["safe_tool", "read_only_tool"]
    actions: ["list", "call"]
```

## 📋 Examples

Check out the [**Weather Service Example**](examples/) - a complete working demo showing:

- Multiple user roles (admin, user, intern)
- Conditional access (time-based restrictions)
- Safety policies (blocking dangerous operations)
- Comprehensive audit logging

```bash
# Try the interactive demo
cd examples
python test_client.py
```

## 🔐 Authentication Methods

### JWT Authentication

```python
from mcp_auth_guard import create_jwt_middleware

middleware = create_jwt_middleware(
    jwt_secret="your-secret-key",
    policies="./policies.yaml",
    required_claims=["sub", "role"]
)
```

### API Key Authentication

```python
from mcp_auth_guard import create_api_key_middleware

middleware = create_api_key_middleware(
    api_keys=["key1", "key2", "key3"],
    policies="./policies.yaml"
)
```

### Header-based Authentication

```python
from mcp_auth_guard import create_header_middleware

middleware = create_header_middleware(
    policies="./policies.yaml",
    header_mapping={
        "x-user-id": "user_id",
        "x-user-roles": "roles"
    }
)
```

## 📝 Policy Language

### Agent Matching

```yaml
agents:
  user_id: ["alice", "bob"]           # Specific users
  roles: ["admin", "developer"]       # User roles  
  agent_id: ["claude", "gpt-4"]      # Agent identifiers
  patterns: ["admin_*", "*_service"]  # Wildcard patterns
```

### Tool Matching

```yaml
tools:
  names: ["get_weather", "send_email"]    # Exact tool names
  patterns: ["get_*", "*_admin"]          # Wildcard patterns
  namespaces: ["weather", "admin"]        # Tool namespaces
  tags: ["safe", "public"]               # Tool tags
```

### Conditions

```yaml
conditions:
  - field: "tool.args.time"
    operator: "equals"
    value: "night"
    
  - field: "user.roles"
    operator: "in"
    value: ["admin", "moderator"]
    
  - field: "tool.name"
    operator: "regex"
    value: "^admin_.*"
```

## 🛠️ Type-safe Policy Building

For programmatic policy creation:

```python
from mcp_auth_guard.policy import policy, rule

# Build policies with code
my_policy = (policy("secure_service")
    .with_description("Security policy for my service")
    .deny_by_default()
    .add_rule(
        rule("admin_access")
        .for_roles("admin")
        .for_tool_patterns("*")
        .allow()
    )
    .add_rule(
        rule("user_read_only")
        .for_roles("user")
        .for_tool_patterns("get_*", "list_*")
        .when_equals("tool.args.readonly", True)
        .allow()
    )
    .build())
```

## 🔍 Policy Testing & Debugging

Built-in tools for testing your policies:

```python
# Test a policy
from mcp_auth_guard.policy import PolicyLoader, PolicyEngine
from mcp_auth_guard.schemas import AuthContext, ToolResource, ResourceContext

# Load and test
policy = PolicyLoader.load_from_file("policies.yaml")
engine = PolicyEngine([policy])

# Create test context
auth_ctx = AuthContext(user_id="alice", roles=["user"], authenticated=True)
resource_ctx = ResourceContext(
    resource_type="tool",
    resource=ToolResource(name="get_weather"),
    action="call",
    method="tools/call"
)

# Evaluate
decision = await engine.evaluate(auth_ctx, resource_ctx)
print(f"Allowed: {decision.allowed}, Reason: {decision.reason}")
```

## 📊 Comparison with Existing Solutions

| Feature | MCP Auth Guard | Eunomia v1 | Custom Solutions |
|---------|----------------|------------|------------------|
| **Setup Complexity** | ⭐⭐⭐⭐⭐ Simple | ⭐⭐ Complex | ⭐ Very Complex |
| **Policy Syntax** | ⭐⭐⭐⭐⭐ Intuitive YAML | ⭐⭐ Verbose JSON | ⭐ Custom Code |
| **Performance** | ⭐⭐⭐⭐⭐ In-process | ⭐⭐⭐ Network calls | ⭐⭐⭐⭐ Variable |
| **MCP Integration** | ⭐⭐⭐⭐⭐ Native | ⭐⭐⭐ External server | ⭐⭐ Manual |
| **Type Safety** | ⭐⭐⭐⭐⭐ Full TypeScript/Python | ⭐⭐ Limited | ⭐ None |
| **Developer Experience** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐ Fair | ⭐ Poor |

## 🔧 Advanced Features

### Dynamic Policy Updates

```python
# Update policies at runtime
middleware.add_policy(new_policy)
middleware.remove_policy("old_policy_name")
middleware.reload_policies("./updated_policies/")
```

### Custom Conditions

```python
# Extend with custom condition evaluators
class TimeBasedCondition(PolicyCondition):
    def evaluate(self, context):
        current_hour = datetime.now().hour
        return 9 <= current_hour <= 17  # Business hours only
```

### Performance Monitoring

```python
# Built-in performance metrics
decision = await engine.evaluate(auth_ctx, resource_ctx)
print(f"Evaluation took: {decision.evaluation_time_ms}ms")
print(f"Rules evaluated: {decision.evaluated_rules}")
```

## 📚 Documentation

- [**Getting Started Guide**](docs/getting-started.md)
- [**Policy Reference**](docs/policy-reference.md)  
- [**Authentication Methods**](docs/authentication.md)
- [**API Reference**](docs/api-reference.md)
- [**Migration from Eunomia v1**](docs/migration.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

Apache License 2.0. See [LICENSE](LICENSE) for details.

---

**Built with ❤️ for the MCP community**
