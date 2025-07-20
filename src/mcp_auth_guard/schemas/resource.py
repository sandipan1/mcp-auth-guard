"""Resource schemas and models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolResource(BaseModel):
    """Represents an MCP tool resource."""
    name: str = Field(..., description="Tool name")
    namespace: Optional[str] = Field(None, description="Tool namespace")
    version: Optional[str] = Field(None, description="Tool version")
    description: Optional[str] = Field(None, description="Tool description")
    tags: List[str] = Field(default_factory=list, description="Tool tags")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ResourceContext(BaseModel):
    """Context for resource being accessed."""
    resource_type: str = Field(..., description="Type of resource (tool, prompt, resource)")
    resource: ToolResource = Field(..., description="The resource being accessed")
    action: str = Field(..., description="Action being performed")
    method: str = Field(..., description="MCP method")
    
    # Request context
    request_id: Optional[str] = Field(None, description="Request identifier")
    timestamp: Optional[float] = Field(None, description="Request timestamp")
    
    model_config = {"arbitrary_types_allowed": True}
