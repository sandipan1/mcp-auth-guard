#!/usr/bin/env python3
"""
Policy Management Examples for MCP Auth Guard

Demonstrates different approaches to policy governance and management.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastmcp import FastMCP
from mcp_auth_guard import AuthGuardMiddleware
from mcp_auth_guard.schemas.policy import PolicyConfig
from mcp_auth_guard.policy.loader import PolicyLoader
from mcp_auth_guard.policy.builder import policy, rule


class PolicyManager:
    """Centralized policy management with governance controls."""
    
    def __init__(self, middleware: AuthGuardMiddleware, audit_log: str = "policy_audit.log"):
        self.middleware = middleware
        self.audit_log = audit_log
        self.logger = self._setup_audit_logger()
    
    def _setup_audit_logger(self):
        """Set up audit logging for policy changes."""
        logger = logging.getLogger("policy_audit")
        handler = logging.FileHandler(self.audit_log)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def add_policy(
        self, 
        policy: PolicyConfig, 
        admin_user: str, 
        reason: str = "Policy addition"
    ) -> bool:
        """Add a policy with audit trail."""
        try:
            # Validate policy
            if not policy.name or not policy.rules:
                raise ValueError("Policy must have name and rules")
            
            # Check for conflicts
            existing_names = self.middleware.get_policy_names()
            if policy.name in existing_names:
                raise ValueError(f"Policy {policy.name} already exists")
            
            # Add policy
            self.middleware.add_policy(policy)
            
            # Audit log
            self.logger.info(
                f"POLICY_ADDED: {policy.name} by {admin_user} - {reason} "
                f"- Rules: {len(policy.rules)}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"POLICY_ADD_FAILED: {admin_user} - {e}")
            raise
    
    def remove_policy(
        self,
        policy_name: str,
        admin_user: str,
        reason: str = "Policy removal"
    ) -> bool:
        """Remove a policy with audit trail."""
        try:
            # Safety check - don't remove if it would lock out admins
            if "admin" in policy_name.lower():
                raise ValueError("Cannot remove admin policies for safety")
            
            # Remove policy
            success = self.middleware.remove_policy(policy_name)
            
            if success:
                self.logger.info(
                    f"POLICY_REMOVED: {policy_name} by {admin_user} - {reason}"
                )
            else:
                self.logger.warning(
                    f"POLICY_REMOVE_FAILED: {policy_name} not found - {admin_user}"
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"POLICY_REMOVE_ERROR: {admin_user} - {e}")
            raise
    
    def update_policies_from_git(
        self,
        git_path: str,
        admin_user: str = "git_sync"
    ):
        """GitOps: Update policies from Git repository."""
        try:
            # Load policies from Git path
            new_policies = PolicyLoader.load_from_directory(git_path)
            
            # Validate all policies before applying
            for policy in new_policies:
                if not policy.rules:
                    raise ValueError(f"Policy {policy.name} has no rules")
            
            # Reload all policies
            self.middleware.reload_policies(new_policies)
            
            # Audit log
            self.logger.info(
                f"POLICIES_SYNCED_FROM_GIT: {len(new_policies)} policies "
                f"loaded from {git_path} by {admin_user}"
            )
            
        except Exception as e:
            self.logger.error(f"GIT_SYNC_FAILED: {e}")
            raise


class SecurePolicyAPI:
    """Secure API for policy management."""
    
    def __init__(self, policy_manager: PolicyManager):
        self.policy_manager = policy_manager
        self.admin_api_keys = {"super-admin-key", "policy-admin-key"}
    
    def _authenticate_admin(self, api_key: str) -> str:
        """Authenticate admin user."""
        if api_key not in self.admin_api_keys:
            raise PermissionError("Invalid admin API key")
        return f"admin_{hash(api_key) % 1000}"
    
    async def add_policy_api(
        self,
        policy_data: dict,
        api_key: str,
        reason: str = "API addition"
    ):
        """REST API endpoint for adding policies."""
        admin_user = self._authenticate_admin(api_key)
        
        # Parse and validate policy
        policy = PolicyLoader.load_from_dict(policy_data)
        
        # Add with governance
        return self.policy_manager.add_policy(policy, admin_user, reason)
    
    async def remove_policy_api(
        self,
        policy_name: str,
        api_key: str,
        reason: str = "API removal"
    ):
        """REST API endpoint for removing policies."""
        admin_user = self._authenticate_admin(api_key)
        return self.policy_manager.remove_policy(policy_name, admin_user, reason)


def create_enterprise_governance_example():
    """Example: Enterprise governance model."""
    
    # 1. Create MCP server with policies
    mcp = FastMCP("Enterprise Server")
    
    @mcp.tool()
    def sensitive_operation() -> str:
        return "Sensitive data"
    
    # 2. Load baseline policies from secure location
    baseline_policies = PolicyLoader.load_from_directory("./enterprise_policies/")
    
    # 3. Create middleware with immutable baseline
    middleware = AuthGuardMiddleware(
        policies=baseline_policies,
        enable_audit_logging=True
    )
    
    # 4. Set up governance layer
    policy_manager = PolicyManager(middleware, "enterprise_audit.log")
    
    # 5. Secure API for policy changes
    policy_api = SecurePolicyAPI(policy_manager)
    
    mcp.add_middleware(middleware)
    
    return mcp, policy_manager, policy_api


def create_gitops_governance_example():
    """Example: GitOps governance model."""
    
    # Policies managed in Git repository
    # Changes go through PR review process
    # Automatic deployment on merge
    
    mcp = FastMCP("GitOps Server")
    
    @mcp.tool()
    def production_tool() -> str:
        return "Production data"
    
    # Load policies from Git-managed directory
    git_policies_path = "./git_policies/"
    policies = PolicyLoader.load_from_directory(git_policies_path)
    
    middleware = AuthGuardMiddleware(policies=policies)
    policy_manager = PolicyManager(middleware)
    
    # Simulate Git webhook for policy updates
    async def on_git_push():
        """Called when policies are updated in Git."""
        try:
            policy_manager.update_policies_from_git(
                git_policies_path, 
                admin_user="github_webhook"
            )
            print("✅ Policies updated from Git")
        except Exception as e:
            print(f"❌ Git sync failed: {e}")
    
    mcp.add_middleware(middleware)
    
    return mcp, policy_manager, on_git_push


def create_developer_governance_example():
    """Example: Developer-friendly governance."""
    
    # For development environments
    # Developers can update policies locally
    # Production has stricter controls
    
    mcp = FastMCP("Dev Server")
    
    @mcp.tool()
    def dev_tool() -> str:
        return "Dev data"
    
    # Start with permissive dev policies
    dev_policy = (policy("dev_policy")
        .allow_by_default()
        .add_rule(
            rule("block_dangerous")
            .for_tool_patterns("*delete*", "*destroy*")
            .deny()
            .build()
        )
        .build())
    
    middleware = AuthGuardMiddleware(policies=[dev_policy])
    
    # Developer can add/remove policies easily
    def add_dev_policy(name: str, rules: List):
        """Easy policy addition for development."""
        new_policy = PolicyConfig(name=name, rules=rules, default_effect="allow")
        middleware.add_policy(new_policy)
        print(f"✅ Added dev policy: {name}")
    
    mcp.add_middleware(middleware)
    
    return mcp, add_dev_policy


if __name__ == "__main__":
    print("🏛️ Policy Governance Examples")
    print("=" * 50)
    
    print("\n1. Enterprise Governance Model")
    print("   - Centralized policy management")
    print("   - Audit trails for all changes")
    print("   - Admin authentication required")
    
    print("\n2. GitOps Governance Model")  
    print("   - Policies managed in Git")
    print("   - PR review process")
    print("   - Automatic deployment")
    
    print("\n3. Developer Governance Model")
    print("   - Local policy development")
    print("   - Easy testing and iteration")
    print("   - Production promotion process")
    
    print("\n🔒 Key Governance Principles:")
    print("   • Authentication required for policy changes")
    print("   • Comprehensive audit logging")
    print("   • Safety checks (don't lock out admins)")
    print("   • Version control integration")
    print("   • Environment-specific controls")
