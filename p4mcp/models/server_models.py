"""Server query models."""

from typing import Literal
from enum import Enum
from pydantic import Field
from .common import BaseParams


class ServerAction(str, Enum):
    SERVER_INFO = "server_info"
    CURRENT_USER = "current_user"


class QueryServerParams(BaseParams):
    """Server information query parameters."""
    action: ServerAction = Field(
        description="Get server info or current user information",
        examples=["server_info", "current_user"]
    )
