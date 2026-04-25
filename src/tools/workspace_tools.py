"""Workspace query & modify tools."""

from __future__ import annotations

from typing import Annotated, Optional, Literal, TYPE_CHECKING

from pydantic import Field
from fastmcp import Context

from ..models import workspace_models as m
from .common import handle_with_logging, handle_modify_with_delete_gate

if TYPE_CHECKING:
    from ..server import P4MCPServer


def register(server: "P4MCPServer") -> None:
    if "workspaces" not in server.toolsets:
        return

    # ── read ────────────────────────────────────────────────────────────
    @server.mcp.tool(tags=["read", "workspaces"])
    async def query_workspaces(
        action: Annotated[Literal["list", "get", "type", "status"], Field(
            description="Workspace query action"
        )],
        ctx: Context,
        workspace_name: Annotated[Optional[str], Field(
            default=None,
            description="Workspace name - required for get, type, status actions",
            examples=["my_workspace"],
        )] = None,
        user: Annotated[Optional[str], Field(
            default=None,
            description="Filter by user - optional for list action",
            examples=["alice", "bob"],
        )] = None,
        max_results: Annotated[int, Field(
            default=100, ge=1, le=1000,
            description="Maximum number of results to return",
        )] = 100,
    ) -> dict:
        """Get workspace details, list workspaces, check type and status (READ permission)"""
        params = m.QueryWorkspacesParams(
            action=action, workspace_name=workspace_name,
            user=user, max_results=max_results,
        )
        return await handle_with_logging(server, "query", "workspaces", params, "query_workspaces", ctx)

    # ── write ───────────────────────────────────────────────────────────
    if server.readonly:
        return

    @server.mcp.tool(tags=["write", "workspaces"])
    async def modify_workspaces(
        action: Annotated[Literal["create", "delete", "update", "switch"], Field(
            description="Workspace modification action"
        )],
        name: Annotated[str, Field(
            description="Workspace name",
            examples=["my_workspace"],
        )],
        ctx: Context,
        specs: Annotated[Optional[dict], Field(
            default=None,
            description="Workspace specification with keys: Name, Root, Description, Options, LineEnd, View",
            examples=[{"Name": "my_workspace", "Root": "/path/to/root", "View": ["//depot/... //my_workspace/..."]}],
        )] = None,
    ) -> dict:
        """Create/delete workspace, Update workspace specs, and switch active workspace (WRITE permission)"""
        workspace_specs = m.WorkspaceSpec(**specs) if specs else None
        params = m.ModifyWorkspacesParams(action=action, name=name, specs=workspace_specs)
        return await handle_modify_with_delete_gate(
            server, "workspaces", params, "modify_workspaces", ctx,
            f"Requires approval to delete workspace: {name}",
        )
