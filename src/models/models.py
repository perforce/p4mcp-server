from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Literal, Union
from enum import Enum
import re

# =============================================================================
# ENUMS FOR BETTER TYPE SAFETY
# =============================================================================

class ServerAction(str, Enum):
    SERVER_INFO = "server_info"
    CURRENT_USER = "current_user"

class WorkspaceAction(str, Enum):
    GET = "get"
    LIST = "list"
    TYPE = "type"
    STATUS = "status"

class FileAction(str, Enum):
    CONTENT = "content"
    HISTORY = "history"
    INFO = "info"
    METADATA = "metadata"
    DIFF = "diff"
    ANNOTATIONS = "annotations"

class ChangelistStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"

class ChangelistAction(str, Enum):
    GET = "get"
    LIST = "list"

class ShelveAction(str, Enum):
    LIST = "list"
    DIFF = "diff"
    FILES = "files"

class JobAction(str, Enum):
    LIST_JOBS = "list_jobs"
    GET_JOB = "get_job"

class WorkspaceModifyAction(str, Enum):
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"
    SWITCH = "switch"

class FileModifyAction(str, Enum):
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    MOVE = "move"
    REVERT = "revert"
    RECONCILE = "reconcile"
    RESOLVE = "resolve"
    SYNC = "sync"

class ChangelistModifyAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    SUBMIT = "submit"
    DELETE = "delete"
    MOVE_FILES = "move_files"

class ShelveModifyAction(str, Enum):
    SHELVE = "shelve"
    UNSHELVE = "unshelve"
    UPDATE = "update"
    DELETE = "delete"
    UNSHELVE_TO_CHANGELIST = "unshelve_to_changelist"

class JobModifyAction(str, Enum):
    LINK_JOB = "link_job"
    UNLINK_JOB = "unlink_job"

class ResolveMode(str, Enum):
    AUTO = "auto"       # -am
    SAFE = "safe"       # -as
    FORCE = "force"     # -af
    PREVIEW = "preview" # -n
    THEIRS = "theirs"   # -at
    YOURS = "yours"     # -ay

# =============================================================================
# BASE MODELS WITH COMMON PATTERNS
# =============================================================================

