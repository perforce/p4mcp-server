"""Tool registration modules for P4 MCP Server.

Each submodule exposes a ``register(server)`` function that accepts a
:class:`~src.server.P4MCPServer` instance and registers the appropriate
MCP tools on ``server.mcp``.
"""

from .server_tools import register as register_server_tools
from .workspace_tools import register as register_workspace_tools
from .file_tools import register as register_file_tools
from .changelist_tools import register as register_changelist_tools
from .shelve_tools import register as register_shelve_tools
from .job_tools import register as register_job_tools
from .review_tools import register as register_review_tools
from .stream_tools import register as register_stream_tools

ALL_REGISTRARS = [
    register_server_tools,
    register_workspace_tools,
    register_file_tools,
    register_changelist_tools,
    register_shelve_tools,
    register_job_tools,
    register_review_tools,
    register_stream_tools,
]

__all__ = [
    "ALL_REGISTRARS",
    "register_server_tools",
    "register_workspace_tools",
    "register_file_tools",
    "register_changelist_tools",
    "register_shelve_tools",
    "register_job_tools",
    "register_review_tools",
    "register_stream_tools",
]
