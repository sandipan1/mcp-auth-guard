# MCP Auth Guard Examples

Working examples demonstrating how to secure MCP servers with role-based authorization and intuitive YAML policies.

## 🌍 Weather Service Example

**[→ Go to Weather Service Example](weather_service/)**

Complete demonstration of MCP Auth Guard featuring:
- **Role-based access control** (admin, user, intern roles)
- **Multiple transport types** (STDIO, HTTP, SSE)
- **Conditional policies** (time-based restrictions, safety rules)
- **Real MCP client integration** with FastMCP

```bash
cd examples/weather_service
python weather_server.py     # Start server
python test_client.py        # Test all roles
```

## 📋 Other Examples

- **[`POLICY_GUIDE.md`](POLICY_GUIDE.md)** - **Complete guide to writing authorization policies**
- **[`comprehensive_server.py`](comprehensive_server.py)** - Demonstrates tools, resources, and prompts authorization
- **`policy_management.py`** - Policy management and validation tools
- **`secure_config.yaml`** - Secure API key configuration example  
- **`TRANSPORT_GUIDE.md`** - Detailed transport configuration guide

## Quick Setup

1. **Install dependencies**:
   ```bash
   cd mcp-auth-guard
   pip install -e .
   ```

2. **Try the weather service**:
   ```bash
   cd examples/weather_service
   python weather_server.py
   ```

**[→ See detailed documentation in weather_service/](weather_service/)**
