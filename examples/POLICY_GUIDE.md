# Policy Writing Guide

Learn how to create secure, flexible authorization policies for your MCP servers using MCP Auth Guard's intuitive YAML syntax.

## 🎯 Policy Basics

### Policy Structure

Every policy file follows this basic structure:

```yaml
name: "my_service_policy"
description: "Authorization policies for my service"
version: "1.0"
default_effect: "deny"  # Default: deny all unless explicitly allowed

rules:
  - name: "rule_name"
    description: "What this rule does"
    effect: "allow" | "deny"
    agents: {...}      # Who this applies to
    tools: {...}       # Which tools/resources
    actions: [...]     # What actions (list, call)
    conditions: [...]  # Optional conditions
    priority: 100      # Rule priority (higher = evaluated first)
```

### Essential Concepts

- **Default Effect**: `deny` (secure by default) or `allow` (permissive)
- **Rule Priority**: Higher numbers evaluated first (1000 = high, 100 = medium, 1 = low)
- **Effect**: `allow` grants access, `deny` blocks access
- **Actions**: `list` (see tool), `call` (execute tool), `*` (all actions)

## 👥 Agent Matching

Define **who** the rule applies to:

### By Role
```yaml
agents:
  roles: ["admin", "user", "readonly"]
```

### By User ID
```yaml
agents:
  user_id: "specific_user_123"
  # or multiple users
  user_id: ["user1", "user2", "user3"]
```

### By Agent ID
```yaml
agents:
  agent_id: "claude_desktop"
  # or multiple agents
  agent_id: ["claude", "copilot", "cursor"]
```

### By Pattern Matching
```yaml
agents:
  patterns: ["admin_*", "*_service"]  # Wildcard matching
```

## 🛠️ Capability Matching (Tools, Resources, Prompts)

MCP Auth Guard secures **all three types** of MCP capabilities with separate, clear sections:

### Tools (Executable Functions)
```yaml
tools:
  names: ["get_weather", "delete_user", "query_database"]
  patterns: ["get_*", "admin_*"]
  namespaces: ["weather", "database"] 
  tags: ["safe", "readonly"]
```

### Resources (Static Content/Data)
```yaml
resources:
  uris: ["user://profile", "admin://config"]
  patterns: ["public://*", "user://*"]
  schemes: ["user", "admin", "public"]
```

### Prompts (AI Templates)
```yaml
prompts:
  names: ["user_query", "admin_report", "sql_analysis"]
  patterns: ["*_report", "user_*"]
  tags: ["safe", "admin_only"]
```

### Multiple Capability Types in One Rule
```yaml
# Rule affecting all three types
tools:
  names: ["get_data"]
resources:
  patterns: ["data://*"]
prompts:
  names: ["data_analysis"]
actions: ["list", "call", "read", "get"]
```

### Wildcard Access
```yaml
# Admin gets everything
tools:
  patterns: ["*"]      # All tools
resources:
  patterns: ["*"]      # All resources  
prompts:
  patterns: ["*"]      # All prompts
```

## 🎬 Actions & Permissions

Control **what actions** users can perform on tools, resources, and prompts:

### MCP Standard Actions
```yaml
# Tools
actions: ["list"]      # Can see tool exists in listings
actions: ["call"]      # Can execute/invoke tool

# Resources  
actions: ["list"]      # Can see resource exists in listings
actions: ["read"]      # Can read/access resource content

# Prompts
actions: ["list"]      # Can see prompt exists in listings
actions: ["get"]       # Can retrieve/use prompt template

# All capabilities
actions: ["list", "call", "read", "get"]  # All standard actions
actions: ["*"]         # All actions (equivalent to above)
```

### Action Compatibility
```yaml
# Tools support: list, call
# Resources support: list, read  
# Prompts support: list, get

# Use appropriate actions for each type:
tools:
  names: ["get_weather"]
actions: ["list", "call"]    # ✅ Correct for tools

resources:
  uris: ["user://profile"] 
actions: ["list", "read"]    # ✅ Correct for resources

prompts:
  names: ["admin_report"]
actions: ["list", "get"]     # ✅ Correct for prompts

# Or use wildcard for mixed types:
tools:
  patterns: ["*"]
resources:
  patterns: ["*"]
prompts:
  patterns: ["*"]
actions: ["*"]               # ✅ Works for all types
```

## 🔍 Conditional Access

Add **dynamic conditions** based on request context:

### Time-based Access
```yaml
conditions:
  - field: "tool.args.time"
    operator: "equals"
    value: "night"
```

### Argument Validation
```yaml
conditions:
  - field: "tool.args.query"
    operator: "regex"
    value: "^SELECT\\s+.*"  # Only SELECT queries
```

### Role-based Conditions
```yaml
conditions:
  - field: "auth.roles"
    operator: "contains"
    value: "premium"
```

