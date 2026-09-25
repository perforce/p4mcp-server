"""P4 DAM query parameter models — one class per tool."""

from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from .common import BaseParams


class P4DamTagPath(BaseModel):
    """A single depot path entry for the batch tag operation."""

    path: str = Field(
        description=(
            "Depot path of the asset or folder. "
            "Use '//depot/folder/...' to target all files in a folder recursively."
        ),
        examples=["//my-stream/renders/hero.png"],
    )
    identifier: Optional[str] = Field(
        default=None,
        description=(
            "File revision (changelist number). When set, tags are applied only to "
            "that revision. Cannot be used when propagatable=true."
        ),
        examples=["80748"],
    )


class SearchP4DamAssetsParams(BaseParams):
    """Parameters for query_p4dam_assets (asset search)."""

    search_term: Optional[str] = Field(
        default=None,
        description="Search term. Omit to browse all assets.",
        examples=["monocycle", "logo"],
    )
    project_ids: Optional[List[str]] = Field(
        default=None,
        description="Filter to these project UUIDs",
        examples=[["proj-uuid-1"]],
    )
    repository_ids: Optional[List[str]] = Field(
        default=None,
        description="Filter to these repository UUIDs",
        examples=[["repo-uuid-1", "repo-uuid-2"]],
    )
    path: Optional[List[str]] = Field(
        default=None,
        description=(
            "Wildcard patterns matched against the full depot file path. "
            "Use * as the wildcard (e.g. '//depot/art/*.png'). "
            "Values without a leading/trailing * are treated as substring matches."
        ),
        examples=[["//depot/art/*", "//depot/renders/*.exr"]],
    )
    name: Optional[str] = Field(
        default=None,
        description=(
            "Filename wildcard filter using * (e.g. 'hero*'). "
            "Targets the filename only, unlike search_term which also searches tags and custom attributes."
        ),
        examples=["hero*", "*.fbx"],
    )
    tag: Optional[List[str]] = Field(
        default=None,
        description="Filter by tag(s)",
        examples=[["approved"]],
    )
    file_extension: Optional[List[str]] = Field(
        default=None,
        description="Include only assets with these file extensions (no leading dot)",
        examples=[["png", "jpg"]],
    )
    exclude_file_extension: Optional[List[str]] = Field(
        default=None,
        description="Exclude assets with these file extensions (no leading dot)",
        examples=[["tmp", "bak"]],
    )
    user: Optional[List[str]] = Field(
        default=None,
        description="Filter by uploader username(s)",
        examples=[["alice"]],
    )
    from_size: Optional[int] = Field(
        default=None,
        description="Minimum file size in bytes (inclusive)",
        examples=[1024],
    )
    to_size: Optional[int] = Field(
        default=None,
        description="Maximum file size in bytes (inclusive)",
        examples=[10485760],
    )
    from_date: Optional[str] = Field(
        default=None,
        description="Include assets modified on or after this date (ISO 8601, e.g. '2024-01-01')",
        examples=["2024-01-01"],
    )
    to_date: Optional[str] = Field(
        default=None,
        description="Include assets modified on or before this date (ISO 8601, e.g. '2024-12-31')",
        examples=["2024-12-31"],
    )
    all_revisions: bool = Field(
        default=False,
        description="Include all revisions (default: latest only)",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Maximum number of results (maps to 'limit' in the P4 DAM payload)",
        examples=[10, 50],
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset",
        examples=[0, 10],
    )


class GetP4DamAssetParams(BaseParams):
    """Parameters for query_p4dam_asset (single-asset detail fetch)."""

    depot_path: Optional[str] = Field(
        default=None,
        description=(
            "Full depot path of the asset (e.g. //depot/art/logo.png). "
            "Use when project_id and repository_id are not known. "
            "When project_id and repository_id are provided, prefer path instead."
        ),
        examples=["//depot/art/logo.png"],
    )
    path: Optional[str] = Field(
        default=None,
        description=(
            "Repository-relative path. Use when project_id and repository_id are known. "
            "For helix_classic: full path without leading slashes "
            "(e.g. depot/art/logo.png for //depot/art/logo.png). "
            "For helix_stream: path relative to stream_path "
            "(e.g. art/logo.png when stream_path is //depot/main and the file is //depot/main/art/logo.png)."
        ),
        examples=["depot/art/logo.png", "art/logo.png"],
    )
    stream_path: Optional[str] = Field(
        default=None,
        description=(
            "Stream path for helix_stream repositories (e.g. //depot/main). "
            "Required when the repository has multiple linked streams and the asset is not in the default one."
        ),
        examples=["//depot/main"],
    )
    identifier: Optional[str] = Field(
        default=None,
        description="Changeset identifier. Omit for the latest revision.",
        examples=["10"],
    )
    project_id: Optional[str] = Field(
        default=None,
        description="P4 DAM project short name or UUID.",
        examples=["my-project"],
    )
    repository_id: Optional[str] = Field(
        default=None,
        description="P4 DAM repository short name or UUID.",
        examples=["my-repo"],
    )
    include: Optional[List[str]] = Field(
        default=None,
        description=(
            "Sections to include in the response. Omit for the default set "
            "(commit, latest_commit, custom_attributes, weblinks, asset_bundle, "
            "parent_asset_bundles, asset_bundle_origin, helix_classic_branch_matches, "
            "stream_view_matches, file_review, sprite). "
            "Valid extras: comments, all_comments, file_count, scene_refs."
        ),
        examples=[["commit", "weblinks", "parent_asset_bundles"]],
    )


