"""Core policy engine for evaluating authorization decisions."""

import logging
import time

from ..schemas.auth import AuthContext
from ..schemas.policy import PolicyConfig
from ..schemas.resource import ResourceContext
from ..schemas.response import AuthDecision, DecisionReason
from .evaluator import PolicyEvaluator

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Main policy engine for authorization decisions."""

    def __init__(self, policies: list[PolicyConfig]):
        """
        Initialize policy engine with a list of policies.

        Args:
            policies: List of policy configurations
        """
        self.policies = policies
        self.evaluator = PolicyEvaluator()

        # Sort policies by priority (higher priority first)
        self._sort_policies()

        logger.info(f"Policy engine initialized with {len(policies)} policies")

    def _sort_policies(self):
        """Sort policies and rules by priority."""
        for policy in self.policies:
            policy.rules.sort(key=lambda r: r.priority, reverse=True)

    async def evaluate(
        self, auth_context: AuthContext, resource_context: ResourceContext
    ) -> AuthDecision:
        """
        Evaluate authorization for a request.

        Args:
            auth_context: Authentication context
            resource_context: Resource being accessed

        Returns:
            Authorization decision
        """
        start_time = time.time()
        evaluated_rules = 0

        logger.debug(
            f"Evaluating authorization for user {auth_context.user_id} "
            f"accessing {resource_context.resource.name}"
        )

        # Check if authentication is required and valid
        if not auth_context.authenticated:
            return AuthDecision(
                allowed=False,
                reason=DecisionReason.AUTHENTICATION_FAILED,
                message="Authentication required",
                evaluated_rules=0,
                evaluation_time_ms=(time.time() - start_time) * 1000,
            )

        # Evaluate each policy
        for policy in self.policies:
            for rule in policy.rules:
                evaluated_rules += 1

                # Check if rule matches
                if await self.evaluator.evaluate_rule(
                    rule, auth_context, resource_context
                ):
                    elapsed_ms = (time.time() - start_time) * 1000

                    logger.debug(
                        f"Rule '{rule.name}' matched with effect: {rule.effect}"
                    )

                    return AuthDecision(
                        allowed=(rule.effect.value == "allow"),
                        reason=DecisionReason.RULE_MATCHED,
                        matched_rule=rule.name,
                        message=f"Matched rule: {rule.name}",
                        evaluated_rules=evaluated_rules,
                        evaluation_time_ms=elapsed_ms,
                    )

        # No rules matched, use default effect
        elapsed_ms = (time.time() - start_time) * 1000
        default_allowed = any(
            (
                p.default_effect.value
                if hasattr(p.default_effect, "value")
                else p.default_effect
            )
            == "allow"
            for p in self.policies
        )

        logger.debug(f"No rules matched, using default effect: {default_allowed}")

        return AuthDecision(
            allowed=default_allowed,
            reason=DecisionReason.DEFAULT_EFFECT,
            message="No matching rules, using default effect",
            evaluated_rules=evaluated_rules,
            evaluation_time_ms=elapsed_ms,
        )

    def add_policy(self, policy: PolicyConfig):
        """Add a new policy to the engine."""
        self.policies.append(policy)
        self._sort_policies()
        logger.info(f"Added policy: {policy.name}")

    def remove_policy(self, policy_name: str) -> bool:
        """Remove a policy by name."""
        for i, policy in enumerate(self.policies):
            if policy.name == policy_name:
                del self.policies[i]
                logger.info(f"Removed policy: {policy_name}")
                return True
        return False

    def get_policy(self, name: str) -> PolicyConfig | None:
        """Get a policy by name."""
        for policy in self.policies:
            if policy.name == name:
                return policy
        return None

    def list_policies(self) -> list[str]:
        """List all policy names."""
        return [p.name for p in self.policies]
