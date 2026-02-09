"""
Schema utilities for MCP client compatibility.

Provides functions to inline $defs/$ref in JSON schemas for strict MCP clients
that don't support JSON Schema's $defs mechanism (GitHub Copilot, etc.).
"""

import copy
from typing import Any, Dict


def resolve_ref(ref: str, defs: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve a $ref pointer to its definition."""
    # $ref format: "#/$defs/ModelName"
    if ref.startswith("#/$defs/"):
        def_name = ref[8:]  # Remove "#/$defs/" prefix
        if def_name in defs:
            return copy.deepcopy(defs[def_name])
    return {"$ref": ref}  # Return as-is if can't resolve


def inline_refs(schema: Dict[str, Any], defs: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively inline all $ref references in a schema."""
    if not isinstance(schema, dict):
        return schema
    
    # If this is a $ref, resolve it
    if "$ref" in schema and len(schema) == 1:
        resolved = resolve_ref(schema["$ref"], defs)
        # Recursively inline any refs in the resolved schema
        return inline_refs(resolved, defs)
    
    # Process all keys recursively
    result = {}
    for key, value in schema.items():
        if key == "$defs":
            # Skip $defs - we're inlining them
            continue
        elif isinstance(value, dict):
            result[key] = inline_refs(value, defs)
        elif isinstance(value, list):
            result[key] = [
                inline_refs(item, defs) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result


def flatten_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten a JSON schema by inlining all $defs references.
    
    This transforms schemas like:
        {
            "$defs": {"MyModel": {...}},
            "properties": {"params": {"$ref": "#/$defs/MyModel"}},
            "required": ["params"]
        }
    
    Into:
        {
            "properties": {"params": {...inlined model...}},
            "required": ["params"]
        }
    
    Args:
        schema: JSON schema dictionary with potential $defs
        
    Returns:
        Flattened schema with all $refs inlined
    """
    if not isinstance(schema, dict):
        return schema
    
    # Extract $defs if present
    defs = schema.get("$defs", {})
    
    # If no $defs, return as-is
    if not defs:
        return schema
    
    # Inline all references
    return inline_refs(schema, defs)


def unwrap_params_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unwrap a schema that has a single 'params' property.
    
    This transforms schemas like:
        {
            "properties": {"params": {actual model schema}},
            "required": ["params"],
            "type": "object"
        }
    
    Into just the model schema directly:
        {actual model schema}
    
    This is useful when the tool wrapper adds unnecessary nesting.
    """
    if not isinstance(schema, dict):
        return schema
    
    props = schema.get("properties", {})
    required = schema.get("required", [])
    
    # Check if this is a wrapper with just 'params'
    if (
        len(props) == 1 
        and "params" in props 
        and required == ["params"]
        and schema.get("type") == "object"
    ):
        # Return the inner params schema
        return props["params"]
    
    return schema


def process_tool_schema(schema: Dict[str, Any], unwrap_params: bool = True) -> Dict[str, Any]:
    """
    Process a tool's input schema for MCP client compatibility.
    
    1. Flattens $defs by inlining all $ref references
    2. Optionally unwraps the 'params' wrapper
    
    Args:
        schema: The tool's inputSchema
        unwrap_params: If True, unwrap single 'params' wrapper
        
    Returns:
        Processed schema compatible with strict MCP clients
    """
    # First flatten any $defs
    flattened = flatten_schema(schema)
    
    # Optionally unwrap the params wrapper
    if unwrap_params:
        flattened = unwrap_params_schema(flattened)
    
    return flattened