# ---------------------------------------------------------------------------
# Navigation — projects, repositories, helix classic branches
# ---------------------------------------------------------------------------

class ListP4DamProjectsParams(BaseParams):
    """Parameters for query_p4dam_projects."""

    search_term: Optional[str] = Field(
        default=None,
        description="Filter projects by name, short name, or description.",
        examples=["characters"],
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum number of results.",
        examples=[20],
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset.",
        examples=[0],
    )


class ListP4DamRepositoriesParams(BaseParams):
    """Parameters for query_p4dam_repositories."""

    project_id: str = Field(
        description="Project short name or UUID.",
        examples=["my-project"],
    )
    search_term: Optional[str] = Field(
        default=None,
        description="Filter repositories by short name.",
        examples=["renders"],
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum number of results.",
        examples=[20],
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset.",
        examples=[0],
    )


class ListP4DamHelixClassicBranchesParams(BaseParams):
    """Parameters for query_p4dam_helix_classic_branches."""

    project_id: str = Field(
        description="Project short name or UUID.",
        examples=["my-project"],
    )
    repository_id: str = Field(
        description="Repository short name or UUID (must be a helix_classic repository).",
        examples=["my-classic-repo"],
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum number of results.",
        examples=[20],
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset.",
        examples=[0],
    )


# ---------------------------------------------------------------------------
# Asset bundle CRUD
# ---------------------------------------------------------------------------

