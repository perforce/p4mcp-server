from typing import Any, List, Optional
from .common import BaseParams, PaginatedParams
from pydantic import Field, model_validator, field_validator
from enum import Enum
import re


# =============================================================================
# ENUMS
# =============================================================================

class StreamQueryAction(str, Enum):
    LIST = "list"
    GET = "get"
    CHILDREN = "children"
    PARENT = "parent"
    GRAPH = "graph"
    INTEGRATION_STATUS = "integration_status"
    GET_WORKSPACE = "get_workspace"
    LIST_WORKSPACES = "list_workspaces"
    VALIDATE_FILE = "validate_file"
    VALIDATE_SUBMIT = "validate_submit"
    CHECK_RESOLVE = "check_resolve"
    INTERCHANGES = "interchanges"


class StreamModifyAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EDIT_SPEC = "edit_spec"
    RESOLVE_SPEC = "resolve_spec"
    REVERT_SPEC = "revert_spec"
    SHELVE_SPEC = "shelve_spec"
    UNSHELVE_SPEC = "unshelve_spec"
    COPY = "copy"
    MERGE = "merge"
    INTEGRATE = "integrate"
    POPULATE = "populate"
    SWITCH = "switch"
    CREATE_WORKSPACE = "create_workspace"


class StreamType(str, Enum):
    MAINLINE = "mainline"
    DEVELOPMENT = "development"
    SPARSEDEV = "sparsedev"
    RELEASE = "release"
    SPARSEREL = "sparserel"
    TASK = "task"
    VIRTUAL = "virtual"


class SpecResolveMode(str, Enum):
    AUTO = "auto"
    ACCEPT_THEIRS = "accept_theirs"
    ACCEPT_YOURS = "accept_yours"


# =============================================================================
# QUERY PARAMS
# =============================================================================

class QueryStreamsParams(PaginatedParams):
    """Stream query parameters."""

    action: StreamQueryAction = Field(
        description=(
            "Stream query action: "
            "'list' streams, 'get' stream spec, 'children' of a stream, 'parent' of a stream, "
            "'graph' (parent + children), 'integration_status' (p4 istat), "
            "'get_workspace' spec, 'list_workspaces' for a stream, "
            "'validate_file' paths against stream view, 'validate_submit' opened files, "
            "'check_resolve' for pending spec conflicts, 'interchanges' between streams"
        ),
        examples=["list", "get", "children", "parent", "graph", "integration_status",
                   "get_workspace", "list_workspaces", "validate_file", "validate_submit",
                   "check_resolve", "interchanges"],
    )

    # --- Common identifiers ---
    stream_name: Optional[str] = Field(
        default=None,
        description=(
            "Stream depot path (e.g. '//depot/main'). "
            "Required for: get, children, parent, graph, integration_status, "
            "list_workspaces, check_resolve, interchanges"
        ),
        examples=["//depot/main", "//depot/dev"],
    )

    # --- list_streams filters ---
    stream_path: Optional[List[str]] = Field(
        default=None,
        description="Stream path pattern(s) for 'list' action (e.g. ['//depot/...'])",
        examples=[["//depot/..."]],
    )
    filter: Optional[str] = Field(
        default=None,
        description=(
            "Filter expression string for 'list' action (-F flag). "
            "Supports &, |, and parentheses. "
            "E.g. \"Parent=//Ace/MAIN&(Type=development|Type=release)\""
        ),
        examples=["Owner=alice&Type=development"],
    )
    fields: Optional[List[str]] = Field(
        default=None,
        description="Fields to return for 'list' (e.g. ['Stream', 'Owner', 'Name', 'Type'])",
        examples=[["Stream", "Owner", "Name", "Type"]],
    )
    unloaded: bool = Field(
        default=False,
        description="Include unloaded streams (list) or workspaces (list_workspaces)",
    )
    all_streams: bool = Field(
        default=False,
        description="Include virtual streams in 'list' results (-a flag)",
    )
    viewmatch: Optional[str] = Field(
        default=None,
        description=(
            "Single depot file path to filter streams whose views contain this path. "
            "E.g. 'foo.c' or '//depot/path/...'. Supports optional revRange."
        ),
        examples=["//depot/project/..."],
    )

    # --- get_stream options ---
    view_without_edit: bool = Field(
        default=False,
        description="Allow admin to view locked stream without opening for edit (-v flag)",
    )
    at_change: Optional[str] = Field(
        default=None,
        description="Changelist number to retrieve historical stream spec (e.g. '12345')",
        examples=["12345"],
    )

    # --- integration_status options ---
    both_directions: bool = Field(
        default=False,
        description="Show integration status in both directions (to parent and from parent) (-a flag for integration_status)",
    )
    force_refresh: bool = Field(
        default=False,
        description="Force istat to assume cache is stale and search for pending integrations (-c flag for integration_status)",
    )

    # --- workspace queries ---
    workspace: Optional[str] = Field(
        default=None,
        description=(
            "Workspace name for get_workspace, validate_file, validate_submit actions"
        ),
        examples=["my_workspace"],
    )
    template: Optional[str] = Field(
        default=None,
        description="Template workspace for get_workspace",
        examples=["template_ws"],
    )
    user: Optional[str] = Field(
        default=None,
        description="Filter workspaces by user (list_workspaces)",
        examples=["alice"],
    )

    # --- validate ---
    file_paths: Optional[List[str]] = Field(
        default=None,
        description="File paths to validate against stream view (validate_file)",
        examples=[["//depot/main/file.txt"]],
    )
    changelist: Optional[str] = Field(
        default=None,
        description="Changelist to validate (validate_submit) or shelve/unshelve spec",
        examples=["12345"],
    )

    # --- interchanges ---
    reverse: bool = Field(
        default=False,
        description="Reverse comparison direction for interchanges",
    )
    long_output: bool = Field(
        default=False,
        description="Include full changelist descriptions for interchanges (-l flag)",
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum changelists for interchanges",
        examples=[10, 50],
    )

    # --- validators ---
    @field_validator("stream_name")
    @classmethod
    def validate_stream_path_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith("//"):
            raise ValueError("stream_name must be a depot path starting with //")
        return v

    @model_validator(mode="after")
    def validate_required_fields(self):
        a = self.action

        stream_required = {
            StreamQueryAction.GET,
            StreamQueryAction.CHILDREN,
            StreamQueryAction.PARENT,
            StreamQueryAction.GRAPH,
            StreamQueryAction.CHECK_RESOLVE,
            StreamQueryAction.INTERCHANGES,
        }
        if a in stream_required and not self.stream_name:
            raise ValueError(f"stream_name is required for action: {str(a)}")

        if a == StreamQueryAction.VALIDATE_FILE and not self.file_paths:
            raise ValueError("file_paths is required for validate_file action")

        return self


