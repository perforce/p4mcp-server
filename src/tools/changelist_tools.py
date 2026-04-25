"""Changelist query & modify tools."""

from __future__ import annotations

from typing import Annotated, Optional, List, Literal, TYPE_CHECKING

from pydantic import Field
from fastmcp import Context

from ..models import changelist_models as m
from .common import handle_with_logging, handle_modify_with_delete_gate

if TYPE_CHECKING:
    from ..server import P4MCPServer


def register(server: "P4MCPServer") -> None:
    if "changelists" not in server.toolsets:
        return

    # ── read ────────────────────────────────────────────────────────────
    @server.mcp.tool(tags=["read", "changelists"])
    async def query_changelists(
        action: Annotated[Literal["get", "list"], Field(
            description="Changelist query action"
        )],
        ctx: Context,
        changelist_id: Annotated[Optional[str], Field(
            default=None,
            description="Changelist ID - required for get action",
            examples=["12345", "default"],
        )] = None,
        workspace_name: Annotated[Optional[str], Field(
            default=None,
            description="Filter by workspace - for list action",
            examples=["my_workspace"],
        )] = None,
        user: Annotated[Optional[str], Field(
            default=None,
            description="Filter by user - for list action",
            examples=["alice"],
        )] = None,
        status: Annotated[Optional[Literal["pending", "submitted"]], Field(
            default=None,
            description="Filter by status - for list action",
        )] = None,
        depot_path: Annotated[Optional[str], Field(
            default=None,
            description="Filter by depot path - for list action",
            examples=["//depot/my_workspace/..."],
        )] = None,
        max_results: Annotated[int, Field(
            default=100, ge=1, le=1000,
            description="Maximum number of results to return",
        )] = 100,
    ) -> dict:
        """Get changelist details and list changelists (READ permission)"""
        params = m.QueryChangelistsParams(
            action=action, changelist_id=changelist_id,
            workspace_name=workspace_name, user=user,
            status=status, depot_path=depot_path,
            max_results=max_results,
        )
        return await handle_with_logging(server, "query", "changelists", params, "query_changelists", ctx)

    # ── write ───────────────────────────────────────────────────────────
    if server.readonly:
        return

    @server.mcp.tool(tags=["write", "changelists"])
    async def modify_changelists(
        action: Annotated[Literal["create", "update", "submit", "delete", "move_files"], Field(
            description="Changelist modification action"
        )],
        ctx: Context,
        changelist_id: Annotated[Optional[str], Field(
            default=None,
            description="Changelist ID - required for most actions except create",
            examples=["12345"],
        )] = None,
        description: Annotated[str, Field(
            default="",
            description="Changelist description - required for create, optional for update",
            examples=["Fix bug in authentication module", "Add new feature X"],
        )] = "",
        file_paths: Annotated[Optional[List[str]], Field(
            default=None,
            description="File paths - required for move_files action",
            examples=[["//depot/projectX/file1.txt"]],
        )] = None,
    ) -> dict:
        """Create/delete changelists, update changelists and organize files/jobs (WRITE permission)"""
        params = m.ModifyChangelistsParams(
            action=action, changelist_id=changelist_id,
            description=description, file_paths=file_paths,
        )
        return await handle_modify_with_delete_gate(
            server, "changelists", params, "modify_changelists", ctx,
            f"Requires approval to delete changelist: {changelist_id}",
        )
