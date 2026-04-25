"""Shelve query & modify tools."""

from __future__ import annotations

from typing import Annotated, Optional, List, Literal, TYPE_CHECKING

from pydantic import Field
from fastmcp import Context

from ..models import shelve_models as m
from .common import handle_with_logging, handle_modify_with_delete_gate

if TYPE_CHECKING:
    from ..server import P4MCPServer


def register(server: "P4MCPServer") -> None:
    if "shelves" not in server.toolsets:
        return

    # ── read ────────────────────────────────────────────────────────────
    @server.mcp.tool(tags=["read", "shelves"])
    async def query_shelves(
        action: Annotated[Literal["list", "diff", "files"], Field(
            description="Shelve query action"
        )],
        ctx: Context,
        changelist_id: Annotated[Optional[str], Field(
            default=None,
            description="Changelist ID - required for diff and files actions",
            examples=["12345"],
        )] = None,
        user: Annotated[Optional[str], Field(
            default=None,
            description="Filter by user - for list action",
            examples=["alice"],
        )] = None,
        max_results: Annotated[int, Field(
            default=100, ge=1, le=1000,
            description="Maximum number of results to return",
        )] = 100,
    ) -> dict:
        """List shelves, get shelve diff and files (READ permission)"""
        params = m.QueryShelvesParams(
            action=action, changelist_id=changelist_id,
            user=user, max_results=max_results,
        )
        return await handle_with_logging(server, "query", "shelves", params, "query_shelves", ctx)

    # ── write ───────────────────────────────────────────────────────────
    if server.readonly:
        return

    @server.mcp.tool(tags=["write", "shelves"])
    async def modify_shelves(
        action: Annotated[Literal["shelve", "unshelve", "update", "delete", "unshelve_to_changelist"], Field(
            description="Shelve modification action"
        )],
        changelist_id: Annotated[str, Field(
            description="Changelist ID",
            examples=["12345"],
        )],
        ctx: Context,
        file_paths: Annotated[Optional[List[str]], Field(
            default=None,
            description="File paths for shelve/unshelve/update/delete",
            examples=[["//depot/projectX/file1.txt"]],
        )] = None,
        target_changelist: Annotated[str, Field(
            default="default",
            description="Target changelist for unshelve operations",
            examples=["default", "54321"],
        )] = "default",
        force: Annotated[bool, Field(
            default=False,
            description="Force operation - use with caution",
        )] = False,
    ) -> dict:
        """Create/delete, update shelves and unshelve files (WRITE permission)"""
        params = m.ModifyShelvesParams(
            action=action, changelist_id=changelist_id,
            file_paths=file_paths, target_changelist=target_changelist,
            force=force,
        )
        return await handle_modify_with_delete_gate(
            server, "shelves", params, "modify_shelves", ctx,
            f"Requires approval to delete shelve for changelist: {changelist_id}",
        )
