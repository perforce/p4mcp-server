"""Workspace query & modify tools."""

from __future__ import annotations

from typing import Annotated, Optional, List, Literal, TYPE_CHECKING

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
            description="Workspace query action: list returns all workspaces matching filters, get retrieves specific workspace spec, type identifies workspace category, status shows opened files and sync state"
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
            description="Workspace modification action: create makes new workspace, delete removes workspace, update modifies workspace spec, switch changes active workspace"
        )],
        workspace_name: Annotated[str, Field(
            description="Workspace name",
            examples=["my_workspace"],
        )],
        ctx: Context,
        workspace_root: Annotated[Optional[str], Field(
            default=None,
            description="Root path of the workspace",
            examples=["/depot/workspace", "C:\\workspace"],
        )] = None,
        workspace_description: Annotated[Optional[str], Field(
            default=None,
            description="Workspace description",
            examples=["Dev workspace for project X"],
        )] = None,
        workspace_options: Annotated[Optional[str], Field(
            default="noallwrite noclobber nocompress unlocked nomodtime normdir",
            description="Workspace options",
            examples=["noallwrite clobber nocompress unlocked nomodtime normdir"],
        )] = "noallwrite noclobber nocompress unlocked nomodtime normdir",
        workspace_line_end: Annotated[Optional[str], Field(
            default="local",
            description="Line ending style (local, unix, win, mac)",
            examples=["local", "unix"],
        )] = "local",
        workspace_view: Annotated[Optional[List[str]], Field(
            default=None,
            description="View mappings in depot-to-client format",
            examples=[["//depot/... //my_workspace/..."]],
        )] = None,
    ) -> dict:
        """Create/delete workspace, Update workspace specs, and switch active workspace (WRITE permission)"""
        # Reconstruct workspace spec from flat fields
        # Only create spec if explicit fields (not defaults) are provided
        workspace_specs = None
        if any([workspace_root is not None, workspace_description is not None, workspace_view is not None]):
            workspace_specs = m.WorkspaceSpec(
                Name=workspace_name,
                Root=workspace_root,
                Description=workspace_description,
                Options=workspace_options,
                LineEnd=workspace_line_end,
                View=workspace_view
            )
        params = m.ModifyWorkspacesParams(
            action=action,
            workspace_name=workspace_name,
            workspace_root=workspace_root,
            workspace_description=workspace_description,
            workspace_options=workspace_options,
            workspace_line_end=workspace_line_end,
            workspace_view=workspace_view,
            specs=workspace_specs
        )
        return await handle_modify_with_delete_gate(
            server, "workspaces", params, "modify_workspaces", ctx,
            f"Requires approval to delete workspace: {workspace_name}",
        )
