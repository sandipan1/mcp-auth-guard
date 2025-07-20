"""Policy rule evaluator."""

import logging
import re
from fnmatch import fnmatch
from typing import Any

from ..schemas.auth import AuthContext
from ..schemas.policy import ConditionOperator, PolicyCondition, PolicyRule
from ..schemas.resource import ResourceContext

logger = logging.getLogger(__name__)


class PolicyEvaluator:
    """Evaluates policy rules against request context."""

    async def evaluate_rule(
        self,
        rule: PolicyRule,
        auth_context: AuthContext,
        resource_context: ResourceContext,
    ) -> bool:
        """
        Evaluate if a rule matches the given context.

        Args:
            rule: Policy rule to evaluate
            auth_context: Authentication context
            resource_context: Resource context

        Returns:
            True if rule matches, False otherwise
        """
        # Check action match
        if not self._matches_action(rule.actions, resource_context.action):
            return False

        # Check agent match
        if rule.agents and not self._matches_agent(rule.agents, auth_context):
            return False

        # Check capability match based on resource type
        capability_matches = False
        
        # If rule has tools and this is a tool, check tool match
        if rule.tools and resource_context.resource_type == "tools":
            capability_matches = self._matches_tool(rule.tools, resource_context)
        
        # If rule has resources and this is a resource, check resource match  
        elif rule.resources and resource_context.resource_type == "resources":
            capability_matches = self._matches_resource(rule.resources, resource_context)
            
        # If rule has prompts and this is a prompt, check prompt match
        elif rule.prompts and resource_context.resource_type == "prompts":
            capability_matches = self._matches_prompt(rule.prompts, resource_context)
            
        # If rule has tools but resource is not a tool (legacy compatibility)
        elif rule.tools and resource_context.resource_type in ["resources", "prompts"]:
            capability_matches = self._matches_tool(rule.tools, resource_context)
            
        # If no specific matcher for this capability type, skip rule
        elif not (rule.tools or rule.resources or rule.prompts):
            capability_matches = True  # No capability restrictions
        
        if not capability_matches:
            return False

        # Check additional conditions
        if rule.conditions:
            context_data = self._build_evaluation_context(
                auth_context, resource_context
            )
            for condition in rule.conditions:
                if not self._evaluate_condition(condition, context_data):
                    return False

        return True

    def _matches_action(self, rule_actions: list[str], action: str) -> bool:
        """Check if action matches rule actions."""
        if "*" in rule_actions:
            return True

        for rule_action in rule_actions:
            if fnmatch(action, rule_action):
                return True

        return False

    def _matches_agent(self, agent_matcher, auth_context: AuthContext) -> bool:
        """Check if agent matches rule criteria."""
        # Check user_id
        if agent_matcher.user_id:
            user_ids = agent_matcher.user_id
            if isinstance(user_ids, str):
                user_ids = [user_ids]

            matched = False
            for user_id_pattern in user_ids:
                if fnmatch(auth_context.user_id or "", user_id_pattern):
                    matched = True
                    break

            if not matched:
                return False

        # Check roles
        if agent_matcher.roles:
            # Wildcard: match any user with at least one role
            if "*" in agent_matcher.roles:
                if not auth_context.roles or len(auth_context.roles) == 0:
                    return False  # User must have at least one role
            else:
                if not any(role in auth_context.roles for role in agent_matcher.roles):
                    return False

        # Check agent_id
        if agent_matcher.agent_id:
            agent_ids = agent_matcher.agent_id
            if isinstance(agent_ids, str):
                agent_ids = [agent_ids]

            matched = False
            for agent_id_pattern in agent_ids:
                if fnmatch(auth_context.agent_id or "", agent_id_pattern):
                    matched = True
                    break

            if not matched:
                return False

        # Check patterns (against user_id and agent_id)
        if agent_matcher.patterns:
            matched = False
            for pattern in agent_matcher.patterns:
                if fnmatch(auth_context.user_id or "", pattern) or fnmatch(
                    auth_context.agent_id or "", pattern
                ):
                    matched = True
                    break

            if not matched:
                return False

        return True

    def _matches_tool(self, tool_matcher, resource_context: ResourceContext) -> bool:
        """Check if tool matches rule criteria."""
        tool = resource_context.resource

        # Check exact names
        if tool_matcher.names:
            if tool.name not in tool_matcher.names:
                return False

        # Check patterns
        if tool_matcher.patterns:
            matched = False
            for pattern in tool_matcher.patterns:
                if fnmatch(tool.name, pattern):
                    matched = True
                    break

            if not matched:
                return False

        # Check namespaces
        if tool_matcher.namespaces:
            if tool.namespace not in tool_matcher.namespaces:
                return False

        # Check tags
        if tool_matcher.tags:
            if not any(tag in tool.tags for tag in tool_matcher.tags):
                return False

        return True

    def _matches_resource(self, resource_matcher, resource_context: ResourceContext) -> bool:
        """Check if resource matches rule criteria."""
        resource = resource_context.resource

        # Check exact URIs
        if resource_matcher.uris:
            if resource.name not in resource_matcher.uris:
                return False

        # Check URI patterns
        if resource_matcher.patterns:
            matched = False
            for pattern in resource_matcher.patterns:
                if fnmatch(resource.name, pattern):
                    matched = True
                    break

            if not matched:
                return False

        # Check schemes (e.g., user://, admin://, public://)
        if resource_matcher.schemes:
            resource_scheme = resource.name.split("://")[0] if "://" in resource.name else ""
            if resource_scheme not in resource_matcher.schemes:
                return False

        return True

    def _matches_prompt(self, prompt_matcher, resource_context: ResourceContext) -> bool:
        """Check if prompt matches rule criteria."""
        prompt = resource_context.resource

        # Check exact names
        if prompt_matcher.names:
            if prompt.name not in prompt_matcher.names:
                return False

        # Check patterns
        if prompt_matcher.patterns:
            matched = False
            for pattern in prompt_matcher.patterns:
                if fnmatch(prompt.name, pattern):
                    matched = True
                    break

            if not matched:
                return False

        # Check tags
        if prompt_matcher.tags:
            if not any(tag in prompt.tags for tag in prompt_matcher.tags):
                return False

        return True

    def _build_evaluation_context(
        self, auth_context: AuthContext, resource_context: ResourceContext
    ) -> dict:
        """Build context data for condition evaluation."""
        return {
            "user": {
                "id": auth_context.user_id,
                "roles": auth_context.roles,
                "agent_id": auth_context.agent_id,
                "authenticated": auth_context.authenticated,
                "claims": auth_context.claims,
            },
            "tool": {
                "name": resource_context.resource.name,
                "namespace": resource_context.resource.namespace,
                "version": resource_context.resource.version,
                "tags": resource_context.resource.tags,
                "args": resource_context.resource.arguments,
                "metadata": resource_context.resource.metadata,
            },
            "request": {
                "action": resource_context.action,
                "method": resource_context.method,
                "resource_type": resource_context.resource_type,
                "timestamp": resource_context.timestamp,
            },
        }

    def _evaluate_condition(self, condition: PolicyCondition, context: dict) -> bool:
        """Evaluate a single condition against context data."""
        try:
            # Get field value from context
            field_value = self._get_field_value(condition.field, context)
            condition_value = condition.value

            # Evaluate based on operator
            if condition.operator == ConditionOperator.EQUALS:
                return field_value == condition_value
            elif condition.operator == ConditionOperator.NOT_EQUALS:
                return field_value != condition_value
            elif condition.operator == ConditionOperator.IN:
                return field_value in condition_value
            elif condition.operator == ConditionOperator.NOT_IN:
                return field_value not in condition_value
            elif condition.operator == ConditionOperator.CONTAINS:
                return condition_value in str(field_value)
            elif condition.operator == ConditionOperator.NOT_CONTAINS:
                return condition_value not in str(field_value)
            elif condition.operator == ConditionOperator.STARTS_WITH:
                return str(field_value).startswith(str(condition_value))
            elif condition.operator == ConditionOperator.ENDS_WITH:
                return str(field_value).endswith(str(condition_value))
            elif condition.operator == ConditionOperator.REGEX:
                return bool(re.match(str(condition_value), str(field_value)))
            elif condition.operator == ConditionOperator.GT:
                return field_value > condition_value
            elif condition.operator == ConditionOperator.LT:
                return field_value < condition_value
            elif condition.operator == ConditionOperator.GTE:
                return field_value >= condition_value
            elif condition.operator == ConditionOperator.LTE:
                return field_value <= condition_value
            else:
                logger.warning(f"Unknown condition operator: {condition.operator}")
                return False

        except Exception as e:
            logger.warning(f"Error evaluating condition {condition.field}: {e}")
            return False

    def _get_field_value(self, field_path: str, context: dict) -> Any:
        """Get value from context using dot notation field path."""
        parts = field_path.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        return value