class BaseParams(BaseModel):
    """Base class for all parameter models with common configuration."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
        use_enum_values=True
    )

class PaginatedParams(BaseParams):
    """Base class for paginated queries."""
    max_results: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results to return"
    )

# =============================================================================
# IMPROVED DATA MODELS
# =============================================================================

class WorkspaceSpec(BaseModel):
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

# =============================================================================
# READ OPERATIONS WITH IMPROVED VALIDATION
# =============================================================================

class QueryServerParams(BaseParams):
    """Server information query parameters."""
    action: ServerAction = Field(
        description="Get server info or current user information",
        examples=["server_info", "current_user"]
    )

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

class QueryShelvesParams(PaginatedParams):
    """Shelve query parameters."""
    action: ShelveAction = Field(
        description="Shelve query action",
        examples=["list", "diff", "files"]
    )
    changelist_id: Optional[str] = Field(
        default=None,
        description="Changelist ID - required for diff and files actions",
        examples=["12345"]
    )
    user: Optional[str] = Field(
        default=None,
        description="Filter by user - for list action",
        examples=["alice"]
    )

    @model_validator(mode='after')
    def validate_changelist_id_for_actions(self):
        """Validate changelist_id for specific actions."""
        if self.action in [ShelveAction.DIFF, ShelveAction.FILES] and not self.changelist_id:
            raise ValueError(f'changelist_id is required for action: {self.action}')
        return self
    
class QueryJobsParams(PaginatedParams):
    """Job query parameters."""
    action: JobAction = Field(
        description="Job query action",
        examples=["list_jobs", "get_job"]
    )
    changelist_id: Optional[str] = Field(
        default=None,
        description="Changelist ID - required for list_jobs action",
        examples=["job2345"]
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Job ID - required for get_job action",
        examples=["job67890"]
    )

    @model_validator(mode='after')
    def validate_changelist_id_required(self):
        """Validate changelist_id is provided when required."""
        if self.action == JobAction.LIST_JOBS and not self.changelist_id:
            raise ValueError('changelist_id is required for list_jobs action')
        return self

    @model_validator(mode='after')
    def validate_job_id_required(self):
        """Validate job_id is provided when required."""
        if self.action == JobAction.GET_JOB and not self.job_id:
            raise ValueError('job_id is required for get_job action')
        return self

# =============================================================================
# MODIFY OPERATIONS WITH ENHANCED VALIDATION
# =============================================================================

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
    def validate_specs_required(self):
        """Validate specs is provided when required."""
        if self.action in [WorkspaceModifyAction.CREATE, WorkspaceModifyAction.UPDATE]:
            if not self.specs:
                raise ValueError(f'specs is required for action: {self.action}')
        return self

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

class ModifyShelvesParams(BaseParams):
    """Shelve modification parameters."""
    action: ShelveModifyAction = Field(
        description="Shelve modification action",
        examples=["shelve", "unshelve", "update", "delete", "unshelve_to_changelist"]
    )
    changelist_id: str = Field(
        description="Changelist ID",
        examples=["12345"]
    )
    file_paths: Optional[List[str]] = Field(
        default=None,
        description="File paths required for shelve/unshelve/update/delete - unused for others",
        examples=[["//depot/projectX/file1.txt"]]
    )
    target_changelist: str = Field(
        default="default",
        description="Target changelist for unshelve operations",
        examples=["default", "54321"]
    )

    force: bool = Field(
        default=False,
        description="Force operation - use with caution",
        examples=[False, True]
    )

class ModifyJobsParams(BaseParams):
    action: JobModifyAction = Field(
        description="Job modification action",
        examples=["link_job", "unlink_job"]
    )
    changelist_id: str = Field(
        default=None,
        description="Changelist ID - required for link_job/unlink_job actions",
        examples=["12345"]
    )
    job_id: str = Field(
        default=None,
        description="Job ID - required for link_job/unlink_job actions",
        examples=["job67890"]
    )

    @model_validator(mode='after')
    def validate_changelist_id_and_job_id(self):
        """Validate changelist_id and job_id are provided when required."""
        if not self.changelist_id and not self.job_id and self.action in ["link_job", "unlink_job"]:
            raise ValueError(f"changelist_id and job_id are required for this {self.action} action")
        return self

# =============================================================================
# DELETE OPERATIONS
# =============================================================================

class ExecuteDeleteParams(BaseParams):
    """Parameters for executing approved delete operations."""
    source_tool: Literal["modify_changelists", "modify_workspaces", "modify_files", "modify_shelves"] = Field(
        description="The source tool that initiated the delete operation",
        examples=["modify_changelists", "modify_workspaces", "modify_files", "modify_shelves"]
    )
    action: Literal["delete"] = Field(
        description="The action to execute - always 'delete' for this operation",
        examples=["delete"]
    )
    changelist_id: Optional[str] = Field(
        default=None,
        description="Changelist ID - required for changelist and shelve operations",
        examples=["12345", "default"]
    )
    workspace_name: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Workspace name - required for workspace operations",
        examples=["my_workspace"]
    )
    file_paths: Optional[List[str]] = Field(
        default=None,
        description="File paths - required for file operations",
        examples=[["//depot/projectX/file1.txt", "//depot/projectX/file2.txt"]]
    )

    operation_id: Optional[str] = Field(
        default=None,
        description="Unique ID for the delete operation - used to retrieve pending operations",
        examples=["op12345"]
    )
    user_confirmed: bool = Field(
        default=False,
        description="Whether the user has confirmed the delete operation",
        examples=[False, True]
    )

    @model_validator(mode='after')
    def validate_required_fields_by_source_tool(self):
        """Validate that required fields are provided based on the source tool."""
        if self.source_tool == "modify_changelists":
            if not self.changelist_id:
                raise ValueError("changelist_id is required for modify_changelists operations")
        
        elif self.source_tool == "modify_workspaces":
            if not self.workspace_name:
                raise ValueError("workspace_name is required for modify_workspaces operations")
        
        elif self.source_tool == "modify_files":
            if not self.file_paths:
                raise ValueError("file_paths is required for modify_files operations")
        
        elif self.source_tool == "modify_shelves":
            if not self.changelist_id:
                raise ValueError("changelist_id is required for modify_shelves operations")
        
        return self

# =============================================================================
# UTILITY MODELS
# =============================================================================

class ValidationError(BaseModel):
    """Standardized validation error response."""
    field: str
    message: str
    invalid_value: Optional[str] = None

class OperationResult(BaseModel):
    """Standardized operation result."""
    success: bool
    message: str
    data: Optional[dict] = None
    errors: Optional[List[ValidationError]] = None