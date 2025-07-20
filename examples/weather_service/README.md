# Weather Service Example

Complete demonstration of MCP Auth Guard with role-based planetary weather service.

## 🚀 Quick Start

```bash
# 1. Start the server
python weather_server.py

# 2. Test with different roles (in another terminal)
python test_client.py                    # Test all roles
python test_client.py admin              # Test admin role only
python test_client.py user               # Test user role only

# 3. HTTP examples
python basic_client.py                   # Simple HTTP client
python http_roles_demo.py                # Role-based HTTP demo
```

## 📁 Files Overview

| File | Purpose | Transport Support |
|------|---------|------------------|
| **`weather_server.py`** | Main MCP server with auth middleware | STDIO, HTTP, SSE |
| **`weather_policies.yaml`** | Authorization policy configuration | All transports |
| **`test_client.py`** | Comprehensive test client for all transports | STDIO, HTTP, SSE |
| **`basic_client.py`** | Simple HTTP client example | HTTP |
| **`http_roles_demo.py`** | HTTP role-based authorization demo | HTTP |
| **`claude_desktop_config.json`** | Claude Desktop integration config | STDIO |

## 👥 Authentication Levels

The example includes three different user roles with specific access levels:

| Role | API Key | Access Level | Tools Available |
|------|---------|--------------|-----------------|
| **Admin** | `demo-key-admin` | Full access to all weather tools | All planets (Mars, Venus, Jupiter, Saturn) |
| **User** | `demo-key-user` | Mars & Venus weather, can list Jupiter | Mars, Venus weather + Jupiter listing only |
| **Intern** | `demo-key-intern` | Jupiter weather only at night | Jupiter weather with time restrictions |

## 📋 Policy Rules

The [`weather_policies.yaml`](weather_policies.yaml) file demonstrates advanced authorization patterns:

### Admin Full Access
```yaml
- name: "admin_full_access"
  effect: "allow"
  agents:
    roles: ["admin"]
  tools:
    patterns: ["*"]  # All tools
  actions: ["list", "call"]
  priority: 1000
```

### User Limited Access
```yaml
- name: "user_basic_weather"
  effect: "allow"
  agents:
    roles: ["user"]
  tools:
    names: ["get_mars_weather", "get_venus_weather"]
  actions: ["list", "call"]
  priority: 500
```

### Conditional Access (Time-based)
```yaml
- name: "intern_jupiter_night_only"
  effect: "allow"
  agents:
    roles: ["intern"]
  tools:
    names: ["get_jupiter_weather"]
  actions: ["call"]
  conditions:
    - field: "tool.args.time"
      operator: "equals"
      value: "night"
  priority: 300
```

### Safety Policy (Deny Rules)
```yaml
- name: "block_saturn_for_safety"
  effect: "deny"
  agents:
    roles: ["user", "intern"]  # Only admins can access
  tools:
    names: ["get_saturn_weather"]
  actions: ["*"]
  priority: 800
```

## 🧪 Expected Test Results

When you run `test_client.py`, you'll see role-based authorization in action:

```
👤 Testing as: ADMIN
   ✅ Visible tools: [get_mars_weather, get_jupiter_weather, get_saturn_weather, get_venus_weather]
   ✅ Admin access granted to get_mars_weather
   ✅ Admin access granted to get_saturn_weather

👤 Testing as: USER  
   ✅ Visible tools: [get_mars_weather, get_venus_weather, get_jupiter_weather]
   ✅ User access granted to get_mars_weather
   ❌ User access denied to get_jupiter_weather (can list but not call)
   ❌ User access denied to get_saturn_weather (safety policy)

👤 Testing as: INTERN
   ✅ Visible tools: [get_jupiter_weather] 
   ❌ Intern access denied to get_jupiter_weather (day time, needs night)
   ✅ Intern access granted to get_jupiter_weather at night
```

## 🚀 Transport Types & Integration