### Multiple Conditions (AND logic)
```yaml
conditions:
  - field: "tool.args.action"
    operator: "not_equals"
    value: "delete"
  - field: "auth.user_id"
    operator: "starts_with"
    value: "trusted_"
```

## 📊 Complete Examples

### Basic Role-based Policy
```yaml
name: "simple_rbac_policy"
description: "Basic role-based access control"
default_effect: "deny"

rules:
  # Admins get everything
  - name: "admin_full_access"
    effect: "allow"
    agents:
      roles: ["admin"]
    tools:
      patterns: ["*"]
    actions: ["*"]
    priority: 1000

  # Users get safe operations
  - name: "user_safe_access"
    effect: "allow"
    agents:
      roles: ["user"]
    tools:
      names: ["read_data", "get_info", "search"]
    actions: ["list", "call"]
    priority: 500

  # Block dangerous operations for everyone except admins
  - name: "block_dangerous"
    effect: "deny"
    agents:
      roles: ["user", "guest"]
    tools:
      patterns: ["delete_*", "admin_*", "*_danger*"]
    actions: ["*"]
    priority: 800
```

### Comprehensive Policy (Tools + Resources + Prompts)
```yaml
name: "comprehensive_policy"
description: "Authorization for all MCP capability types"
default_effect: "deny"

rules:
  # Admins get full access to everything
  - name: "admin_full_access"
    effect: "allow"
    agents:
      roles: ["admin"]
    tools:
      patterns: ["*"]  # All tools, resources, prompts
    actions: ["*"]     # All actions
    priority: 1000

  # Analysts get data access
  - name: "analyst_data_access"
    effect: "allow"
    agents:
      roles: ["analyst"]
    tools:
      names: ["query_database"]  # Tool: Database queries
    resources:
      uris: ["api://logs"]       # Resource: API logs
    prompts:
      names: ["sql_analysis"]    # Prompt: SQL analysis template
    actions: ["list", "call", "read", "get"]
    priority: 700

  # Users get basic access
  - name: "user_basic_access"
    effect: "allow"
    agents:
      roles: ["user"]
    tools:
      names: ["get_user_info"]   # Tool: User information
    resources:
      uris: ["user://profile"]   # Resource: Own profile
    prompts:
      names: ["user_query"]      # Prompt: General query template
    actions: ["list", "call", "read", "get"]
    priority: 500

  # Public resources for all
  - name: "public_resource_access"
    effect: "allow"
    agents:
      roles: ["admin", "analyst", "user"]
    resources:
      patterns: ["public://*"]  # All public resources
    actions: ["list", "read"]
    priority: 400

  # Block admin resources for non-admins
  - name: "block_admin_resources"
    effect: "deny"
    agents:
      roles: ["analyst", "user"]
    tools:
      patterns: [
        "admin://*",          # Admin resources
        "admin_*"             # Admin prompts
      ]
    actions: ["*"]
    priority: 900

  # SQL injection prevention
  - name: "safe_sql_only"
    effect: "allow"
    agents:
      roles: ["analyst"]
    tools:
      names: ["query_database"]
    actions: ["call"]
    conditions:
      - field: "tool.args.sql"
        operator: "regex"
        value: "^\\s*SELECT\\s+.*"  # Only SELECT statements
    priority: 750
```

### Time-based Access Policy
```yaml
name: "time_based_policy"
description: "Time-sensitive access control"
default_effect: "deny"

rules:
  # Admins always have access
  - name: "admin_always"
    effect: "allow"
    agents:
      roles: ["admin"]
    tools:
      patterns: ["*"]
    actions: ["*"]
    priority: 1000

  # Business hours access for users
  - name: "business_hours_access"
    effect: "allow"
    agents:
      roles: ["user"]
    tools:
      patterns: ["business_*"]
    actions: ["list", "call"]
    conditions:
      - field: "context.time.hour"
        operator: "gte"
        value: 9
      - field: "context.time.hour"
        operator: "lte"
        value: 17
    priority: 500

  # Emergency access after hours
  - name: "emergency_after_hours"
    effect: "allow"
    agents:
      roles: ["oncall"]
    tools:
      names: ["emergency_alert", "system_status"]
    actions: ["list", "call"]
    conditions:
      - field: "context.time.hour"
        operator: "not_in"
        value: [9, 10, 11, 12, 13, 14, 15, 16, 17]
    priority: 400
```

## ⚙️ Available Operators

### Comparison Operators
- `equals` - Exact match
- `not_equals` - Not equal
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than  
- `lte` - Less than or equal

### String Operators
- `contains` - String contains substring
- `not_contains` - String doesn't contain substring
- `starts_with` - String starts with prefix
- `ends_with` - String ends with suffix
- `regex` - Regular expression match

