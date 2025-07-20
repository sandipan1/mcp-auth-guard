# 🚀 MCP Auth Guard Transport Guide

Complete guide for using MCP Auth Guard with different FastMCP transport types.

## 📋 Quick Reference

| Transport | Auth Method | Use Case | Command Example |
|-----------|-------------|----------|-----------------|
| **STDIO** | Environment Variables | Local development, testing | `python real_test_client.py admin` |
| **HTTP** | HTTP Headers | Production, cloud services | `python real_test_client.py admin http https://api.com/mcp` |
| **SSE** | HTTP Headers | Legacy systems, streaming | `python real_test_client.py admin sse https://api.com/sse` |

## 🔧 STDIO Transport (Local Development)

**Best for**: Local development, testing, Claude Desktop integration

### Authentication
- **Method**: Environment variables converted to headers by FastMCP
- **Variables**: `MCP_X_API_KEY`, `MCP_X_USER_ROLES`, `MCP_X_USER_ID`, `MCP_X_AGENT_ID`

### Server Setup
```bash
# Run server directly
python weather_server.py

# Run with specific auth
MCP_X_API_KEY="demo-key-admin" MCP_X_USER_ROLES="admin" python weather_server.py
```

### Client Usage
```bash
# Test all roles
python real_test_client.py

# Test specific role
python real_test_client.py admin
python real_test_client.py user
python real_test_client.py intern
```

### MCP Configuration
```python
config = {
    "mcpServers": {
        "weather_service": {
            "transport": "stdio",
            "command": "python",
            "args": ["./weather_server.py"],
            "env": {
                "MCP_X_API_KEY": "demo-key-admin",
                "MCP_X_USER_ROLES": "admin",
                "MCP_X_USER_ID": "user_123",
                "MCP_X_AGENT_ID": "my_agent"
            }
        }
    }
}
```

### Claude Desktop Config
```json
{
  "mcpServers": {
    "weather-admin": {
      "command": "python",
      "args": ["./weather_server.py"],
      "cwd": "/path/to/mcp-auth-guard/examples",
      "env": {
        "MCP_X_API_KEY": "demo-key-admin",
        "MCP_X_USER_ROLES": "admin"
      }
    }
  }
}
```

## 🌐 HTTP Transport (Production)

**Best for**: Production deployments, cloud services, microservices

### Authentication
- **Method**: Standard HTTP headers
- **Headers**: `X-API-Key`, `X-User-Roles`, `X-User-ID`, `X-Agent-ID`

### Server Setup
```bash
# Run with FastMCP CLI
python -m fastmcp.cli run weather_server.py --transport http --port 8000

# Or with uvicorn
uvicorn weather_server:app --host 0.0.0.0 --port 8000
```

### Client Usage
```bash
# Test with HTTP transport
python real_test_client.py admin http https://api.example.com:8000/mcp

# Test all roles
python real_test_client.py http https://api.example.com:8000/mcp
```

### MCP Configuration
```python
config = {
    "mcpServers": {
        "weather_service": {
            "transport": "http",
            "url": "https://api.example.com/mcp",
            "headers": {
                "X-API-Key": "demo-key-admin",
                "X-User-Roles": "admin",
                "X-User-ID": "prod_user",
                "X-Agent-ID": "prod_agent",
                "Authorization": "Bearer your-token"  # Optional
            }
        }
    }
}
```

### Production Deployment
```dockerfile
# Dockerfile example
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -e .
EXPOSE 8000
CMD ["python", "-m", "fastmcp.cli", "run", "examples/weather_server.py", "--transport", "http", "--port", "8000"]
```

## 📡 SSE Transport (Server-Sent Events)

**Best for**: Legacy systems, streaming data, real-time updates

### Authentication
- **Method**: HTTP headers (same as HTTP transport)
- **Headers**: `X-API-Key`, `X-User-Roles`, `X-User-ID`, `X-Agent-ID`

