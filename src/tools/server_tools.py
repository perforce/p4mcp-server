"""Server query tools – always registered (no toolset gate)."""

from __future__ import annotations

from typing import Annotated, Literal, TYPE_CHECKING

from pydantic import Field
from fastmcp import Context

from ..models import server_models as m
from .common import handle_with_logging

if TYPE_CHECKING:
    from ..server import P4MCPServer


def register(server: "P4MCPServer") -> None:
    @server.mcp.tool(tags=["read", "server"])
    async def query_server(
        action: Annotated[Literal["server_info", "current_user"], Field(
            description="Get server info or current user information"
        )],
        ctx: Context,
    ) -> dict:
        """Get server info and current user information (READ permission)"""
        params = m.QueryServerParams(action=action)
        return await handle_with_logging(server, "query", "server", params, "query_server", ctx)