### List Operators
- `in` - Value is in list
- `not_in` - Value is not in list

## 🏗️ Best Practices

### 1. Security-First Design
```yaml
default_effect: "deny"  # Always deny by default
```

### 2. Clear Priority Ordering
```yaml
# High priority for security rules
- name: "block_dangerous"
  priority: 900
  effect: "deny"

# Medium priority for role access
- name: "user_access"
  priority: 500
  effect: "allow"

# Low priority for fallbacks
- name: "default_readonly"
  priority: 100
  effect: "allow"
```

### 3. Descriptive Names & Comments
```yaml
- name: "analyst_select_only_queries"
  description: "Allow analysts to run SELECT queries but block writes"
  # This prevents data modification by non-admin users
```

### 4. Specific Tool Matching
```yaml
# Good: Specific
tools:
  names: ["get_user_data", "search_records"]

# Avoid: Too broad
tools:
  patterns: ["*"]  # Unless for admin roles
```

### 5. Layered Security
```yaml
rules:
  # 1. Block dangerous operations first
  - name: "block_delete"
    effect: "deny"
    priority: 900

  # 2. Allow specific access
  - name: "allow_read"
    effect: "allow"
    priority: 500

  # 3. Catch-all deny (redundant with default_effect but explicit)
  - name: "deny_everything_else"
    effect: "deny"
    priority: 1
```

## 🧪 Testing Your Policies

### 1. Use the Policy Validator
```bash
cd examples
python -c "
import yaml
from mcp_auth_guard.schemas.policy import PolicyConfig

with open('my_policy.yaml') as f:
    policy_data = yaml.safe_load(f)
    
try:
    policy = PolicyConfig.model_validate(policy_data)
    print('✅ Policy is valid!')
except Exception as e:
    print(f'❌ Policy error: {e}')
"
```

### 2. Test with Real Scenarios
Create test cases for each role:

```python
# Test admin access
test_cases = [
    {"role": "admin", "tool": "delete_user", "should_allow": True},
    {"role": "user", "tool": "delete_user", "should_allow": False},
    {"role": "user", "tool": "read_data", "should_allow": True},
]
```

### 3. Review Policy Logic
- Are deny rules high priority?
- Do allow rules have appropriate conditions?
- Is the default effect secure?
- Are patterns specific enough?

## 🚨 Common Pitfalls

### ❌ Overly Permissive Patterns
```yaml
# BAD: Too broad
tools:
  patterns: ["*"]
agents:
  roles: ["user"]  # Users get everything!
```

### ❌ Wrong Priority Order  
```yaml
# BAD: Allow rule has higher priority than deny
- name: "allow_all"
  priority: 900
  effect: "allow"

- name: "block_dangerous"  
  priority: 100  # Too low!
  effect: "deny"
```

### ❌ Missing Conditions
```yaml
# BAD: No validation on SQL queries
- name: "database_access"
  effect: "allow"
  tools: ["execute_query"]
  # Should have conditions to prevent DROP TABLE!
```

### ✅ Better Approach
```yaml
# GOOD: Specific access with validation
- name: "analyst_select_queries"
  effect: "allow"
  agents:
    roles: ["analyst"]
  tools:
    names: ["execute_query"]
  conditions:
    - field: "tool.args.query"
      operator: "regex"
      value: "^\\s*SELECT\\s+.*"
  priority: 500
```

## 📚 Advanced Topics

### Custom Field Validation
```yaml
conditions:
  - field: "tool.args.file_path"
    operator: "not_contains"
    value: "../"  # Prevent path traversal
```

### Multi-tenant Access
```yaml
conditions:
  - field: "auth.tenant_id"
    operator: "equals"
    value: "{{auth.user_tenant}}"  # Same tenant only
```

### Rate Limiting (if supported)
```yaml
conditions:
  - field: "context.rate_limit.calls_per_minute"
    operator: "lte"
    value: 10
```

## 🔗 Next Steps

- **Try the examples**: Start with [weather service policies](weather_service/weather_policies.yaml)
- **Read the schemas**: Check `src/mcp_auth_guard/schemas/policy.py`
- **Test thoroughly**: Use the test client to verify your policies
- **Monitor in production**: Enable audit logging to track policy decisions

## 📖 Related Documentation

- [Weather Service Example](weather_service/) - Complete working example (tools only)
- [Comprehensive Server Example](comprehensive_server.py) - Tools, resources, and prompts example
- [Transport Guide](TRANSPORT_GUIDE.md) - Authentication across transports
- [API Documentation](../docs/) - Full API reference

## 🧪 Try the Examples

### Weather Service (Tools Only)
```bash
cd examples/weather_service
python weather_server.py
python test_client.py
```

### Comprehensive Demo (All Capability Types)
```bash
cd examples
python comprehensive_server.py
# Test with different API keys to see resource/prompt authorization
```
