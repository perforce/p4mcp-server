"""File query and modify models."""

from typing import Optional, List
from enum import Enum
from pydantic import Field, field_validator, model_validator
from .common import BaseParams, PaginatedParams, ResolveMode


class FileAction(str, Enum):
    CONTENT = "content"
    HISTORY = "history"
    INFO = "info"
    METADATA = "metadata"
    DIFF = "diff"
    ANNOTATIONS = "annotations"


class FileModifyAction(str, Enum):
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    MOVE = "move"
    REVERT = "revert"
    RECONCILE = "reconcile"
    RESOLVE = "resolve"
    SYNC = "sync"


class QueryFilesParams(PaginatedParams):
    """File query parameters with action-specific validation."""
    action: FileAction = Field(
        description="File query action, metadata includes extra information like optional attributes and file size",
        examples=["content", "history", "info", "metadata", "diff", "annotations"]
    )
    file_path: str = Field(
        min_length=1,
        description="Primary file path - required for all actions",
        examples=["//depot/projectX/file.txt", "/local/path/file.txt"]
    )
    file2: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Second file path - required for diff action",
        examples=["//depot/projectX/file2.txt"]
    )
    diff2: bool = Field(
        default=True,
        description="Use p4 diff2 for depot-to-depot diff, false for mixed diff",
        examples=[True, False]
    )

    @model_validator(mode='after')
    def validate_diff_params(self):
        """Validate diff-specific parameters."""
        if self.action == FileAction.DIFF and not self.file2:
            raise ValueError('file2 is required for diff action')
        return self

    @field_validator('file_path', 'file2')
    @classmethod
    def validate_file_paths(cls, v: Optional[str]) -> Optional[str]:
        """Basic validation for file paths."""
        if v and not (v.startswith('//') or v.startswith('/') or ':' in v):
            raise ValueError('File path must be depot path (//depot/...) or absolute local path')
        return v


class ModifyFilesParams(BaseParams):
    """File modification parameters with comprehensive validation."""
    action: FileModifyAction = Field(
        description="File modification action",
        examples=["add", "edit", "delete", "move", "revert", "reconcile", "resolve", "sync"]
    )
    file_paths: Optional[List[str]] = Field(
        default=None,
        description="Should be full depot or client or local paths",
        examples=[["//depot/projectX/file1.txt", "//workspace_name/projectX/file2.txt", "//workspace_name/...", "/path/to/local/file.txt", "/path/to/workspace/root/...", "//depot/branch/..."]]
    )
    changelist: str = Field(
        default="default",
        description="Changelist ID or 'default' if not provided",
        examples=["default", "12345"]
    )
    source_paths: Optional[List[str]] = Field(
        default=None,
        description="Source paths - required for move action from source branch",
        examples=[["//depot/projectX/file1.txt"]]
    )
    target_paths: Optional[List[str]] = Field(
        default=None,
        description="Target paths - required for move action to target branch",
        examples=[["//depot/projectX/file1_renamed.txt"]]
    )
    mode: Optional[ResolveMode] = Field(
        default=ResolveMode.AUTO,
        description=(
            "Resolve mode for file conflict resolution:\n"
            "  - auto: Attempt automatic resolution, merge if safe (-am).\n"
            "  - safe: Accept only non-conflicting changes from theirs (-as).\n"
            "  - force: Force accept merged result even if conflicts exist (-af).\n"
            "  - preview: Show what would be resolved without making changes (-n).\n"
            "  - theirs: Accept changes from the depot version, overwrite yours (-at).\n"
            "  - yours: Keep your workspace version, ignore depot changes (-ay)."
        ),
        examples=["auto", "safe", "force", "preview", "theirs", "yours"]
    )
    force: bool = Field(
        default=False,
        description="Force operation - use with caution",
        examples=[False, True]
    )

    @model_validator(mode='after')
    def validate_file_action_params(self):
        """Validate parameters based on action type."""
        # Changelist should be default if not provided
        if not self.changelist:
            self.changelist = "default"
        # Most actions require file_paths except sync
        if self.action not in [FileModifyAction.SYNC, FileModifyAction.MOVE, FileModifyAction.RECONCILE, FileModifyAction.RESOLVE] and not self.file_paths:
            raise ValueError(f'file_paths is required for action: {self.action}')

        # Move action requires both source and target paths
        if self.action == FileModifyAction.MOVE:
            if not self.source_paths or not self.target_paths:
                raise ValueError('move action requires both source_paths and target_paths')
            if len(self.source_paths) != len(self.target_paths):
                raise ValueError('source_paths and target_paths must have the same length')

        return self
