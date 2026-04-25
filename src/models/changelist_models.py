"""Changelist query and modify models."""

from typing import Optional, List
from enum import Enum
from pydantic import Field, model_validator
from .common import BaseParams, PaginatedParams


class ChangelistStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"


class ChangelistAction(str, Enum):
    GET = "get"
    LIST = "list"


class ChangelistModifyAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    SUBMIT = "submit"
    DELETE = "delete"
    MOVE_FILES = "move_files"


class QueryChangelistsParams(PaginatedParams):
    """Changelist query parameters."""
    action: ChangelistAction = Field(
        description="Changelist query action",
        examples=["get", "list"]
    )
    changelist_id: Optional[str] = Field(
        default=None,
        description="Changelist ID - required for get action",
        examples=["12345", "default"]
    )
    workspace_name: Optional[str] = Field(
        default=None,
        description="Filter by workspace - for list action",
        examples=["my_workspace"]
    )
    user: Optional[str] = Field(
        default=None,
        description="Filter by user - for list action",
        examples=["alice"]
    )
    status: Optional[ChangelistStatus] = Field(
        default=None,
        description="Filter by status - for list action",
        examples=["pending", "submitted"]
    )
    depot_path: Optional[str] = Field(
        default=None,
        description="Filter by depot path - for list action",
        examples=["//depot/my_workspace/..."]
    )

    @model_validator(mode='after')
    def validate_changelist_id_required(self):
        """Validate changelist_id is provided when required."""
        if self.action == ChangelistAction.GET and not self.changelist_id:
            raise ValueError('changelist_id is required for get action')
        return self


class ModifyChangelistsParams(BaseParams):
    """Changelist modification parameters."""
    action: ChangelistModifyAction = Field(
        description="Changelist modification action",
        examples=["create", "update", "submit", "delete", "move_files"]
    )
    changelist_id: Optional[str] = Field(
        default=None,
        description="Changelist ID - required for most actions except create",
        examples=["12345"]
    )
    description: Optional[str] = Field(
        default="",
        max_length=2000,
        description="Changelist description - required for create, optional for update",
        examples=["Fix bug in authentication module", "Add new feature X"]
    )
    file_paths: Optional[List[str]] = Field(
        default=None,
        description="File paths - required for move_files action to a specific changelist",
        examples=[["//depot/projectX/file1.txt"]]
    )

    @model_validator(mode='after')
    def validate_changelist_params(self):
        """Validate parameters based on action type."""
        # Most actions require changelist_id except create
        if self.action != ChangelistModifyAction.CREATE and not self.changelist_id:
            raise ValueError(f'changelist_id is required for action: {self.action}')

        # Create requires description
        if self.action == ChangelistModifyAction.CREATE and not self.description:
            raise ValueError('description is required for create action')

        # Move files requires file_paths
        if self.action == ChangelistModifyAction.MOVE_FILES and not self.file_paths:
            raise ValueError('file_paths is required for move_files action')

        return self
