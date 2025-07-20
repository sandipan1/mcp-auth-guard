# Comprehensive Authorization Demo

Complete example demonstrating MCP Auth Guard authorization across **all three MCP capability types**: tools, resources, and prompts.

## 🚀 Quick Start

### 1. Start the Server
```bash
python comprehensive_server.py
```

### 2. Test Authorization
```bash
# Complete test suite for all roles
python comprehensive_client.py all

# Test specific role
python comprehensive_client.py admin
python comprehensive_client.py user

# Quick demo
python comprehensive_client.py demo

# Basic HTTP client demo
python comprehensive_basic_client.py
```

## 🎭 User Roles & Access Levels

| Role | API Key | Tools Access | Resources Access | Prompts Access |
|------|---------|--------------|------------------|----------------|
| **Admin** | `admin-key-123` | All tools | All resources | All prompts |
| **Analyst** | `analyst-key-456` | Data tools only | Logs + public | SQL analysis |
| **User** | `user-key-789` | Basic tools | Own profile + public | User queries |
| **Public** | `public-key-000` | Public info only | Public docs only | None |

## 🛠️ Available Capabilities

### Tools (Executable Functions)
- `get_user_info` - Get user information (user+ access)
- `delete_user` - Delete user account (admin only)
- `query_database` - Execute SQL queries (analyst+ access)
- `public_info` - Get public information (everyone)

### Resources (Static Content)
- `user://profile` - User profile data (user+ access)
- `public://docs` - Public documentation (everyone)
- `admin://system` - System configuration (admin only)
- `api://logs` - API access logs (analyst+ access)

### Prompts (AI Templates)
- `user_query` - General query template (user+ access)
- `admin_report` - Administrative reports (admin only)
- `sql_analysis` - SQL security analysis (analyst+ access)

## 🧪 Authorization Examples

### Admin (Full Access)
```bash
# ✅ Can do everything
curl -H "X-API-Key: admin-key-123" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"delete_user","arguments":{"user_id":"test"}}}' \
     http://localhost:8000/mcp
```

### User (Limited Access)
```bash
# ✅ Can get user info
curl -H "X-API-Key: user-key-789" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_user_info","arguments":{"user_id":"test"}}}' \
     http://localhost:8000/mcp

# ❌ Cannot delete users
curl -H "X-API-Key: user-key-789" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"delete_user","arguments":{"user_id":"test"}}}' \
     http://localhost:8000/mcp
```

### Public (Minimal Access)
```bash
# ✅ Can access public resources
curl -H "X-API-Key: public-key-000" \
     -d '{"jsonrpc":"2.0","id":1,"method":"resources/read","params":{"uri":"public://docs"}}' \
     http://localhost:8000/mcp

# ❌ Cannot access private resources
curl -H "X-API-Key: public-key-000" \
     -d '{"jsonrpc":"2.0","id":1,"method":"resources/read","params":{"uri":"user://profile"}}' \
     http://localhost:8000/mcp
```

## 📋 Policy Highlights

The `comprehensive_policies.yaml` demonstrates:

### Clear Capability Separation
```yaml
# Separate sections for each capability type
tools:
  names: ["get_user_info", "query_database"]
resources:
  uris: ["api://logs"]
prompts:
  names: ["sql_analysis"]
```

### Resource URI Patterns
```yaml
# Pattern-based resource access
resources:
  patterns: ["public://*"]  # All public resources
  schemes: ["user"]         # All user:// resources
```

### Conditional SQL Security
```yaml
# Allow only SELECT statements for analysts
conditions:
  - field: "tool.args.sql"
    operator: "regex"
    value: "^\\s*SELECT\\s+.*"
```

### Layered Security
```yaml
# High-priority deny rules override allow rules
- name: "block_admin_tools"
  effect: "deny" 
  priority: 900
  
- name: "allow_user_access"
  effect: "allow"
  priority: 500
```

## 🔄 Testing Scenarios

### 1. Privilege Escalation Prevention
- User tries to access admin tools → Blocked
- Public tries to read private resources → Blocked
- Analyst tries to use admin prompts → Blocked

### 2. SQL Injection Prevention
- Analyst can run `SELECT * FROM users` → Allowed
- Analyst tries `DROP TABLE users` → Blocked
- User tries any SQL → Blocked (no access to query tool)

### 3. Resource Isolation
- User can read `user://profile` → Allowed
- User tries `admin://system` → Blocked
- Public tries `user://profile` → Blocked

### 4. Prompt Template Security
- Admin can use any prompt → Allowed
- Analyst can use `sql_analysis` → Allowed
- User tries `admin_report` → Blocked

## 🎯 Key Security Features

1. **Defense in Depth**: Multiple layers of security checks
2. **Principle of Least Privilege**: Each role gets minimal necessary access
3. **Clear Separation**: Tools, resources, and prompts have distinct access rules
4. **Pattern Matching**: Flexible URI and name pattern controls
5. **Conditional Logic**: Dynamic access based on request content
6. **Audit Trail**: Full logging of all authorization decisions

## 🔧 Customization

### Add New Role
1. Add API key to server:
   ```python
   "scientist-key-999": ["scientist"]
   ```

2. Add policy rules:
   ```yaml
   - name: "scientist_research_access"
     agents:
       roles: ["scientist"]
     tools:
       patterns: ["research_*"]
     resources:
       patterns: ["data://*"]
   ```

### Add New Capability
1. Add to server (tool/resource/prompt)
2. Update policies to control access
3. Test with different roles

This demo shows how MCP Auth Guard provides comprehensive, fine-grained authorization across all MCP capability types while maintaining security and usability.
