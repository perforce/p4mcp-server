"""File query & modify tools."""

from __future__ import annotations

from typing import Annotated, Optional, List, Literal, TYPE_CHECKING

from pydantic import Field
from fastmcp import Context

from ..models import file_models as m
from .common import handle_with_logging, handle_modify_with_delete_gate

if TYPE_CHECKING:
    from ..server import P4MCPServer


def register(server: "P4MCPServer") -> None:
    if "files" not in server.toolsets:
        return

    # ── read ────────────────────────────────────────────────────────────
    @server.mcp.tool(tags=["read", "files"])
    async def query_files(
        action: Annotated[Literal["content", "history", "info", "metadata", "diff", "annotations"], Field(
            description="File query action, metadata includes extra information like optional attributes and file size"
        )],
        file_path: Annotated[str, Field(
            description="Primary file path - required for all actions",
            examples=["//depot/projectX/file.txt", "/local/path/file.txt"],
        )],
        ctx: Context,
        file2: Annotated[Optional[str], Field(
            default=None,
            description="Second file path - required for diff action",
            examples=["//depot/projectX/file2.txt"],
        )] = None,
        diff2: Annotated[bool, Field(
            default=True,
            description="Use p4 diff2 for depot-to-depot diff, false for mixed diff",
        )] = True,
        max_results: Annotated[int, Field(
            default=100, ge=1, le=1000,
            description="Maximum number of results to return",
        )] = 100,
    ) -> dict:
        """Get file content, history, info, diff, annotations (READ permission)"""
        params = m.QueryFilesParams(
            action=action, file_path=file_path,
            file2=file2, diff2=diff2, max_results=max_results,
        )
        return await handle_with_logging(server, "query", "files", params, "query_files", ctx)

    # ── write ───────────────────────────────────────────────────────────
    if server.readonly:
        return

    @server.mcp.tool(tags=["write", "files"])
    async def modify_files(
        action: Annotated[Literal["add", "edit", "delete", "move", "revert", "reconcile", "resolve", "sync"], Field(
            description="File modification action"
        )],
        ctx: Context,
        file_paths: Annotated[Optional[List[str]], Field(
            default=None,
            description="Full depot or client or local paths",
            examples=[["//depot/projectX/file1.txt", "//workspace_name/projectX/file2.txt"]],
        )] = None,
        changelist: Annotated[str, Field(
            default="default",
            description="Changelist ID or 'default'",
            examples=["default", "12345"],
        )] = "default",
        source_paths: Annotated[Optional[List[str]], Field(
            default=None,
            description="Source paths - required for move action",
            examples=[["//depot/projectX/file1.txt"]],
        )] = None,
        target_paths: Annotated[Optional[List[str]], Field(
            default=None,
            description="Target paths - required for move action",
            examples=[["//depot/projectX/file1_renamed.txt"]],
        )] = None,
        mode: Annotated[Literal["auto", "safe", "force", "preview", "theirs", "yours"], Field(
            default="auto",
            description="Resolve mode: auto(-am), safe(-as), force(-af), preview(-n), theirs(-at), yours(-ay)",
        )] = "auto",
        force: Annotated[bool, Field(
            default=False,
            description="Force operation - use with caution",
        )] = False,
    ) -> dict:
        """Add, edit, move, delete, revert, reconcile, resolve, and sync files (WRITE permission)"""
        params = m.ModifyFilesParams(
            action=action, file_paths=file_paths, changelist=changelist,
            source_paths=source_paths, target_paths=target_paths,
            mode=mode, force=force,
        )
        return await handle_modify_with_delete_gate(
            server, "files", params, "modify_files", ctx,
            f"Requires approval to delete files: {', '.join(file_paths or [])}",
        )
