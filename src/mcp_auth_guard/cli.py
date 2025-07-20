#!/usr/bin/env python3
"""Command line interface for MCP Auth Guard."""

import json
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from .policy.loader import PolicyLoader
from .policy.builder import policy, rule
from .schemas.policy import Effect, ConditionOperator

app = typer.Typer(help="MCP Auth Guard - Authorization middleware for MCP tools")
console = Console()


@app.command()
def validate(
    policy_file: Path = typer.Argument(..., help="Path to policy YAML file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Validate a policy file."""
    try:
        policy_config = PolicyLoader.load_from_file(policy_file)
        
        if verbose:
            console.print(Panel.fit(
                f"✅ Policy '{policy_config.name}' is valid\n"
                f"Version: {policy_config.version}\n"
                f"Rules: {len(policy_config.rules)}\n"
                f"Default effect: {policy_config.default_effect}",
                title="Validation Result",
                border_style="green"
            ))
        else:
            console.print(f"✅ Policy '{policy_config.name}' is valid")
            
    except Exception as e:
        console.print(f"❌ Policy validation failed: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def info(
    policy_file: Path = typer.Argument(..., help="Path to policy YAML file")
):
    """Show detailed information about a policy."""
    try:
        policy_config = PolicyLoader.load_from_file(policy_file)
        
        # Basic info
        console.print(Panel.fit(
            f"Name: {policy_config.name}\n"
            f"Description: {policy_config.description or 'N/A'}\n"
            f"Version: {policy_config.version}\n"
            f"Default Effect: {policy_config.default_effect}\n"
            f"Rules: {len(policy_config.rules)}",
            title="Policy Information",
            border_style="blue"
        ))
        
        # Rules table
        if policy_config.rules:
            table = Table(title="Policy Rules")
            table.add_column("Name", style="cyan")
            table.add_column("Effect", style="green")
            table.add_column("Priority", style="yellow")
            table.add_column("Description", style="dim")
            
            for rule_config in sorted(policy_config.rules, key=lambda r: r.priority, reverse=True):
                table.add_row(
                    rule_config.name,
                    rule_config.effect,
                    str(rule_config.priority),
                    rule_config.description or "N/A"
                )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error reading policy: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(..., help="Policy name"),
    output: Path = typer.Option("policy.yaml", "--output", "-o", help="Output file path"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Policy description")
):
    """Create a new policy template."""
    
    # Create a sample policy
    sample_policy = (policy(name)
        .with_description(description or f"Authorization policy for {name}")
        .deny_by_default()
        .add_rule(
            rule("admin_full_access")
            .with_description("Administrators have full access")
            .for_roles("admin")
            .for_tool_patterns("*")
            .allow()
            .with_priority(1000)
            .build()
        )
        .add_rule(
            rule("user_read_access")
            .with_description("Users can list and call read-only tools")
            .for_roles("user")
            .for_tool_patterns("get_*", "list_*", "read_*")
            .for_actions("list", "call")
            .allow()
            .with_priority(500)
            .build()
        )
        .build())
    
    try:
        PolicyLoader.save_to_file(sample_policy, output)
        console.print(f"✅ Created policy template: {output}")
        console.print("Edit the file to customize your authorization rules!")
        
    except Exception as e:
        console.print(f"❌ Error creating policy: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def test(
    policy_file: Path = typer.Argument(..., help="Path to policy YAML file"),
    user_id: str = typer.Option("test_user", "--user", "-u", help="Test user ID"),
    roles: str = typer.Option("user", "--roles", "-r", help="Comma-separated roles"),
    tool_name: str = typer.Option("test_tool", "--tool", "-t", help="Tool name to test"),
    action: str = typer.Option("call", "--action", "-a", help="Action to test")
):
    """Test a policy against specific parameters."""
    try:
        from .policy.engine import PolicyEngine
        from .schemas.auth import AuthContext, AuthMethod
        from .schemas.resource import ToolResource, ResourceContext
        
        # Load policy
        policy_config = PolicyLoader.load_from_file(policy_file)
        engine = PolicyEngine([policy_config])
        
        # Create test contexts
        auth_context = AuthContext(
            user_id=user_id,
            roles=roles.split(","),
            authenticated=True,
            auth_method=AuthMethod.NONE
        )
        
        resource_context = ResourceContext(
            resource_type="tool",
            resource=ToolResource(name=tool_name),
            action=action,
            method=f"tools/{action}"
        )
        
        # Evaluate
        import asyncio
        decision = asyncio.run(engine.evaluate(auth_context, resource_context))
        
        # Show result
        result_color = "green" if decision.allowed else "red"
        result_icon = "✅" if decision.allowed else "❌"
        
        console.print(Panel.fit(
            f"{result_icon} Decision: {'ALLOWED' if decision.allowed else 'DENIED'}\n"
            f"Reason: {decision.reason}\n"
            f"Matched Rule: {decision.matched_rule or 'None'}\n"
            f"Message: {decision.message or 'N/A'}\n"
            f"Evaluation Time: {decision.evaluation_time_ms:.2f}ms\n"
            f"Rules Evaluated: {decision.evaluated_rules}",
            title="Authorization Test Result",
            border_style=result_color
        ))
        
    except Exception as e:
        console.print(f"❌ Test failed: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def format(
    policy_file: Path = typer.Argument(..., help="Path to policy YAML file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (overwrites input if not specified)")
):
    """Format and clean up a policy file."""
    try:
        # Load and re-save to format
        policy_config = PolicyLoader.load_from_file(policy_file)
        output_path = output or policy_file
        PolicyLoader.save_to_file(policy_config, output_path)
        
        console.print(f"✅ Formatted policy file: {output_path}")
        
    except Exception as e:
        console.print(f"❌ Format failed: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def convert(
    input_file: Path = typer.Argument(..., help="Input file (JSON or YAML)"),
    output_file: Path = typer.Argument(..., help="Output file"),
    format: str = typer.Option("yaml", "--format", "-f", help="Output format (yaml/json)")
):
    """Convert between policy file formats."""
    try:
        # Load policy (auto-detect format)
        if input_file.suffix.lower() in ['.yml', '.yaml']:
            with open(input_file, 'r') as f:
                data = yaml.safe_load(f)
        else:
            with open(input_file, 'r') as f:
                data = json.load(f)
        
        policy_config = PolicyLoader.load_from_dict(data)
        
        # Save in requested format
        if format.lower() == 'json':
            with open(output_file, 'w') as f:
                json.dump(policy_config.model_dump(exclude_none=True), f, indent=2)
        else:
            PolicyLoader.save_to_file(policy_config, output_file)
        
        console.print(f"✅ Converted {input_file} → {output_file} ({format.upper()})")
        
    except Exception as e:
        console.print(f"❌ Conversion failed: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    from . import __version__
    console.print(f"MCP Auth Guard v{__version__}")


if __name__ == "__main__":
    app()