# =============================================================================
# MODIFY PARAMS
# =============================================================================

class ModifyStreamsParams(BaseParams):
    """Stream modification parameters."""

    action: StreamModifyAction = Field(
        description=(
            "Stream modification action: "
            "'create', 'update', 'delete' a stream, "
            "'edit_spec', 'resolve_spec', 'revert_spec', 'shelve_spec', 'unshelve_spec' for spec editing, "
            "'copy', 'merge', 'integrate', 'populate' for propagation, "
            "'switch' workspace stream, 'create_workspace' for a stream"
        ),
        examples=["create", "update", "delete", "merge", "integrate", "copy",
                   "populate", "switch", "create_workspace"],
    )

    # --- Common identifiers ---
    stream_name: Optional[str] = Field(
        default=None,
        description=(
            "Stream depot path (e.g. '//depot/main'). "
            "Required for: create, update, delete, edit_spec, resolve_spec, "
            "revert_spec, switch, create_workspace. "
            "Also used as -S flag for copy/merge/integrate/populate."
        ),
        examples=["//depot/main", "//depot/dev"],
    )

    # --- create_stream / update_stream ---
    stream_type: Optional[str] = Field(
        default=None,
        description="Stream type (required for create): mainline, development, sparsedev, release, sparserel, task, virtual",
        examples=["mainline", "development", "release"],
    )
    parent: Optional[str] = Field(
        default=None,
        description="Parent stream (required for non-mainline create)",
        examples=["//depot/main"],
    )
    name: Optional[str] = Field(
        default=None,
        description="Short display name for the stream",
        examples=["dev-feature-x"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Stream or workspace description",
        examples=["Development stream for feature X"],
    )
    options: Optional[str] = Field(
        default=None,
        description=(
            "Stream options string: 'allsubmit/ownersubmit unlocked/locked "
            "toparent/notoparent fromparent/nofromparent mergedown/mergeany'"
        ),
        examples=["allsubmit unlocked toparent fromparent mergedown"],
    )
    parent_view: Optional[str] = Field(
        default=None,
        description="Parent view treatment: 'inherit' or 'noinherit'",
        examples=["inherit", "noinherit"],
    )
    paths: Optional[List[str]] = Field(
        default=None,
        description="Stream view paths (e.g. ['share ...', 'isolate dir/...'])",
        examples=[["share ...", "isolate dir/..."]],
    )
    remapped: Optional[List[str]] = Field(
        default=None,
        description="Remapped paths (e.g. ['dir/... other_dir/...'])",
        examples=[["dir/... other_dir/..."]],
    )
    ignored: Optional[List[str]] = Field(
        default=None,
        description="Ignored paths (e.g. ['*.tmp', 'temp/...'])",
        examples=[["*.tmp", "temp/..."]],
    )

    # --- spec editing ---
    changelist: Optional[str] = Field(
        default=None,
        description="Changelist for edit_spec, shelve_spec, unshelve_spec, or propagation ops",
        examples=["12345", "default"],
    )
    resolve_mode: Optional[str] = Field(
        default=None,
        description=(
            "Resolve mode for resolve_spec action: "
            "'auto' (default), 'accept_theirs', 'accept_yours'"
        ),
        examples=["auto", "accept_theirs", "accept_yours"],
    )
    target_changelist: Optional[str] = Field(
        default=None,
        description="Target changelist for unshelve_spec",
        examples=["default", "12345"],
    )

    # --- propagation common (copy / merge / integrate / populate) ---
    parent_stream: Optional[str] = Field(
        default=None,
        description="Override parent stream for copy/merge/integrate/populate (-P flag)",
        examples=["//depot/main"],
    )
    branch: Optional[str] = Field(
        default=None,
        description="Branch spec name for integrate/populate (-b flag)",
        examples=["my-branch-spec"],
    )
    file_paths: Optional[List[str]] = Field(
        default=None,
        description="File paths for propagation or validation",
        examples=[["//depot/main/src/..."]],
    )
    preview: bool = Field(
        default=False,
        description="Preview only, don't make changes (-n flag)",
    )
    force: bool = Field(
        default=False,
        description="Force operation (-f or -F flag)",
    )
    reverse: bool = Field(
        default=False,
        description="Reverse direction (-r flag)",
    )
    quiet: bool = Field(
        default=False,
        description="Suppress informational messages (-q flag)",
    )
    max_files: Optional[int] = Field(
        default=None,
        ge=1,
        description="Limit number of files processed (-m flag)",
        examples=[100],
    )
    output_base: bool = Field(
        default=False,
        description=(
            "Show base revision with each scheduled resolve (-Ob flag for merge/integrate) "
            "or display list of files created (-o flag for populate)"
        ),
    )

    # --- copy_stream extras ---
    virtual: bool = Field(
        default=False,
        description="Copy using virtual stream (-v flag, copy only)",
    )

    # --- integrate_stream extras ---
    schedule_branch_resolve: bool = Field(
        default=False,
        description="Schedule 'branch resolves' instead of branching new target files automatically (-Rb flag)",
    )
    integrate_around_deleted: bool = Field(
        default=False,
        description="Integrate around deleted revisions (-Di flag)",
    )
    skip_cherry_picked: bool = Field(
        default=False,
        description="Skip cherry-picked revisions already integrated (-Rs flag)",
    )

    # --- populate_stream extras ---
    source_path: Optional[str] = Field(
        default=None,
        description="Source path for populate",
        examples=["//depot/main/src/..."],
    )
    target_path: Optional[str] = Field(
        default=None,
        description="Target path for populate",
        examples=["//depot/dev/src/..."],
    )

    # --- switch_stream ---
    workspace: Optional[str] = Field(
        default=None,
        description="Workspace name for switch or create_workspace",
        examples=["my_workspace"],
    )

    # --- create_stream_workspace extras ---
    workspace_name: Optional[str] = Field(
        default=None,
        description="Workspace name to create (create_workspace action)",
        examples=["my-stream-ws"],
    )
    root: Optional[str] = Field(
        default=None,
        description="Workspace root directory (create_workspace)",
        examples=["/home/user/workspace"],
    )
    host: Optional[str] = Field(
        default=None,
        description="Host restriction for workspace (create_workspace)",
        examples=["build-server-01"],
    )
    alt_roots: Optional[List[str]] = Field(
        default=None,
        description="Alternate root paths for workspace (create_workspace)",
        examples=[["/tmp/alt1", "/tmp/alt2"]],
    )

    # --- validators ---
    @field_validator("stream_name", "parent", "parent_stream")
    @classmethod
    def validate_depot_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith("//"):
            raise ValueError("Must be a depot path starting with //")
        return v

    @model_validator(mode="after")
    def validate_required_fields(self):
        a = self.action

        # Actions requiring stream_name
        stream_required = {
            StreamModifyAction.CREATE,
            StreamModifyAction.UPDATE,
            StreamModifyAction.DELETE,
            StreamModifyAction.EDIT_SPEC,
            StreamModifyAction.RESOLVE_SPEC,
            StreamModifyAction.REVERT_SPEC,
            StreamModifyAction.SWITCH,
        }
        if a in stream_required and not self.stream_name:
            raise ValueError(f"stream_name is required for action: {str(a)}")

        # create requires stream_type
        if a == StreamModifyAction.CREATE and not self.stream_type:
            raise ValueError("stream_type is required for create action")

        # shelve_spec requires changelist
        if a == StreamModifyAction.SHELVE_SPEC and not self.changelist:
            raise ValueError("changelist is required for shelve_spec action")
        if a == StreamModifyAction.SHELVE_SPEC and self.changelist == "default":
            raise ValueError("shelve_spec requires a numbered changelist (e.g., '1234'), not 'default'. Create a numbered changelist first (e.g. via modify_changelists action='create').")

        # create_workspace requires workspace_name, stream_name, root
        if a == StreamModifyAction.CREATE_WORKSPACE:
            if not self.workspace_name:
                raise ValueError("workspace_name is required for create_workspace action")
            if not self.stream_name:
                raise ValueError("stream_name is required for create_workspace action")
            if not self.root:
                raise ValueError("root is required for create_workspace action")

        return self
