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

2. **Run the test client** to see authorization in action:
   ```bash
   python examples/test_client.py
   ```

3. **Run the actual server** (for integration with MCP clients):
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

## Integration with MCP Clients

To use this with actual MCP clients (like Claude Desktop), add to your MCP configuration:

```json
{
  "mcpServers": {
    "weather-service": {
      "command": "python",
      "args": ["examples/weather_server.py"],
      "env": {
        "X-API-Key": "demo-key-user"
      }
    }
  }
}
```

## Key Benefits Demonstrated

1. **🔒 Security**: Multi-layered authorization with authentication + policies
2. **📝 Simplicity**: Intuitive YAML syntax vs complex JSON configurations  
3. **🎯 Flexibility**: Role-based, pattern-based, and conditional access controls
4. **🚀 Performance**: In-process authorization with no external dependencies
5. **🔍 Observability**: Comprehensive audit logging for security monitoring
6. **⚡ Developer Experience**: Type-safe policy building and easy testing

## Next Steps

- Explore different authentication methods (JWT, header-based)
- Try building your own policies using the PolicyBuilder API
- Check out the comprehensive documentation in `/docs`
- Integrate with your existing MCP servers
