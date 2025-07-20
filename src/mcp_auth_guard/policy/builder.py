"""Type-safe policy builder for creating policies programmatically."""

from typing import List, Optional, Union

from ..schemas.policy import (
    PolicyConfig, PolicyRule, PolicyCondition, AgentMatcher, ToolMatcher, 
    Effect, ConditionOperator
)


class PolicyBuilder:
    """Fluent builder for creating policies programmatically."""
    
    def __init__(self, name: str):
        """Initialize builder with policy name."""
        self.name = name
        self.description: Optional[str] = None
        self.version: str = "1.0"
        self.default_effect: Effect = Effect.DENY
        self.rules: List[PolicyRule] = []
        self.tags: List[str] = []
        self.created_by: Optional[str] = None
    
    def with_description(self, description: str) -> "PolicyBuilder":
        """Set policy description."""
        self.description = description
        return self
    
    def with_version(self, version: str) -> "PolicyBuilder":
        """Set policy version."""
        self.version = version
        return self
    
    def with_default_effect(self, effect: Effect) -> "PolicyBuilder":
        """Set default effect when no rules match."""
        self.default_effect = effect
        return self
    
    def allow_by_default(self) -> "PolicyBuilder":
        """Set default effect to ALLOW."""
        return self.with_default_effect(Effect.ALLOW)
    
    def deny_by_default(self) -> "PolicyBuilder":
        """Set default effect to DENY."""
        return self.with_default_effect(Effect.DENY)
    
    def with_tags(self, *tags: str) -> "PolicyBuilder":
        """Add tags to the policy."""
        self.tags.extend(tags)
        return self
    
    def created_by(self, creator: str) -> "PolicyBuilder":
        """Set policy creator."""
        self.created_by = creator
        return self
    
    def add_rule(self, rule: PolicyRule) -> "PolicyBuilder":
        """Add a rule to the policy."""
        self.rules.append(rule)
        return self
    
    def build(self) -> PolicyConfig:
        """Build the final policy configuration."""
        return PolicyConfig(
            name=self.name,
            description=self.description,
            version=self.version,
            default_effect=self.default_effect,
            rules=self.rules,
            tags=self.tags,
            created_by=self.created_by
        )


class RuleBuilder:
    """Fluent builder for creating policy rules."""
    
    def __init__(self, name: str):
        """Initialize builder with rule name."""
        self.name = name
        self.description: Optional[str] = None
        self.effect: Effect = Effect.ALLOW
        self.agents: Optional[AgentMatcher] = None
        self.tools: Optional[ToolMatcher] = None
        self.actions: List[str] = ["*"]
        self.conditions: List[PolicyCondition] = []
        self.priority: int = 100
    
    def with_description(self, description: str) -> "RuleBuilder":
        """Set rule description."""
        self.description = description
        return self
    
    def allow(self) -> "RuleBuilder":
        """Set effect to ALLOW."""
        self.effect = Effect.ALLOW
        return self
    
    def deny(self) -> "RuleBuilder":
        """Set effect to DENY."""
        self.effect = Effect.DENY
        return self
    
    def for_users(self, *user_ids: str) -> "RuleBuilder":
        """Match specific user IDs."""
        if self.agents is None:
            self.agents = AgentMatcher()
        self.agents.user_id = list(user_ids)
        return self
    
    def for_roles(self, *roles: str) -> "RuleBuilder":
        """Match specific roles."""
        if self.agents is None:
            self.agents = AgentMatcher()
        self.agents.roles = list(roles)
        return self
    
    def for_agents(self, *agent_ids: str) -> "RuleBuilder":
        """Match specific agent IDs."""
        if self.agents is None:
            self.agents = AgentMatcher()
        self.agents.agent_id = list(agent_ids)
        return self
    
    def for_patterns(self, *patterns: str) -> "RuleBuilder":
        """Match agent patterns."""
        if self.agents is None:
            self.agents = AgentMatcher()
        self.agents.patterns = list(patterns)
        return self
    
    def for_tools(self, *tool_names: str) -> "RuleBuilder":
        """Match specific tool names."""
        if self.tools is None:
            self.tools = ToolMatcher()
        self.tools.names = list(tool_names)
        return self
    
    def for_tool_patterns(self, *patterns: str) -> "RuleBuilder":
        """Match tool name patterns."""
        if self.tools is None:
            self.tools = ToolMatcher()
        self.tools.patterns = list(patterns)
        return self
    
    def for_namespaces(self, *namespaces: str) -> "RuleBuilder":
        """Match tool namespaces."""
        if self.tools is None:
            self.tools = ToolMatcher()
        self.tools.namespaces = list(namespaces)
        return self
    
    def for_tool_tags(self, *tags: str) -> "RuleBuilder":
        """Match tool tags."""
        if self.tools is None:
            self.tools = ToolMatcher()
        self.tools.tags = list(tags)
        return self
    
    def for_actions(self, *actions: str) -> "RuleBuilder":
        """Match specific actions."""
        self.actions = list(actions)
        return self
    
    def when(self, field: str, operator: ConditionOperator, value) -> "RuleBuilder":
        """Add a condition to the rule."""
        condition = PolicyCondition(field=field, operator=operator, value=value)
        self.conditions.append(condition)
        return self
    
    def when_equals(self, field: str, value) -> "RuleBuilder":
        """Add an equals condition."""
        return self.when(field, ConditionOperator.EQUALS, value)
    
    def when_in(self, field: str, values: List) -> "RuleBuilder":
        """Add an 'in' condition."""
        return self.when(field, ConditionOperator.IN, values)
    
    def when_contains(self, field: str, value: str) -> "RuleBuilder":
        """Add a contains condition."""
        return self.when(field, ConditionOperator.CONTAINS, value)
    
    def with_priority(self, priority: int) -> "RuleBuilder":
        """Set rule priority."""
        self.priority = priority
        return self
    
    def build(self) -> PolicyRule:
        """Build the final policy rule."""
        return PolicyRule(
            name=self.name,
            description=self.description,
            effect=self.effect,
            agents=self.agents,
            tools=self.tools,
            actions=self.actions,
            conditions=self.conditions,
            priority=self.priority
        )


# Convenience functions for common patterns
def policy(name: str) -> PolicyBuilder:
    """Start building a new policy."""
    return PolicyBuilder(name)


def rule(name: str) -> RuleBuilder:
    """Start building a new rule."""
    return RuleBuilder(name)


def allow_all_for_admins() -> PolicyRule:
    """Create a rule allowing all actions for admin role."""
    return (rule("admin_access")
            .for_roles("admin")
            .for_actions("*")
            .allow()
            .with_priority(1000)
            .build())


def deny_sensitive_tools() -> PolicyRule:
    """Create a rule denying access to sensitive tools."""
    return (rule("deny_sensitive")
            .for_tool_patterns("*admin*", "*delete*", "*destroy*")
            .deny()
            .with_priority(900)
            .build())