The weather service supports all FastMCP transport types with proper authentication:

### STDIO Transport (Local Development)

**Environment Variables**: Authentication passed via environment variables

```bash
# Run with specific role
MCP_X_API_KEY="demo-key-admin" MCP_X_USER_ROLES="admin" python weather_server.py
```

**Claude Desktop Configuration**:
```json
{
  "mcpServers": {
    "weather-admin": {
      "command": "python",
      "args": ["./weather_server.py"],
      "cwd": "/path/to/mcp-auth-guard/examples/weather_service",
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
      "cwd": "/path/to/mcp-auth-guard/examples/weather_service",
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
python weather_server.py  # Server starts on HTTP by default
```

**Client Configuration**:
```python
config = {
    "mcpServers": {
        "weather_service": {
            "transport": "http",
            "url": "http://localhost:8000/mcp",
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
# Run server for SSE transport (modify server to use SSE)
python weather_server.py  # Modify asyncio.run(mcp.run(transport="sse"))
```

## 🧪 Testing Examples

### HTTP Client Examples

#### Simple HTTP Client
Use [`basic_client.py`](basic_client.py) for a basic HTTP client demo:

```bash
# Start the server
python weather_server.py

# Run the HTTP client (in another terminal)
python basic_client.py
```

#### HTTP Role-Based Authorization Demo
Use [`http_roles_demo.py`](http_roles_demo.py) to see all user roles in action:

```bash
# Start the server
python weather_server.py

# Run the role demo (in another terminal)
python http_roles_demo.py
```

### Real MCP Client Testing

Use [`test_client.py`](test_client.py) for comprehensive testing:

```bash
# Test all roles with STDIO (default)
python test_client.py

# Test specific role with STDIO
python test_client.py admin

# Test with HTTP transport
python test_client.py admin http http://localhost:8000/mcp

# Test all roles with HTTP
python test_client.py http http://localhost:8000/mcp

# Test with SSE transport
python test_client.py user sse http://localhost:8000/sse
```

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

## 🎯 Key Features Demonstrated

1. **🔒 Multi-layer Security**: Authentication + Authorization with role-based access
2. **📝 Intuitive Policies**: Human-readable YAML vs complex JSON configurations  
3. **🎯 Flexible Controls**: Role-based, pattern-based, and conditional access rules
4. **🚀 High Performance**: In-process authorization with no external dependencies
5. **🔍 Complete Observability**: Comprehensive audit logging for security monitoring
6. **⚡ Developer Experience**: Type-safe policy building and easy testing

## 🔧 Customization

### Adding New Roles
1. Add new API key to `weather_server.py`:
   ```python
   api_key_roles={
       "demo-key-admin": ["admin"],
       "demo-key-user": ["user"], 
       "demo-key-intern": ["intern"],
       "demo-key-scientist": ["scientist"]  # New role
   }
   ```

2. Add policy rules in `weather_policies.yaml`:
   ```yaml
   - name: "scientist_research_access"
     effect: "allow"
     agents:
       roles: ["scientist"]
     tools:
       patterns: ["*_weather"]
     actions: ["list", "call"]
   ```

### Adding New Tools
1. Add tool to `weather_server.py`:
   ```python
   @mcp.tool()
   def get_moon_weather(time: str = "day") -> str:
       """Get current weather conditions on Earth's Moon."""
       return "Vacuum conditions, temperature varies drastically"
   ```

2. Update policies to control access

## 🚦 Next Steps

- **📋 Learn Policy Writing**: Check out the [**Policy Writing Guide**](../POLICY_GUIDE.md) for creating your own policies
- **🔐 Authentication**: Try JWT and header-based authentication methods
- **📋 Advanced Policies**: Experiment with complex conditional rules
- **📚 Documentation**: Check out the main documentation in `/docs`
- **🔌 Integration**: Integrate with your existing MCP servers
- **🚀 Production**: Deploy with proper HTTP transport for production environments
