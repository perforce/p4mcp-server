"""Shared helpers for tool registration modules.

Centralises the delete-approval gating logic and result-logging boilerplate
so that every toolset module can stay focused on parameter declaration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from fastmcp import Context
from pydantic import BaseModel, Field, create_model

if TYPE_CHECKING:
    from ..server import P4MCPServer

logger = logging.getLogger(__name__)


def process_and_log(server: "P4MCPServer", tool_name: str, result: dict, ctx: Context) -> None:
    """Log a tool call result through the server's standard pipeline."""
    server.process_tool_logs(tool_name, result, ctx)


async def handle_with_logging(
    server: "P4MCPServer",
    operation: str,
    resource: str,
    params,
    tool_name: str,
    ctx: Context,
) -> dict:
    """Run the handler, log the result, and return it.

    Any benign P4 info/warning messages captured during the operation (e.g.
    "file(s) up-to-date", "not on client") are drained via
    ``pop_last_warnings()`` and attached as an additive top-level ``warnings``
    list when present. This is purely additive: ``status``/``code``/``error``
    are left untouched, and a clean operation omits the ``warnings`` field
    entirely.
    """
    from ..core.connection import pop_last_warnings

    result = await server.handlers.handle(operation, resource, params)
    warnings = pop_last_warnings()
    if warnings and isinstance(result, dict) and "warnings" not in result:
        result["warnings"] = warnings
    process_and_log(server, tool_name, result, ctx)
    return result


async def handle_modify_with_delete_gate(
    server: "P4MCPServer",
    resource: str,
    params,
    tool_name: str,
    ctx: Context,
    delete_warning_msg: str,
) -> dict:
    """Handle a modify operation, intercepting ``delete`` and ``obliterate`` actions for approval.

    If ``params.action`` is ``delete`` or ``obliterate``, the user is prompted
    via ``ctx.elicit`` with PROCEED / CANCEL choices.  The operation only
    executes when the user explicitly selects PROCEED.
    """
    if params.action in ["delete", "obliterate"]:
        result = {"status": "warning", "action": params.action, "message": delete_warning_msg}
        process_and_log(server, tool_name, result, ctx)

        elicit_result = await ctx.elicit(
            message=f"⚠️ This action is irreversible. Do you want to continue?" ,
            response_type=create_model(
                "ConfirmAction",
                select_one=(
                    Literal["PROCEED", "CANCEL"],
                    Field(
                        title=delete_warning_msg,
                        description="Select PROCEED to confirm, or CANCEL to abort.",
                    ),
                ),
            ),
        )

        if elicit_result.action != "accept" or elicit_result.data.select_one != "PROCEED":
            cancelled = {"status": "cancelled", "action": params.action, "message": "Operation cancelled by user."}
            process_and_log(server, tool_name, cancelled, ctx)
            return cancelled

    return await handle_with_logging(server, "modify", resource, params, tool_name, ctx)
