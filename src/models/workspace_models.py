"""Workspace query and modify models."""

from typing import Optional, List
from enum import Enum
from pydantic import Field, field_validator, model_validator, ConfigDict
from .common import BaseParams, PaginatedParams
import re


class WorkspaceAction(str, Enum):
    GET = "get"
    LIST = "list"
    TYPE = "type"
    STATUS = "status"


class WorkspaceModifyAction(str, Enum):
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"
    SWITCH = "switch"


class WorkspaceSpec(BaseParams):
    """Workspace specification with validation."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    Name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the workspace if not provided, consider the current workspace - mandatory field",
        examples=["my_workspace", "dev_branch_workspace"]
    )
    Root: Optional[str] = Field(
        default=None,
        description="Root path of the workspace",
        examples=["/depot/workspace", "C:\\workspace"]
    )
    Description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Workspace description",
        examples=["Workspace for project X", "Development workspace"]
    )
    Options: Optional[str] = Field(
        default="noallwrite noclobber nocompress unlocked nomodtime normdir",
        description="Workspace options",
        examples=["noallwrite clobber nocompress unlocked nomodtime normdir"]
    )
    LineEnd: Optional[str] = Field(
        default="local",
        description="Line ending style",
        examples=["local", "unix", "win", "mac"]
    )
    View: Optional[List[str]] = Field(
        default=None,
        description="View mappings - each mapping should follow depot-to-client format",
        examples=[["//depot/projectX/... //my_workspace/projectX/..."]]
    )

    @field_validator('Name')
    @classmethod
    def validate_workspace_name(cls, v: str) -> str:
        """Validate workspace name follows Perforce naming conventions."""
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Workspace name can only contain alphanumeric characters, dots, underscores, and hyphens')
        return v

    @field_validator('View')
    @classmethod
    def validate_view_mappings(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate view mappings format."""
        if v:
            for mapping in v:
                if not re.match(r'^//[\w/.-]+/\.\.\.\s+//[\w/.-]+/\.\.\.$', mapping.replace('\\', '/')):
                    raise ValueError(f'Invalid view mapping format: {mapping}')
        return v


class QueryWorkspacesParams(PaginatedParams):
    """Workspace query parameters with conditional validation."""
    action: WorkspaceAction = Field(
        description="Workspace query action",
        examples=["list", "get", "type", "status"]
    )
    workspace_name: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Workspace name - required for get, type, status actions",
        examples=["my_workspace"]
    )
    user: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Filter by user - optional for list action",
        examples=["alice", "bob"]
    )

    @model_validator(mode='after')
    def validate_workspace_name_required(self):
        """Validate workspace_name is provided when required."""
        if self.action in [WorkspaceAction.GET, WorkspaceAction.TYPE, WorkspaceAction.STATUS]:
            if not self.workspace_name:
                raise ValueError(f'workspace_name is required for action: {self.action}')
        return self


class ModifyWorkspacesParams(BaseParams):
    """Workspace modification parameters."""
    action: WorkspaceModifyAction = Field(
        description="Workspace modification action",
        examples=["create", "update", "delete", "switch"]
    )
    name: str = Field(
        min_length=1,
        description="Workspace name",
        examples=["my_workspace"]
    )
    specs: Optional[WorkspaceSpec] = Field(
        default=None,
        description="Workspace specification - required for create and update actions"
    )

    @model_validator(mode='after')
    def validate_workspace_params(self):
        """Validate parameters based on action type."""
        if self.action in [WorkspaceModifyAction.CREATE, WorkspaceModifyAction.UPDATE]:
            if not self.specs:
                raise ValueError(f'specs is required for action: {self.action}')
        elif self.action == WorkspaceModifyAction.DELETE:
            if not self.name:
                raise ValueError('name is required for delete action')
        return self
