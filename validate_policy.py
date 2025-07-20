#!/usr/bin/env python
"""Standalone policy validator."""

import yaml
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ValidationError
from enum import Enum


class Effect(str, Enum):
    """Policy effect options."""
    ALLOW = "allow"
    DENY = "deny"


class ConditionOperator(str, Enum):
    """Condition operators for policy rules."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"


class PolicyCondition(BaseModel):
    """A condition in a policy rule."""
    field: str = Field(..., description="Field path to evaluate")
    operator: ConditionOperator = Field(..., description="Comparison operator")
    value: Union[str, int, float, bool, List[Any]] = Field(..., description="Value to compare against")


class AgentMatcher(BaseModel):
    """Matches agents based on various criteria."""
    user_id: Optional[Union[str, List[str]]] = Field(None, description="User ID(s) to match")
    roles: Optional[List[str]] = Field(None, description="Roles to match")
    agent_id: Optional[Union[str, List[str]]] = Field(None, description="Agent ID(s) to match")
    patterns: Optional[List[str]] = Field(None, description="Wildcard patterns to match")


class ToolMatcher(BaseModel):
    """Matches tools based on various criteria."""
    names: Optional[List[str]] = Field(None, description="Exact tool names to match")
    patterns: Optional[List[str]] = Field(None, description="Wildcard patterns to match")
    namespaces: Optional[List[str]] = Field(None, description="Tool namespaces to match")
    tags: Optional[List[str]] = Field(None, description="Tool tags to match")


class PolicyRule(BaseModel):
    """A single policy rule."""
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    effect: Effect = Field(..., description="Effect when rule matches")
    
    agents: Optional[AgentMatcher] = Field(None, description="Agent matching criteria")
    tools: Optional[ToolMatcher] = Field(None, description="Tool matching criteria")
    actions: List[str] = Field(default_factory=lambda: ["*"], description="Actions this rule applies to")
    
    conditions: List[PolicyCondition] = Field(
        default_factory=list, 
        description="Additional conditions for this rule"
    )
    
    priority: int = Field(100, description="Rule priority (higher = evaluated first)")


class PolicyConfig(BaseModel):
    """Complete policy configuration."""
    name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    version: str = Field("1.0", description="Policy version")
    
    default_effect: Effect = Field(Effect.DENY, description="Default effect when no rules match")
    
    rules: List[PolicyRule] = Field(..., description="Policy rules")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Policy tags")
    created_by: Optional[str] = Field(None, description="Policy creator")

    model_config = {"use_enum_values": True}


def validate_policy_file(filepath: str):
    """Validate a policy YAML file."""
    try:
        with open(filepath, 'r') as f:
            policy_data = yaml.safe_load(f)
        
        # Validate against schema
        policy = PolicyConfig.model_validate(policy_data)
        print(f'✅ Policy file "{filepath}" is valid!')
        print(f'Policy: {policy.name}')
        print(f'Rules: {len(policy.rules)}')
        for rule in policy.rules:
            print(f'  - {rule.name}: {rule.effect} (priority: {rule.priority})')
        return True
        
    except ValidationError as e:
        print(f'❌ Policy validation failed for "{filepath}":')
        for error in e.errors():
            print(f'  {error["loc"]}: {error["msg"]}')
        return False
    except Exception as e:
        print(f'❌ Error reading "{filepath}": {e}')
        return False


if __name__ == "__main__":
    validate_policy_file("examples/weather_policies.yaml")
