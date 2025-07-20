# MCP Auth Guard Examples

This directory contains working examples demonstrating how to use MCP Auth Guard to secure your MCP servers with intuitive YAML policies.

## 🌍 Weather Service Example

A complete example showing how to secure a planetary weather service with different authorization levels.

### Features Demonstrated

- **Multiple Authentication Methods**: API key authentication with role-based access
- **Intuitive YAML Policies**: Easy-to-read policy definitions
- **Fine-grained Authorization**: Different access levels for different user roles
- **Conditional Access**: Time-based restrictions and safety policies
- **Audit Logging**: Complete request logging for security monitoring

### Quick Start

1. **Install dependencies**:
   ```bash
   cd mcp-auth-guard
   pip install -e .
   ```

2. **Run the real MCP client** to test authorization with actual FastMCP:
   ```bash
   # Test all roles with STDIO transport
   python examples/real_test_client.py
   
   # Test specific role
   python examples/real_test_client.py admin
   
   # Test with HTTP transport (requires running server)
   python examples/real_test_client.py http https://api.example.com/mcp
   
   # Test with SSE transport (requires running server)
   python examples/real_test_client.py sse https://api.example.com/sse
   ```

3. **Run the simulated test** to see policy logic:
   ```bash
   python examples/test_client.py
   ```

4. **Run the actual server** (for integration with MCP clients):
   ```bash
   python examples/weather_server.py
   ```

### Authentication Levels

The example includes three different user roles:

| Role | API Key | Access Level |
|------|---------|--------------|
| **Admin** | `demo-key-admin` | Full access to all weather tools |
| **User** | `demo-key-user` | Mars & Venus weather, can list Jupiter |
| **Intern** | `demo-key-intern` | Jupiter weather only at night |

### Policy Rules

The [`weather_policies.yaml`](weather_policies.yaml) file demonstrates:

```yaml
# Admin users get full access
- name: "admin_full_access"
  effect: "allow"
  agents:
    roles: ["admin"]
  tools:
    patterns: ["*"]  # All tools
  actions: ["list", "call"]

# Conditional access based on arguments
- name: "intern_jupiter_night_only"
  effect: "allow"
  agents:
    roles: ["intern"]
  tools:
    names: ["get_jupiter_weather"]
  conditions:
    - field: "tool.args.time"
      operator: "equals"
      value: "night"

# Safety policy blocking access
- name: "block_saturn_for_safety"
  effect: "deny"
  agents:
    roles: ["user", "intern"]
  tools:
    names: ["get_saturn_weather"]
```

### Expected Test Results

When you run `test_client.py`, you'll see:

```
👤 Testing as: ADMIN
   ✅ Visible tools: [get_mars_weather, get_jupiter_weather, get_saturn_weather, get_venus_weather]
   ✅ Admin access granted to get_mars_weather
   ✅ Admin access granted to get_saturn_weather

👤 Testing as: USER  
   ✅ Visible tools: [get_mars_weather, get_venus_weather, get_jupiter_weather]
   ✅ User access granted to get_mars_weather
   ❌ User access denied to get_jupiter_weather
   ❌ User access denied to get_saturn_weather

👤 Testing as: INTERN
   ✅ Visible tools: [get_jupiter_weather] 
   ❌ Intern access denied to get_jupiter_weather (wrong conditions)
   ✅ Intern access granted to get_jupiter_weather at night
```

## 🚀 Transport Types & Integration

The weather service supports all FastMCP transport types with proper authentication:

### STDIO Transport (Local Development)

**Environment Variables**: Authentication passed via environment variables
```bash
# Run with specific role
MCP_X_API_KEY="demo-key-admin" MCP_X_USER_ROLES="admin" python examples/weather_server.py
```

**Claude Desktop Configuration**:
```json
{
  "mcpServers": {
    "weather-admin": {
      "command": "python",
      "args": ["./weather_server.py"],
      "cwd": "/path/to/mcp-auth-guard/examples",
      "env": {
        "MCP_X_API_KEY": "demo-key-admin",
        "MCP_X_USER_ROLES": "admin",
        "MCP_X_USER_ID": "claude_admin",
        "MCP_X_AGENT_ID": "claude_desktop"
      }
    },
    "weather-user": {
      "command": "python",
      "args": ["./weather_server.py"],
      "cwd": "/path/to/mcp-auth-guard/examples",
      "env": {
        "MCP_X_API_KEY": "demo-key-user",
        "MCP_X_USER_ROLES": "user",
        "MCP_X_USER_ID": "claude_user",
        "MCP_X_AGENT_ID": "claude_desktop"
      }
    }
  }
}
```

### HTTP Transport (Production)

**HTTP Headers**: Authentication passed via standard HTTP headers
```bash
# Run server for HTTP transport
python -m fastmcp.cli run examples/weather_server.py --transport http --port 8000
```