### Server Setup
```bash
# Run with SSE transport
python -m fastmcp.cli run weather_server.py --transport sse --port 8000
```

### Client Usage
```bash
# Test with SSE transport
python real_test_client.py admin sse https://api.example.com:8000/sse

# Test all roles
python real_test_client.py sse https://api.example.com:8000/sse
```

### MCP Configuration
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

## 🔄 Authentication Flow Comparison

### STDIO Flow
```
Client Process
    ↓ (spawn subprocess with env vars)
Server Process (MCP_X_API_KEY=...)
    ↓ (FastMCP converts env → headers)
Auth Middleware (X-API-Key header)
    ↓ (extract auth context)
Policy Engine (evaluate rules)
    ↓ (allow/deny)
Tool Execution
```

### HTTP/SSE Flow
```
HTTP Client
    ↓ (HTTP request with headers)
HTTP Server (X-API-Key header)
    ↓ (FastMCP receives request)
Auth Middleware (extract headers)
    ↓ (extract auth context)
Policy Engine (evaluate rules)
    ↓ (allow/deny)
Tool Execution
    ↓ (HTTP response)
Client
```

## 🧪 Testing Commands Reference

```bash
# STDIO Transport Tests
python real_test_client.py                    # All roles
python real_test_client.py admin              # Admin only
python real_test_client.py user               # User only
python real_test_client.py intern             # Intern only

# HTTP Transport Tests
python real_test_client.py http https://api.example.com/mcp              # All roles
python real_test_client.py admin http https://api.example.com/mcp        # Admin only
python real_test_client.py user http https://api.example.com/mcp         # User only

# SSE Transport Tests
python real_test_client.py sse https://api.example.com/sse               # All roles
python real_test_client.py admin sse https://api.example.com/sse         # Admin only
python real_test_client.py user sse https://api.example.com/sse          # User only

# Configuration Examples
python weather_client_config.py examples     # Show all config examples
python weather_client_config.py admin        # Admin config only
python weather_client_config.py production   # Production config with env vars

# Policy Testing (Simulation)
python test_client.py                         # Simulated policy tests
```

## 🚀 Deployment Examples

### Docker Compose (HTTP)
```yaml
version: '3.8'
services:
  weather-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    command: ["python", "-m", "fastmcp.cli", "run", "examples/weather_server.py", "--transport", "http", "--port", "8000"]
  
  nginx:
    image: nginx
    ports:
      - "80:80"
    depends_on:
      - weather-service
```

### Kubernetes Deployment (HTTP)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weather-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: weather-service
  template:
    metadata:
      labels:
        app: weather-service
    spec:
      containers:
      - name: weather-service
        image: weather-service:latest
        ports:
        - containerPort: 8000
        command: ["python", "-m", "fastmcp.cli", "run", "examples/weather_server.py", "--transport", "http", "--port", "8000"]
---
apiVersion: v1
kind: Service
metadata:
  name: weather-service
spec:
  selector:
    app: weather-service
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 📋 Troubleshooting

### Common Issues

1. **STDIO: "Missing X-API-Key header"**
   - Check environment variable names: `MCP_X_API_KEY` not `X_API_KEY`
   - Ensure env vars are passed to subprocess

2. **HTTP: "Connection refused"**
   - Verify server is running on correct port
   - Check firewall/network settings
   - Ensure correct URL format

3. **SSE: "Stream disconnected"**
   - Check server stability
   - Verify SSE endpoint configuration
   - Monitor network connectivity

4. **All: "Access denied"**
   - Verify API key in policies configuration
   - Check role mapping in YAML
   - Review policy rule priorities

### Debug Commands
```bash
# Enable debug logging
DEBUG=true python real_test_client.py admin

# Test server connectivity
curl -H "X-API-Key: demo-key-admin" https://api.example.com/mcp/ping

# Check policy configuration
python -c "from mcp_auth_guard.policy.loader import PolicyLoader; print(PolicyLoader.load_from_file('weather_policies.yaml'))"
```
