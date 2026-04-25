"""Job query & modify tools."""

from __future__ import annotations

from typing import Annotated, Optional, Literal, TYPE_CHECKING

from pydantic import Field
from fastmcp import Context

from ..models import job_models as m
from .common import handle_with_logging

if TYPE_CHECKING:
    from ..server import P4MCPServer


def register(server: "P4MCPServer") -> None:
    if "jobs" not in server.toolsets:
        return

    # ── read ────────────────────────────────────────────────────────────
    @server.mcp.tool(tags=["read", "jobs"])
    async def query_jobs(
        action: Annotated[Literal["list_jobs", "get_job"], Field(
            description="Job query action"
        )],
        ctx: Context,
        changelist_id: Annotated[Optional[str], Field(
            default=None,
            description="Changelist ID - required for list_jobs action",
            examples=["12345"],
        )] = None,
        job_id: Annotated[Optional[str], Field(
            default=None,
            description="Job ID - required for get_job action",
            examples=["job67890"],
        )] = None,
        max_results: Annotated[int, Field(
            default=100, ge=1, le=1000,
            description="Maximum number of results to return",
        )] = 100,
    ) -> dict:
        """Get jobs from changelist and get job details (READ permission)"""
        params = m.QueryJobsParams(
            action=action, changelist_id=changelist_id,
            job_id=job_id, max_results=max_results,
        )
        return await handle_with_logging(server, "query", "jobs", params, "query_jobs", ctx)

    # ── write ───────────────────────────────────────────────────────────
    if server.readonly:
        return

    @server.mcp.tool(tags=["write", "jobs"])
    async def modify_jobs(
        action: Annotated[Literal["link_job", "unlink_job"], Field(
            description="Job modification action"
        )],
        changelist_id: Annotated[str, Field(
            description="Changelist ID - required for link_job/unlink_job",
            examples=["12345"],
        )],
        job_id: Annotated[str, Field(
            description="Job ID - required for link_job/unlink_job",
            examples=["job67890"],
        )],
        ctx: Context,
    ) -> dict:
        """Link or unlink jobs (WRITE permission)"""
        params = m.ModifyJobsParams(action=action, changelist_id=changelist_id, job_id=job_id)
        return await handle_with_logging(server, "modify", "jobs", params, "modify_jobs", ctx)