**Client Configuration**:
```python
config = {
    "mcpServers": {
        "weather_service": {
            "transport": "http",
            "url": "https://api.example.com/mcp",
            "headers": {
                "X-API-Key": "demo-key-admin",
                "X-User-Roles": "admin",
                "X-User-ID": "production_user",
                "X-Agent-ID": "production_agent"
            }
        }
    }
}
```

### SSE Transport (Server-Sent Events)

**HTTP Headers**: Same authentication as HTTP transport
```bash
# Run server for SSE transport
python -m fastmcp.cli run examples/weather_server.py --transport sse --port 8000
```

**Client Configuration**:
```python
config = {
    "mcpServers": {
        "weather_service": {
            "transport": "sse",
            "url": "https://api.example.com/sse",
            "headers": {
                "X-API-Key": "demo-key-user",
                "X-User-Roles": "user"
            }
        }
    }
}
```

## 🧪 Testing Examples

### HTTP Client Examples

#### Simple HTTP Client
Use [`http_client_example.py`](http_client_example.py) for a basic HTTP client demo:

```bash
# Start the server
python examples/weather_server.py

# Run the HTTP client (in another terminal)
python examples/http_client_example.py
```

#### HTTP Role-Based Authorization Demo
Use [`http_roles_demo.py`](http_roles_demo.py) to see all user roles in action:

```bash
# Start the server
python examples/weather_server.py

# Run the role demo (in another terminal)
python examples/http_roles_demo.py
```

**Configuration Format**: Shows the standard MCP config format for HTTP transport:
```python
config = {
    "mcpServers": {
        "weather_service": {
            "transport": "http",
            "url": "http://127.0.0.1:8000/mcp/",
            "headers": {
                "X-API-Key": "demo-key-admin",
                "X-User-Roles": "admin",
                "X-User-ID": "prod_user",
                "X-Agent-ID": "prod_agent",
            }
        }
    }
}
```

### Real MCP Client Testing

Use [`real_test_client.py`](real_test_client.py) for comprehensive testing:

```bash
# Test all roles with STDIO (default)
python examples/real_test_client.py

# Test specific role with STDIO
python examples/real_test_client.py admin

# Test with HTTP transport
python examples/real_test_client.py admin http https://weather.api.com/mcp

# Test all roles with HTTP
python examples/real_test_client.py http https://weather.api.com/mcp

# Test with SSE transport
python examples/real_test_client.py user sse https://weather.api.com/sse
```

### Configuration-Based Testing

Use [`weather_client_config.py`](weather_client_config.py) for MCP config examples:

```bash
# Show configuration examples
python examples/weather_client_config.py examples

# Test production setup with environment variables
WEATHER_API_KEY="demo-key-admin" WEATHER_USER_ROLE="admin" \
python examples/weather_client_config.py production

# Generate config for specific role
python examples/weather_client_config.py admin
```

## Key Benefits Demonstrated

1. **🔒 Security**: Multi-layered authorization with authentication + policies
2. **📝 Simplicity**: Intuitive YAML syntax vs complex JSON configurations  
3. **🎯 Flexibility**: Role-based, pattern-based, and conditional access controls
4. **🚀 Performance**: In-process authorization with no external dependencies
5. **🔍 Observability**: Comprehensive audit logging for security monitoring
6. **⚡ Developer Experience**: Type-safe policy building and easy testing

## 📁 Example Files

| File | Purpose | Transport Support |
|------|---------|------------------|
| [`weather_server.py`](weather_server.py) | Main MCP server with auth middleware | STDIO, HTTP, SSE |
| [`http_client_example.py`](http_client_example.py) | Simple HTTP client example | HTTP |
| [`http_roles_demo.py`](http_roles_demo.py) | HTTP role-based authorization demo | HTTP |
| [`real_test_client.py`](real_test_client.py) | Real FastMCP client for testing | STDIO, HTTP, SSE |
| [`test_client.py`](test_client.py) | Simulated client for policy testing | Simulation only |
| [`weather_client_config.py`](weather_client_config.py) | MCP configuration examples | STDIO, HTTP, SSE |
| [`claude_desktop_config.json`](claude_desktop_config.json) | Claude Desktop configuration | STDIO |
| [`weather_policies.yaml`](weather_policies.yaml) | Authorization policy definitions | All transports |

## 🔄 Authentication Flow

### STDIO Transport
```
Client → Environment Variables → FastMCP → Auth Middleware → Policy Engine
         (MCP_X_API_KEY)       (Headers)   (AuthContext)    (Decision)
```

### HTTP/SSE Transport  
```
Client → HTTP Headers → FastMCP → Auth Middleware → Policy Engine
         (X-API-Key)    (Headers) (AuthContext)    (Decision)
```

## Next Steps

- **🔐 Authentication**: Explore JWT and header-based authentication methods
- **📋 Policies**: Try building custom policies using the PolicyBuilder API  
- **📚 Documentation**: Check out comprehensive docs in `/docs`
- **🔌 Integration**: Integrate auth middleware with your existing MCP servers
- **🚀 Production**: Deploy with HTTP transport for production environments