class CreateP4DamAssetBundleParams(BaseParams):
    """Parameters for create_p4dam_asset_bundle."""

    depot_path: str = Field(
        description="Depot path for the bundle file. Must end with '.p4bundle'.",
        examples=["//my-stream/bundles/chars-q3.p4bundle"],
    )
    project: str = Field(
        description="Project short name or UUID.",
        examples=["my-project"],
    )
    repository: str = Field(
        description="Repository short name or UUID.",
        examples=["my-repo"],
    )
    view_paths: List[str] = Field(
        description=(
            "Depot paths that define the bundle scope — which files are included. "
            "Must start with '//' (or '-//' to exclude). Use '...' suffix for recursive "
            "inclusion (e.g. '//stream/renders/...'). For helix stream repos every path "
            "must start with stream_path. Max 250 entries."
        ),
        examples=[["//my-stream/renders/...", "//my-stream/textures/..."]],
    )
    stream_path: Optional[str] = Field(
        default=None,
        description="Stream path (e.g. //depot/main). Required for helix stream repositories.",
        examples=["//my-stream/mainline"],
    )
    helix_classic_branch: Optional[str] = Field(
        default=None,
        description="Helix Classic branch short name or UUID. Required for helix classic repositories.",
        examples=["main"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the bundle.",
        examples=["Q3 character renders for review"],
    )
    hero_file_path: Optional[str] = Field(
        default=None,
        description="Depot path of the hero/cover image for this bundle.",
        examples=["//my-stream/renders/hero.png"],
    )


class UpdateP4DamAssetBundleParams(BaseParams):
    """Parameters for update_p4dam_asset_bundle."""

    bundle_id: str = Field(
        description="UUID of the asset bundle to update.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Updated description. Pass null to clear.",
        examples=["Q3 character renders — final review"],
    )
    view_paths: Optional[List[str]] = Field(
        default=None,
        description=(
            "Replacement view paths list. Same rules as for create: must start with '//', "
            "use '...' for recursive inclusion, max 250 entries. Replaces the full existing list."
        ),
        examples=[["//my-stream/renders/...", "//my-stream/textures/hero/..."]],
    )
    hero_file_path: Optional[str] = Field(
        default=None,
        description="Updated hero/cover image depot path.",
        examples=["//my-stream/renders/hero-final.png"],
    )


class DeleteP4DamAssetBundleParams(BaseParams):
    """Parameters for delete_p4dam_asset_bundle."""

    bundle_id: str = Field(
        description="UUID of the asset bundle to delete.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    action: str = Field(default="delete", description="Operation action.")


class SyncP4DamAssetBundleParams(BaseParams):
    """Parameters for sync_p4dam_asset_bundle."""

    view_paths: List[str] = Field(
        description=(
            "Depot paths to sync — the view_paths from the asset bundle. "
            "Obtain from query_p4dam_asset with include=asset_bundle."
        ),
        examples=[["//my-stream/renders/...", "//my-stream/textures/..."]],
    )

    @field_validator("view_paths")
    @classmethod
    def validate_view_paths(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("view_paths must not be empty")
        for path in v:
            if not (path.startswith("//") or path.startswith("-//")):
                raise ValueError(
                    f"Invalid view path {path!r}: each path must start with '//' (include) or '-//' (exclude)"
                )
        return v


# ---------------------------------------------------------------------------
# File review CRUD
# ---------------------------------------------------------------------------

class ListP4DamFileReviewsParams(BaseParams):
    """Parameters for query_p4dam_file_reviews."""

    project_id: str = Field(
        description="Project short name or UUID.",
        examples=["my-project"],
    )
    depot_path: Optional[str] = Field(
        default=None,
        description="Filter reviews by depot path.",
        examples=["//my-stream/renders/hero.png"],
    )
    include: Optional[List[str]] = Field(
        default=None,
        description="Comma-separated sections to include. Valid value: weblinks.",
        examples=[["weblinks"]],
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum number of results.",
        examples=[20],
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset.",
        examples=[0],
    )


class GetP4DamFileReviewParams(BaseParams):
    """Parameters for query_p4dam_file_review."""

    project_id: str = Field(
        description="Project short name or UUID.",
        examples=["my-project"],
    )
    review_id: str = Field(
        description="File review UUID.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class CreateP4DamFileReviewParams(BaseParams):
    """Parameters for create_p4dam_file_review."""

    project_id: str = Field(
        description="Project short name or UUID.",
        examples=["my-project"],
    )
    name: str = Field(
        description="Review name. Must be unique within the project. Length 2–100 characters.",
        examples=["Q3 hero renders — art director pass"],
    )
    depot_path: str = Field(
        description=(
            "Depot path of the file or bundle being reviewed. "
            "Use a .p4bundle path for asset bundle reviews."
        ),
        examples=["//my-stream/renders/hero.png"],
    )
    view_paths: List[str] = Field(
        description=(
            "Depot paths included in the review scope. Same rules as asset bundle view_paths: "
            "must start with '//' (or '-//' to exclude), use '...' for recursive inclusion."
        ),
        examples=[["//my-stream/renders/..."]],
    )
    state: str = Field(
        description=(
            "Workflow state name to place the review in. "
            "Use query_p4dam_projects to find the project's workflow states. "
            "Note: the backend always starts reviews in the first open state regardless of this value."
        ),
        examples=["open"],
    )
    repository: Optional[str] = Field(
        default=None,
        description="Repository short name or UUID.",
        examples=["repo-uuid-1"],
    )
    helix_classic_branch: Optional[str] = Field(
        default=None,
        description="Helix Classic branch UUID. Required for helix_classic repositories.",
        examples=["branch-uuid-1"],
    )
    asset_bundle: Optional[str] = Field(
        default=None,
        description="Asset bundle UUID. Required when depot_path ends in .p4bundle. Auto-detected when omitted.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    hero_file_path: Optional[str] = Field(
        default=None,
        description="Depot path of the cover image for this review.",
        examples=["//my-stream/renders/hero.png"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Review description. Max 5000 characters.",
        examples=["Art director pass on Q3 hero renders"],
    )
    position: Optional[int] = Field(
        default=None,
        description="Sequential position within the workflow state.",
        examples=[1],
    )
    base_commit_id: str = Field(
        description=(
            "Base changeset identifier. Set to the changelist number the user is currently "
            "viewing, or the latest changelist number of the file if not viewing a specific one."
        ),
        examples=["100"],
    )
    head_commit_id: Optional[str] = Field(
        default=None,
        description=(
            "Head changeset identifier. Required for regular file reviews; omit for bundle reviews. "
            "Set to the changelist number the user is currently viewing, or the latest changelist "
            "number of the file if not viewing a specific one."
        ),
        examples=["120"],
    )


class UpdateP4DamFileReviewParams(BaseParams):
    """Parameters for update_p4dam_file_review."""

    project_id: str = Field(
        description="Project short name or UUID.",
        examples=["my-project"],
    )
    review_id: str = Field(
        description="File review UUID.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    state: Optional[str] = Field(
        default=None,
        description="New workflow state name. Transition must be allowed for the current user.",
        examples=["review"],
    )
    name: Optional[str] = Field(
        default=None,
        description="Updated review name. Length 2–100 characters.",
        examples=["Q3 hero renders — final"],
    )
    view_paths: Optional[List[str]] = Field(
        default=None,
        description="Replacement view paths list. Replaces the full existing list.",
        examples=[["//my-stream/renders/...", "//my-stream/textures/hero/..."]],
    )
    hero_file_path: Optional[str] = Field(
        default=None,
        description="Updated cover image depot path.",
        examples=["//my-stream/renders/hero-final.png"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Updated description. Max 5000 characters.",
        examples=["Final art director pass — approved"],
    )
    position: Optional[int] = Field(
        default=None,
        description="Updated sequential position within the workflow state.",
        examples=[2],
    )


class DeleteP4DamFileReviewParams(BaseParams):
    """Parameters for delete_p4dam_file_review."""

    project_id: str = Field(
        description="Project short name or UUID.",
        examples=["my-project"],
    )
    review_id: str = Field(
        description="File review UUID.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    action: str = Field(default="delete", description="Operation action.")


# ---------------------------------------------------------------------------
# Workflows (read-only)
# ---------------------------------------------------------------------------

class ListP4DamWorkflowsParams(BaseParams):
    """Parameters for query_p4dam_workflows."""

    include: Optional[List[str]] = Field(
        default=None,
        description=(
            "Additional sections to embed in each workflow. "
            "Valid values: states, transition_rules, projects."
        ),
        examples=[["states"]],
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum number of results.",
        examples=[20],
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset.",
        examples=[0],
    )


class GetP4DamWorkflowParams(BaseParams):
    """Parameters for query_p4dam_workflow."""

    workflow_id: str = Field(
        description="Workflow short name or UUID.",
        examples=["default_workflow"],
    )
    include: Optional[List[str]] = Field(
        default=None,
        description=(
            "Additional sections to embed. "
            "Valid values: states, transition_rules, projects."
        ),
        examples=[["states", "transition_rules"]],
    )


class ListP4DamWorkflowStatesParams(BaseParams):
    """Parameters for query_p4dam_workflow_states."""

    workflow_id: str = Field(
        description="Workflow short name or UUID.",
        examples=["default_workflow"],
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of results.",
        examples=[50],
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset.",
        examples=[0],
    )


# ---------------------------------------------------------------------------
# Asset tag management
# ---------------------------------------------------------------------------

class UpdateP4DamAssetTagsParams(BaseParams):
    """Parameters for update_p4dam_asset_tags."""

    paths: List[P4DamTagPath] = Field(
        description=(
            "Assets to tag. Each entry requires a depot path; identifier is optional. "
            "Use '//depot/folder/...' to target all files in a folder recursively."
        ),
        examples=[[{"path": "//my-stream/renders/hero.png"}]],
    )
    create: Optional[List[str]] = Field(
        default=None,
        description="User tags to add. Tags are case-insensitive (stored lowercase).",
        examples=[["approved", "q3-final"]],
    )
    delete: Optional[List[str]] = Field(
        default=None,
        description="User tags to remove.",
        examples=[["wip"]],
    )
    delete_auto: Optional[List[str]] = Field(
        default=None,
        description="Auto-generated tags to remove.",
        examples=[["outdated"]],
    )
    propagatable: bool = Field(
        default=True,
        description=(
            "When true (default), tag changes apply to the most recent revision and all future revisions. "
            "When false, changes apply only to the specific revision (identifier) or "
            "the most recent revision. Cannot be true if any path has an identifier."
        ),
    )
    identifier: Optional[str] = Field(
        default=None,
        description="Helix Classic branch short name. Required when assets live in a Helix Classic repository.",
        examples=["main"],
    )


class RegenerateP4DamPreviewParams(BaseParams):
    """Parameters for regenerate_p4dam_preview."""

    depot_path: str = Field(
        description="Depot path of the asset (e.g. //depot/art/logo.png).",
        examples=["//my-stream/renders/hero.png"],
    )
    commit_id: str = Field(
        description="Changeset number of the revision to regenerate.",
        examples=["42"],
    )


class QueryP4DamCustomAttributeTemplatesParams(BaseParams):
    """Parameters for query_p4dam_custom_attribute_templates."""

    project_id: str = Field(
        description="Project short name or UUID.",
        examples=["my-project"],
    )


class P4DamCustomAttributeCreate(BaseModel):
    """A single custom attribute value to set."""

    uuid: str = Field(
        description="Template UUID from query_p4dam_custom_attribute_templates.",
        examples=["5ee7de6c-4cc5-4f8d-9939-82b115a1933d"],
    )
    value: Union[str, List[str]] = Field(
        description=(
            "Value to set. String for text, single-select, and checkbox types. "
            "List of strings for multi-select."
        ),
        examples=["audio"],
    )


class UpdateP4DamAssetCustomAttributesParams(BaseParams):
    """Parameters for update_p4dam_asset_custom_attributes."""

    paths: List[P4DamTagPath] = Field(
        description=(
            "Assets to update. Each entry requires a depot path; identifier is optional. "
            "Use '//depot/folder/...' to target all files in a folder recursively."
        ),
        examples=[[{"path": "//my-stream/renders/hero.png"}]],
    )
    create: Optional[List[P4DamCustomAttributeCreate]] = Field(
        default=None,
        description="Attribute values to set. Each entry must include the template UUID and new value.",
        examples=[[{"uuid": "5ee7de6c-4cc5-4f8d-9939-82b115a1933d", "value": "audio"}]],
    )
    delete: Optional[List[str]] = Field(
        default=None,
        description="Template UUIDs of attributes to remove.",
        examples=[["eb42bb83-f90e-4213-9240-2cf817c11f3e"]],
    )
    propagatable: bool = Field(
        default=True,
        description=(
            "When true (default), changes apply to the most recent revision and all future revisions. "
            "When false, changes apply only to the specific revision or the most recent revision."
        ),
    )


class CreateP4DamCommentParams(BaseParams):
    """Parameters for create_p4dam_comment."""

    type: Literal["file_review", "file_review_file", "commit_file", "comment"] = Field(
        description=(
            "Comment type: "
            "'file_review' — on a file review (asset bundles only); "
            "'file_review_file' — on a specific file inside a file review (asset bundle files only); "
            "'commit_file' — on a regular file, or on an asset bundle without a review; "
            "'comment' — reply to an existing comment."
        ),
    )
    content: str = Field(description="Comment text.")
    project: Optional[str] = Field(
        default=None,
        description="Project UUID or short name. Required for file_review, file_review_file, commit_file.",
    )
    repository: Optional[str] = Field(
        default=None,
        description="Repository UUID or short name. Required for file_review, file_review_file, commit_file.",
    )
    file_review: Optional[str] = Field(
        default=None,
        description="File review UUID. Required for file_review and file_review_file.",
    )
    commit: Optional[str] = Field(
        default=None,
        description="Changeset number (as a string). Required for commit_file.",
        examples=["14"],
    )
    path: Optional[str] = Field(
        default=None,
        description=(
            "Relative file path within the repository (e.g. 'renders/hero.png'). "
            "Required for file_review_file and commit_file."
        ),
    )
    stream_path: Optional[str] = Field(
        default=None,
        description="Stream path (e.g. '//stream/mainline'). Required for commit_file on helix_stream repos.",
    )
    helix_classic_branch: Optional[str] = Field(
        default=None,
        description="Helix Classic branch short name. Required for commit_file on helix_classic repos.",
    )
    comment: Optional[str] = Field(
        default=None,
        description="Parent comment UUID. Required for type 'comment' (reply).",
    )
    @model_validator(mode="after")
    def validate_type_fields(self) -> "CreateP4DamCommentParams":
        t = self.type
        missing = []
        if t in ("file_review", "file_review_file", "commit_file"):
            if not self.project:
                missing.append("project")
            if not self.repository:
                missing.append("repository")
        if t in ("file_review", "file_review_file"):
            if not self.file_review:
                missing.append("file_review")
        if t in ("file_review_file", "commit_file"):
            if not self.path:
                missing.append("path")
        if t == "commit_file":
            if not self.commit:
                missing.append("commit")
        if t == "comment":
            if not self.comment:
                missing.append("comment")
        if missing:
            raise ValueError(f"type '{t}' requires: {', '.join(missing)}")
        return self


class FetchP4DamMediaParams(BaseParams):
    """Parameters for fetch_p4dam_media."""

    url: str = Field(
        description=(
            "URL from query_p4dam_assets or query_p4dam_asset result. "
            "Pass thumbnail_url, preview_url, or file_url. "
            "thumbnail_url and preview_url are only present for image files."
        ),
        examples=["https://dam.example.com/api/p4/files/thumbnail?depot_path=//stream/renders/hero.png&identifier=42"],
    )
