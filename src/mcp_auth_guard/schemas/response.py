"""Response schemas and models."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DecisionReason(str, Enum):
    """Reasons for authorization decisions."""
    RULE_MATCHED = "rule_matched"
    DEFAULT_EFFECT = "default_effect"
    AUTHENTICATION_FAILED = "authentication_failed"
    INVALID_TOKEN = "invalid_token"
    MISSING_CLAIMS = "missing_claims"
    TOOL_NOT_FOUND = "tool_not_found"
    CONDITION_FAILED = "condition_failed"


class AuthDecision(BaseModel):
    """Authorization decision result."""
    allowed: bool = Field(..., description="Whether access is allowed")
    reason: DecisionReason = Field(..., description="Reason for the decision")
    matched_rule: Optional[str] = Field(None, description="Name of the matched rule")
    message: Optional[str] = Field(None, description="Human-readable message")
    
    # Debugging info
    evaluated_rules: int = Field(0, description="Number of rules evaluated")
    evaluation_time_ms: Optional[float] = Field(None, description="Evaluation time in milliseconds")
