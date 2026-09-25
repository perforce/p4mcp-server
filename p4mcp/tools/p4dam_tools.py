"""P4 DAM tools."""

from __future__ import annotations

from typing import Annotated, List, Literal, Optional, TYPE_CHECKING

from ..models.p4dam_models import P4DamTagPath

from fastmcp import Context
from pydantic import Field

from ..models import p4dam_models as p4dam_m
from .common import handle_with_logging, handle_modify_with_delete_gate

if TYPE_CHECKING:
    from ..server import P4MCPServer


def register(server: "P4MCPServer") -> None:
    if "p4dam" not in server.toolsets:
        return
    if not server.p4dam_api_key:
        import logging
        logging.getLogger(__name__).warning(
            "P4 DAM toolset skipped: P4DAM_API_KEY is not set. "
            "Set P4DAM_API_KEY to enable P4 DAM tools."
        )
        return

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_assets(
        ctx: Context,
        search_term: Annotated[Optional[str], Field(
            default=None,
            description="Search term. Searches across filename, tags, and custom attributes. Omit to browse all assets.",
            examples=["monocycle", "logo"],
        )] = None,
        project_ids: Annotated[Optional[List[str]], Field(
            default=None,
            description="Filter to these project UUIDs (UUID only — use query_p4dam_projects to resolve a short name to a UUID first).",
            examples=[["proj-uuid-1"]],
        )] = None,
        repository_ids: Annotated[Optional[List[str]], Field(
            default=None,
            description="Filter to these repository UUIDs (UUID only — use query_p4dam_repositories to resolve a short name to a UUID first).",
            examples=[["repo-uuid-1"]],
        )] = None,
        path: Annotated[Optional[List[str]], Field(
            default=None,
            description=(
                "Wildcard patterns matched against the full depot file path. "
                "Use * as the wildcard (e.g. '//depot/art/*.png'). "
                "Values without a leading/trailing * are treated as substring matches."
            ),
            examples=[["//depot/art/*", "//depot/renders/*.exr"]],
        )] = None,
        name: Annotated[Optional[str], Field(
            default=None,
            description=(
                "Filename wildcard filter using * (e.g. 'hero*'). "
                "Targets the filename only, unlike search_term which also searches tags and custom attributes."
            ),
            examples=["hero*", "*.fbx"],
        )] = None,
        tag: Annotated[Optional[List[str]], Field(
            default=None,
            description="Filter by tag(s)",
            examples=[["hero", "q3"]],
        )] = None,
        file_extension: Annotated[Optional[List[str]], Field(
            default=None,
            description="Include only assets with these file extensions (no leading dot)",
            examples=[["png", "jpg"]],
        )] = None,
        exclude_file_extension: Annotated[Optional[List[str]], Field(
            default=None,
            description="Exclude assets with these file extensions (no leading dot)",
            examples=[["tmp", "bak"]],
        )] = None,
        user: Annotated[Optional[List[str]], Field(
            default=None,
            description="Filter by uploader username(s)",
            examples=[["alice"]],
        )] = None,
        from_size: Annotated[Optional[int], Field(
            default=None,
            description="Minimum file size in bytes (inclusive)",
            examples=[1024],
        )] = None,
        to_size: Annotated[Optional[int], Field(
            default=None,
            description="Maximum file size in bytes (inclusive)",
            examples=[10485760],
        )] = None,
        from_date: Annotated[Optional[str], Field(
            default=None,
            description="Include assets modified on or after this date (ISO 8601, e.g. '2024-01-01')",
            examples=["2024-01-01"],
        )] = None,
        to_date: Annotated[Optional[str], Field(
            default=None,
            description="Include assets modified on or before this date (ISO 8601, e.g. '2024-12-31')",
            examples=["2024-12-31"],
        )] = None,
        all_revisions: Annotated[bool, Field(
            default=False,
            description="Include all revisions (default: latest only)",
        )] = False,
        max_results: Annotated[int, Field(
            default=10,
            ge=1,
            le=1000,
            description="Maximum number of results",
        )] = 10,
        offset: Annotated[int, Field(
            default=0,
            ge=0,
            description="Pagination offset",
        )] = 0,
    ) -> dict:
        """Search P4 DAM assets. Supports filtering by keyword, filename, tag, file
        type, depot path, project, repository, uploader, file size, and date range.
        Returns a list of matching assets with metadata and URLs.
        Use when you don't have a specific depot path yet.
        For full metadata on a known asset, use query_p4dam_asset instead."""
        params = p4dam_m.SearchP4DamAssetsParams(
            search_term=search_term,
            project_ids=project_ids,
            repository_ids=repository_ids,
            path=path,
            name=name,
            tag=tag,
            file_extension=file_extension,
            exclude_file_extension=exclude_file_extension,
            user=user,
            from_size=from_size,
            to_size=to_size,
            from_date=from_date,
            to_date=to_date,
            all_revisions=all_revisions,
            max_results=max_results,
            offset=offset,
        )
        return await handle_with_logging(server, "query", "p4dam_assets", params, "query_p4dam_assets", ctx)

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_asset(
        ctx: Context,
        depot_path: Annotated[Optional[str], Field(
            default=None,
            description=(
                "Full depot path of the asset (e.g. //depot/art/logo.png). "
                "Use when project_id and repository_id are not known. "
                "When project_id and repository_id are provided, prefer path instead."
            ),
            examples=["//depot/art/logo.png"],
        )] = None,
        path: Annotated[Optional[str], Field(
            default=None,
            description=(
                "Repository-relative path. Use when project_id and repository_id are known. "
                "For helix_classic: full path without leading slashes "
                "(e.g. depot/art/logo.png for //depot/art/logo.png). "
                "For helix_stream: path relative to stream_path "
                "(e.g. art/logo.png when stream_path is //depot/main and the file is //depot/main/art/logo.png)."
            ),
            examples=["depot/art/logo.png", "art/logo.png"],
        )] = None,
        stream_path: Annotated[Optional[str], Field(
            default=None,
            description=(
                "Stream path for helix_stream repositories (e.g. //depot/main). "
                "Required when the repository has multiple linked streams and the asset is not in the default one."
            ),
            examples=["//depot/main"],
        )] = None,
        identifier: Annotated[Optional[str], Field(
            default=None,
            description="Changeset identifier. Omit for the latest revision.",
            examples=["10"],
        )] = None,
        project_id: Annotated[Optional[str], Field(
            default=None,
            description="Project short name or UUID.",
            examples=["my-project"],
        )] = None,
        repository_id: Annotated[Optional[str], Field(
            default=None,
            description="Repository short name or UUID.",
            examples=["my-repo"],
        )] = None,
        include: Annotated[Optional[List[str]], Field(
            default=[
                "commit", "latest_commit", "custom_attributes", "weblinks",
                "asset_bundle", "asset_bundle_origin", "parent_asset_bundles",
                "helix_classic_branch_matches", "stream_view_matches", "sprite",
            ],
            description=(
                "Sections to include in the response. "
                "Default set: commit, latest_commit, custom_attributes, weblinks, asset_bundle, "
                "asset_bundle_origin, parent_asset_bundles, helix_classic_branch_matches, "
                "stream_view_matches, sprite. "
                "Require project/repository context: file_review, comments, all_comments. "
                "Extras: scene_refs, file_count."
            ),
            examples=[["commit", "weblinks", "parent_asset_bundles"]],
        )] = None,
    ) -> dict:
        """Fetch full metadata for a single P4 DAM asset. Pass depot_path when
        project/repository scope is unknown; pass path + project_id + repository_id
        when scope is known (more efficient). For discovery without a known path,
        use query_p4dam_assets instead."""
        params = p4dam_m.GetP4DamAssetParams(
            depot_path=depot_path,
            path=path,
            stream_path=stream_path,
            identifier=identifier,
            project_id=project_id,
            repository_id=repository_id,
            include=include,
        )
        return await handle_with_logging(server, "query", "p4dam_asset", params, "query_p4dam_asset", ctx)

    # ------------------------------------------------------------------
    # Navigation — projects, repositories, helix classic branches
    # ------------------------------------------------------------------

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_projects(
        ctx: Context,
        search_term: Annotated[Optional[str], Field(
            default=None,
            description="Filter projects by name, short name, or description.",
            examples=["characters"],
        )] = None,
        limit: Annotated[int, Field(
            default=20, ge=1, le=200,
            description="Maximum number of results.",
        )] = 20,
        offset: Annotated[int, Field(
            default=0, ge=0,
            description="Pagination offset.",
        )] = 0,
    ) -> dict:
        """List P4 DAM projects."""
        params = p4dam_m.ListP4DamProjectsParams(
            search_term=search_term,
            limit=limit,
            offset=offset,
        )
        return await handle_with_logging(server, "query", "p4dam_projects", params, "query_p4dam_projects", ctx)

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_repositories(
        project_id: Annotated[str, Field(
            description="Project short name or UUID.",
            examples=["my-project"],
        )],
        ctx: Context,
        search_term: Annotated[Optional[str], Field(
            default=None,
            description="Filter repositories by short name.",
            examples=["renders"],
        )] = None,
        limit: Annotated[int, Field(
            default=20, ge=1, le=200,
            description="Maximum number of results.",
        )] = 20,
        offset: Annotated[int, Field(
            default=0, ge=0,
            description="Pagination offset.",
        )] = 0,
    ) -> dict:
        """List repositories (collections) in a P4 DAM project. The response includes
        repository type (helix_stream or helix_classic) and linked_streams."""
        params = p4dam_m.ListP4DamRepositoriesParams(
            project_id=project_id,
            search_term=search_term,
            limit=limit,
            offset=offset,
        )
        return await handle_with_logging(server, "query", "p4dam_repositories", params, "query_p4dam_repositories", ctx)

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_helix_classic_branches(
        project_id: Annotated[str, Field(
            description="Project short name or UUID.",
            examples=["my-project"],
        )],
        repository_id: Annotated[str, Field(
            description="Repository short name or UUID. Must be a helix_classic repository.",
            examples=["my-classic-repo"],
        )],
        ctx: Context,
        limit: Annotated[int, Field(
            default=20, ge=1, le=200,
            description="Maximum number of results.",
        )] = 20,
        offset: Annotated[int, Field(
            default=0, ge=0,
            description="Pagination offset.",
        )] = 0,
    ) -> dict:
        """List Helix Classic branches in a repository. Only applies to helix_classic
        repositories."""
        params = p4dam_m.ListP4DamHelixClassicBranchesParams(
            project_id=project_id,
            repository_id=repository_id,
            limit=limit,
            offset=offset,
        )
        return await handle_with_logging(server, "query", "p4dam_helix_classic_branches", params, "query_p4dam_helix_classic_branches", ctx)

    @server.mcp.tool(tags=["read", "p4dam"])
    async def fetch_p4dam_media(
        url: Annotated[str, Field(
            description=(
                "thumbnail_url, preview_url, sprite_url, or file_url from a query_p4dam_assets "
                "or query_p4dam_asset result. thumbnail_url, preview_url, and sprite_url are only "
                "present for image files (nil for non-image assets). "
                "Prefer thumbnail_url to limit data transfer unless higher resolution is needed."
            ),
            examples=["https://dam.example.com/api/p4/files/thumbnail?depot_path=//stream/renders/hero.png&identifier=42"],
        )],
        ctx: Context,
    ):
        """Fetch P4 DAM media and return it as a viewable image. Use thumbnail_url,
        preview_url, or sprite_url from query_p4dam_assets / query_p4dam_asset results —
        these are only present for image files. For file_url of non-image assets, returns
        the MIME type and size instead of image content."""
        from mcp.types import ImageContent, TextContent
        params = p4dam_m.FetchP4DamMediaParams(url=url)
        result = await handle_with_logging(server, "query", "p4dam_media", params, "fetch_p4dam_media", ctx)
        if result.get("status") != "success":
            return [TextContent(type="text", text=str(result.get("message", "Unknown error")))]
        msg = result["message"]
        mime = msg["mime_type"]
        if mime.startswith("image/"):
            return [ImageContent(type="image", data=msg["data_b64"], mimeType=mime)]
        return [TextContent(type="text", text=f"Binary content: {mime}, {msg['size']} bytes (not an image)")]

    # ------------------------------------------------------------------
    # File reviews (read)
    # ------------------------------------------------------------------

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_file_reviews(
        project_id: Annotated[str, Field(
            description="Project short name or UUID.",
            examples=["my-project"],
        )],
        ctx: Context,
        depot_path: Annotated[Optional[str], Field(
            default=None,
            description="Filter by depot path of the file being reviewed.",
            examples=["//my-stream/renders/hero.png"],
        )] = None,
        include: Annotated[Optional[List[str]], Field(
            default=None,
            description="Sections to include in each result. Valid value: weblinks.",
            examples=[["weblinks"]],
        )] = None,
        limit: Annotated[int, Field(
            default=20, ge=1, le=200,
            description="Maximum number of results.",
        )] = 20,
        offset: Annotated[int, Field(
            default=0, ge=0,
            description="Pagination offset.",
        )] = 0,
    ) -> dict:
        """List P4 DAM file (asset) reviews for a project. Returns paginated results with
        metadata (total_count, more_results). For full detail on a single review including
        download_url, use query_p4dam_file_review instead."""
        params = p4dam_m.ListP4DamFileReviewsParams(
            project_id=project_id,
            depot_path=depot_path,
            include=include,
            limit=limit,
            offset=offset,
        )
        return await handle_with_logging(server, "query", "p4dam_file_reviews", params, "query_p4dam_file_reviews", ctx)

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_file_review(
        project_id: Annotated[str, Field(
            description="Project short name or UUID.",
            examples=["my-project"],
        )],
        review_id: Annotated[str, Field(
            description="File review UUID. Found in query_p4dam_file_reviews results.",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        )],
        ctx: Context,
    ) -> dict:
        """Fetch a single P4 DAM file review by UUID. Returns full detail including state,
        view_paths, asset_bundle, creator, and download_url (for bundle reviews).
        Use query_p4dam_file_reviews to discover review UUIDs."""
        params = p4dam_m.GetP4DamFileReviewParams(
            project_id=project_id,
            review_id=review_id,
        )
        return await handle_with_logging(server, "query", "p4dam_file_review", params, "query_p4dam_file_review", ctx)

    # ------------------------------------------------------------------
    # Workflows (read)
    # ------------------------------------------------------------------

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_workflows(
        ctx: Context,
        include: Annotated[Optional[List[str]], Field(
            default=None,
            description=(
                "Sections to embed in each workflow. "
                "Pass ['states'] to get all states in a single call — "
                "each state has name, short_name, kind (open/review/done), color, and position. "
                "Pass ['transition_rules'] to include allowed state transitions. "
                "Pass ['projects'] to see which projects use the workflow."
            ),
            examples=[["states"]],
        )] = None,
        limit: Annotated[int, Field(
            default=20, ge=1, le=200,
            description="Maximum number of results.",
        )] = 20,
        offset: Annotated[int, Field(
            default=0, ge=0,
            description="Pagination offset.",
        )] = 0,
    ) -> dict:
        """List P4 DAM workflows. Each workflow defines the set of states an asset review
        can be in (open, review, done kinds). Pass include=['states'] to get all states
        in one call. Use query_p4dam_workflow_states for the states of a specific workflow."""
        params = p4dam_m.ListP4DamWorkflowsParams(
            include=include,
            limit=limit,
            offset=offset,
        )
        return await handle_with_logging(server, "query", "p4dam_workflows", params, "query_p4dam_workflows", ctx)

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_workflow(
        workflow_id: Annotated[str, Field(
            description="Workflow short name or UUID. Found in query_p4dam_workflows results.",
            examples=["default_workflow"],
        )],
        ctx: Context,
        include: Annotated[Optional[List[str]], Field(
            default=None,
            description=(
                "Sections to embed. "
                "Valid values: states, transition_rules, projects."
            ),
            examples=[["states", "transition_rules"]],
        )] = None,
    ) -> dict:
        """Fetch a single P4 DAM workflow by short name or UUID. Pass include=['states']
        to see all available review states with their kind (open/review/done), color, and
        position. Pass include=['transition_rules'] to see which state transitions are
        allowed and for which users."""
        params = p4dam_m.GetP4DamWorkflowParams(
            workflow_id=workflow_id,
            include=include,
        )
        return await handle_with_logging(server, "query", "p4dam_workflow", params, "query_p4dam_workflow", ctx)

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_workflow_states(
        workflow_id: Annotated[str, Field(
            description="Workflow short name or UUID.",
            examples=["default_workflow"],
        )],
        ctx: Context,
        limit: Annotated[int, Field(
            default=50, ge=1, le=200,
            description="Maximum number of results.",
        )] = 50,
        offset: Annotated[int, Field(
            default=0, ge=0,
            description="Pagination offset.",
        )] = 0,
    ) -> dict:
        """List states for a P4 DAM workflow. Each state has: name, short_name, kind
        (open/review/done), color, and position. The short_name is the value to pass
        as state when creating or updating a file review.

        State kinds: 'open' — initial state; 'review' — under review; 'done' — terminal.
        Preconfigured states: Open, In Review, Reviewed, Released, Rejected."""
        params = p4dam_m.ListP4DamWorkflowStatesParams(
            workflow_id=workflow_id,
            limit=limit,
            offset=offset,
        )
        return await handle_with_logging(server, "query", "p4dam_workflow_states", params, "query_p4dam_workflow_states", ctx)

    # ------------------------------------------------------------------
    # Custom attribute templates (read)
    # ------------------------------------------------------------------

    @server.mcp.tool(tags=["read", "p4dam"])
    async def query_p4dam_custom_attribute_templates(
        ctx: Context,
        project_id: Annotated[str, Field(
            description="Project short name or UUID.",
            examples=["my-project"],
        )],
    ) -> dict:
        """List custom file attribute templates available in a P4 DAM project. Each
        template defines an attribute name, type (text, single-select, multi-select,
        checkbox), and for select types the list of allowed values. Use the returned
        UUID when setting attribute values with update_p4dam_asset_custom_attributes."""
        params = p4dam_m.QueryP4DamCustomAttributeTemplatesParams(project_id=project_id)
        return await handle_with_logging(server, "query", "p4dam_custom_attribute_templates", params, "query_p4dam_custom_attribute_templates", ctx)

    if server.readonly:
        return

    @server.mcp.tool(tags=["write", "p4dam"])
    async def create_p4dam_comment(
        type: Annotated[Literal["file_review", "file_review_file", "commit_file", "comment"], Field(
            description=(
                "Comment type: "
                "'file_review' — on a file review (asset bundles only); "
                "'file_review_file' — on a specific file inside a file review (asset bundle files only); "
                "'commit_file' — on a regular file, or on an asset bundle without a review; "
                "'comment' — reply to an existing comment."
            ),
        )],
        content: Annotated[str, Field(description="Comment text.")],
        ctx: Context,
        project: Annotated[Optional[str], Field(
            default=None,
            description="Project UUID or short name. Required for file_review, file_review_file, commit_file.",
        )] = None,
        repository: Annotated[Optional[str], Field(
            default=None,
            description="Repository UUID or short name. Required for file_review, file_review_file, commit_file.",
        )] = None,
        file_review: Annotated[Optional[str], Field(
            default=None,
            description="File review UUID. Required for file_review and file_review_file.",
        )] = None,
        commit: Annotated[Optional[str], Field(
            default=None,
            description="Changeset number (as a string). Required for commit_file.",
            examples=["14"],
        )] = None,
        path: Annotated[Optional[str], Field(
            default=None,
            description=(
                "Relative file path within the repository (e.g. 'renders/hero.png'). "
                "Required for file_review_file and commit_file."
            ),
        )] = None,
        stream_path: Annotated[Optional[str], Field(
            default=None,
            description="Stream path. Required for commit_file on helix_stream repos.",
        )] = None,
        helix_classic_branch: Annotated[Optional[str], Field(
            default=None,
            description="Helix Classic branch short name. Required for commit_file on helix_classic repos.",
        )] = None,
        comment: Annotated[Optional[str], Field(
            default=None,
            description="Parent comment UUID. Required for type 'comment' (reply).",
        )] = None,
    ) -> dict:
        """Add a comment to a file review (asset bundles only), a file within a file review,
        a committed file or asset bundle without a review, or reply to an existing comment."""
        params = p4dam_m.CreateP4DamCommentParams(
            type=type, content=content, project=project, repository=repository,
            file_review=file_review, commit=commit, path=path, stream_path=stream_path,
            helix_classic_branch=helix_classic_branch, comment=comment,
        )
        return await handle_with_logging(server, "modify", "create_p4dam_comment", params, "create_p4dam_comment", ctx)

    @server.mcp.tool(tags=["write", "p4dam"])
    async def regenerate_p4dam_preview(
        depot_path: Annotated[str, Field(
            description="Depot path of the asset (e.g. //depot/art/logo.png).",
            examples=["//my-stream/renders/hero.png"],
        )],
        commit_id: Annotated[str, Field(
            description="Changeset number of the revision to regenerate.",
            examples=["42"],
        )],
        ctx: Context,
    ) -> dict:
        """Trigger P4Search to regenerate the thumbnail and preview image for a
        specific asset revision. Deletes the existing preview attributes and asks
        P4Search to re-index the file. Returns 'accepted' immediately — the actual
        regeneration happens asynchronously. Requires P4.P4Search.URL and
        P4.P4Search.AUTH_TOKEN to be set on the P4 server."""
        params = p4dam_m.RegenerateP4DamPreviewParams(depot_path=depot_path, commit_id=commit_id)
        return await handle_with_logging(server, "modify", "regenerate_p4dam_preview", params, "regenerate_p4dam_preview", ctx)

    # ------------------------------------------------------------------
    # Asset bundles
    # ------------------------------------------------------------------

    @server.mcp.tool(tags=["write", "p4dam"])
    async def create_p4dam_asset_bundle(
        depot_path: Annotated[str, Field(
            description="Depot path for the bundle file. Must end with '.p4bundle'.",
            examples=["//my-stream/bundles/chars-q3.p4bundle"],
        )],
        project: Annotated[str, Field(
            description="Project short name or UUID.",
            examples=["my-project"],
        )],
        repository: Annotated[str, Field(
            description="Repository short name or UUID.",
            examples=["my-repo"],
        )],
        view_paths: Annotated[List[str], Field(
            description=(
                "Depot paths defining the bundle scope. Must start with '//' (or '-//' to exclude). "
                "Use '...' suffix for recursive inclusion (e.g. '//stream/renders/...'). "
                "For helix stream repos, every path must start with stream_path. Max 250 entries. "
                "Tip: derive from the asset's depot_path by taking its parent directory + '/...'."
            ),
            examples=[["//my-stream/renders/...", "//my-stream/textures/..."]],
        )],
        ctx: Context,
        stream_path: Annotated[Optional[str], Field(
            default=None,
            description="Stream path (e.g. //depot/main). Required for helix_stream repositories. Found in linked_streams from query_p4dam_repositories.",
            examples=["//my-stream/mainline"],
        )] = None,
        helix_classic_branch: Annotated[Optional[str], Field(
            default=None,
            description="Helix Classic branch short name or UUID. Required for helix_classic repositories.",
            examples=["main"],
        )] = None,
        description: Annotated[Optional[str], Field(
            default=None,
            description="Human-readable description of the bundle.",
            examples=["Q3 character renders for review"],
        )] = None,
        hero_file_path: Annotated[Optional[str], Field(
            default=None,
            description="Depot path of the hero/cover image for this bundle.",
            examples=["//my-stream/renders/hero.png"],
        )] = None,
    ) -> dict:
        """Create a P4 DAM asset bundle — a named collection of depot files scoped
        for review. Requires a project, repository, depot_path (must end .p4bundle),
        and view_paths. Supply stream_path for helix_stream repos, or
        helix_classic_branch for helix_classic repos."""
        params = p4dam_m.CreateP4DamAssetBundleParams(
            depot_path=depot_path,
            project=project,
            repository=repository,
            view_paths=view_paths,
            stream_path=stream_path,
            helix_classic_branch=helix_classic_branch,
            description=description,
            hero_file_path=hero_file_path,
        )
        return await handle_with_logging(server, "modify", "create_p4dam_asset_bundle", params, "create_p4dam_asset_bundle", ctx)

    @server.mcp.tool(tags=["write", "p4dam"])
    async def update_p4dam_asset_bundle(
        bundle_id: Annotated[str, Field(
            description="UUID of the asset bundle to update. Found in query_p4dam_asset response under asset_bundle.uuid.",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        )],
        ctx: Context,
        description: Annotated[Optional[str], Field(
            default=None,
            description="Updated description.",
            examples=["Q3 character renders — final review"],
        )] = None,
        view_paths: Annotated[Optional[List[str]], Field(
            default=None,
            description="Replacement view paths list. Replaces the full existing list. Same rules as create.",
            examples=[["//my-stream/renders/...", "//my-stream/textures/hero/..."]],
        )] = None,
        hero_file_path: Annotated[Optional[str], Field(
            default=None,
            description="Updated hero/cover image depot path.",
            examples=["//my-stream/renders/hero-final.png"],
        )] = None,
    ) -> dict:
        """Update a P4 DAM asset bundle. Only description, view_paths, and
        hero_file_path can be changed after creation. depot_path is immutable.
        Provide only the fields you want to change."""
        params = p4dam_m.UpdateP4DamAssetBundleParams(
            bundle_id=bundle_id,
            description=description,
            view_paths=view_paths,
            hero_file_path=hero_file_path,
        )
        return await handle_with_logging(server, "modify", "update_p4dam_asset_bundle", params, "update_p4dam_asset_bundle", ctx)

    @server.mcp.tool(tags=["write", "p4dam"])
    async def delete_p4dam_asset_bundle(
        bundle_id: Annotated[str, Field(
            description="UUID of the asset bundle to delete.",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        )],
        ctx: Context,
    ) -> dict:
        """Delete a P4 DAM asset bundle. Prompts for confirmation before deleting."""
        params = p4dam_m.DeleteP4DamAssetBundleParams(bundle_id=bundle_id)
        return await handle_modify_with_delete_gate(
            server, "delete_p4dam_asset_bundle", params, "delete_p4dam_asset_bundle", ctx,
            f"Delete asset bundle: {bundle_id}",
        )

    @server.mcp.tool(tags=["write", "p4dam"])
    async def sync_p4dam_asset_bundle(
        view_paths: Annotated[List[str], Field(
            description=(
                "Depot paths to sync — the view_paths from the asset bundle. "
                "Obtain from query_p4dam_asset with include=asset_bundle."
            ),
            examples=[["//my-stream/renders/...", "//my-stream/textures/..."]],
        )],
        ctx: Context,
    ) -> dict:
        """Sync an asset bundle's depot files to the local P4CLIENT workspace via p4 sync.
        Requires P4CLIENT to be set — returns an error if it is not.
        Sync is scoped to view_paths only; files outside those paths are not touched
        even if the client's View is broader."""
        params = p4dam_m.SyncP4DamAssetBundleParams(view_paths=view_paths)
        return await handle_with_logging(server, "modify", "sync_p4dam_asset_bundle", params, "sync_p4dam_asset_bundle", ctx)

    # ------------------------------------------------------------------
    # File review CRUD
    # ------------------------------------------------------------------

    @server.mcp.tool(tags=["write", "p4dam"])
    async def create_p4dam_file_review(
        project_id: Annotated[str, Field(
            description="Project short name or UUID.",
            examples=["my-project"],
        )],
        name: Annotated[str, Field(
            description="Review name. Must be unique within the project. Length 2–100 characters.",
            examples=["Q3 hero renders — art director pass"],
        )],
        depot_path: Annotated[str, Field(
            description=(
                "Depot path of the file or bundle being reviewed. "
                "Use a .p4bundle path for asset bundle reviews."
            ),
            examples=["//my-stream/renders/hero.png"],
        )],
        view_paths: Annotated[List[str], Field(
            description=(
                "Depot paths scoping the review. Must start with '//' (or '-//' to exclude). "
                "Use '...' for recursive inclusion. For bundle reviews, should match the bundle's view_paths."
            ),
            examples=[["//my-stream/renders/..."]],
        )],
        state: Annotated[str, Field(
            description=(
                "Workflow state name. The backend always places new reviews in the project's "
                "first open state — this field is required by the API but its value is not used."
            ),
            examples=["open"],
        )],
        base_commit_id: Annotated[str, Field(
            description=(
                "Base changeset identifier. Set to the changelist number the user is currently "
                "viewing, or the latest changelist number of the file if not viewing a specific one."
            ),
            examples=["100"],
        )],
        ctx: Context,
        repository: Annotated[Optional[str], Field(
            default=None,
            description="Repository short name or UUID.",
            examples=["repo-uuid-1"],
        )] = None,
        helix_classic_branch: Annotated[Optional[str], Field(
            default=None,
            description="Helix Classic branch short name or UUID. Required for helix_classic repositories.",
            examples=["branch-uuid-1"],
        )] = None,
        asset_bundle: Annotated[Optional[str], Field(
            default=None,
            description="Asset bundle UUID. Required when depot_path ends in .p4bundle. Auto-detected when omitted.",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        )] = None,
        hero_file_path: Annotated[Optional[str], Field(
            default=None,
            description="Depot path of the cover image for this review.",
            examples=["//my-stream/renders/hero.png"],
        )] = None,
        description: Annotated[Optional[str], Field(
            default=None,
            description="Review description. Max 5000 characters.",
            examples=["Art director pass on Q3 hero renders"],
        )] = None,
        position: Annotated[Optional[int], Field(
            default=None,
            description="Sequential position within the workflow state.",
            examples=[1],
        )] = None,
        head_commit_id: Annotated[Optional[str], Field(
            default=None,
            description=(
                "Head changeset identifier. Required for regular file reviews; omit for bundle reviews. "
                "Set to the changelist number the user is currently viewing, or the latest changelist "
                "number of the file if not viewing a specific one."
            ),
            examples=["120"],
        )] = None,
    ) -> dict:
        """Create a P4 DAM file (asset) review. Supports both single-file reviews and
        asset bundle reviews (.p4bundle). For bundle reviews supply asset_bundle UUID
        (auto-detected from depot_path when omitted). For helix_classic repos supply
        helix_classic_branch. Always set base_commit_id to the changelist the user is
        viewing, or the latest changelist number of the file. Set head_commit_id for
        regular file reviews; omit for bundle reviews."""
        params = p4dam_m.CreateP4DamFileReviewParams(
            project_id=project_id,
            name=name,
            depot_path=depot_path,
            view_paths=view_paths,
            state=state,
            repository=repository,
            helix_classic_branch=helix_classic_branch,
            asset_bundle=asset_bundle,
            hero_file_path=hero_file_path,
            description=description,
            position=position,
            base_commit_id=base_commit_id,
            head_commit_id=head_commit_id,
        )
        return await handle_with_logging(server, "modify", "create_p4dam_file_review", params, "create_p4dam_file_review", ctx)

    @server.mcp.tool(tags=["write", "p4dam"])
    async def update_p4dam_file_review(
        project_id: Annotated[str, Field(
            description="Project short name or UUID.",
            examples=["my-project"],
        )],
        review_id: Annotated[str, Field(
            description="File review UUID.",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        )],
        ctx: Context,
        state: Annotated[Optional[str], Field(
            default=None,
            description="New workflow state name. The transition must be permitted for the authenticated user.",
            examples=["review"],
        )] = None,
        name: Annotated[Optional[str], Field(
            default=None,
            description="Updated review name. Length 2–100 characters.",
            examples=["Q3 hero renders — final"],
        )] = None,
        view_paths: Annotated[Optional[List[str]], Field(
            default=None,
            description="Replacement view paths list. Replaces the full existing list.",
            examples=[["//my-stream/renders/...", "//my-stream/textures/hero/..."]],
        )] = None,
        hero_file_path: Annotated[Optional[str], Field(
            default=None,
            description="Updated cover image depot path.",
            examples=["//my-stream/renders/hero-final.png"],
        )] = None,
        description: Annotated[Optional[str], Field(
            default=None,
            description="Updated description. Max 5000 characters.",
            examples=["Final art director pass — approved"],
        )] = None,
        position: Annotated[Optional[int], Field(
            default=None,
            description="Updated sequential position within the workflow state.",
            examples=[2],
        )] = None,
    ) -> dict:
        """Update a P4 DAM file review. Provide only the fields you want to change.
        State transitions must be permitted by the project's workflow for the current user."""
        params = p4dam_m.UpdateP4DamFileReviewParams(
            project_id=project_id,
            review_id=review_id,
            state=state,
            name=name,
            view_paths=view_paths,
            hero_file_path=hero_file_path,
            description=description,
            position=position,
        )
        return await handle_with_logging(server, "modify", "update_p4dam_file_review", params, "update_p4dam_file_review", ctx)

    @server.mcp.tool(tags=["write", "p4dam"])
    async def delete_p4dam_file_review(
        project_id: Annotated[str, Field(
            description="Project short name or UUID.",
            examples=["my-project"],
        )],
        review_id: Annotated[str, Field(
            description="File review UUID to delete.",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        )],
        ctx: Context,
    ) -> dict:
        """Delete a P4 DAM file review. Prompts for confirmation before deleting."""
        params = p4dam_m.DeleteP4DamFileReviewParams(
            project_id=project_id,
            review_id=review_id,
        )
        return await handle_modify_with_delete_gate(
            server, "delete_p4dam_file_review", params, "delete_p4dam_file_review", ctx,
            f"Delete file review: {review_id}",
        )

    # ------------------------------------------------------------------
    # Asset tag management
    # ------------------------------------------------------------------

    @server.mcp.tool(tags=["write", "p4dam"])
    async def update_p4dam_asset_tags(
        paths: Annotated[List[P4DamTagPath], Field(
            description=(
                "Assets to tag. Each entry needs a depot path; identifier (revision) is optional. "
                "Use '//depot/folder/...' to target all files in a folder recursively. "
                "Tip: use the depot_path from query_p4dam_asset or query_p4dam_assets results."
            ),
            examples=[[{"path": "//my-stream/renders/hero.png"}]],
        )],
        ctx: Context,
        create: Annotated[Optional[List[str]], Field(
            default=None,
            description="User tags to add. Case-insensitive — stored lowercase.",
            examples=[["hero", "q3-final"]],
        )] = None,
        delete: Annotated[Optional[List[str]], Field(
            default=None,
            description="User tags to remove.",
            examples=[["wip"]],
        )] = None,
        delete_auto: Annotated[Optional[List[str]], Field(
            default=None,
            description="Auto-generated tags to remove (auto_tags from asset metadata).",
            examples=[["outdated"]],
        )] = None,
        propagatable: Annotated[bool, Field(
            default=True,
            description=(
                "When true (default), changes apply to the latest revision and all future revisions. "
                "When false, changes apply only to the specified revision (identifier) "
                "or the latest revision. Cannot be true when any path includes an identifier."
            ),
        )] = True,
        identifier: Annotated[Optional[str], Field(
            default=None,
            description="Helix Classic branch short name. Required for assets in Helix Classic repositories.",
            examples=["main"],
        )] = None,
    ) -> dict:
        """Add or remove user tags and auto-tags on one or more P4 DAM assets in a single
        call. Supports individual files, specific revisions, and recursive folder paths
        (//depot/folder/...). All three operations (create, delete, delete_auto) can be
        combined in one request.

        Returns an array with the updated tags and auto_tags for each affected asset.

        Examples:
        - Tag a single file:         paths=[{path: "//s/file.png"}], create=["hero"]
        - Untag a file:              paths=[{path: "//s/file.png"}], delete=["wip"]
        - Remove auto-tag:           paths=[{path: "//s/file.png"}], delete_auto=["outdated"]
        - Tag a whole folder:        paths=[{path: "//s/renders/..."}], create=["q3"]
        - Tag a specific revision:   paths=[{path: "//s/file.png", identifier: "12345"}], create=["pinned"]
        - Propagate to future revs:  paths=[{path: "//s/file.png"}], create=["featured"], propagatable=true"""
        params = p4dam_m.UpdateP4DamAssetTagsParams(
            paths=paths,
            create=create,
            delete=delete,
            delete_auto=delete_auto,
            propagatable=propagatable,
            identifier=identifier,
        )
        return await handle_with_logging(server, "modify", "update_p4dam_asset_tags", params, "update_p4dam_asset_tags", ctx)

    @server.mcp.tool(tags=["write", "p4dam"])
    async def update_p4dam_asset_custom_attributes(
        ctx: Context,
        paths: Annotated[List[p4dam_m.P4DamTagPath], Field(
            description=(
                "Assets to update. Each entry requires a depot path; identifier is optional. "
                "Use '//depot/folder/...' to target all files in a folder recursively."
            ),
            examples=[[{"path": "//my-stream/renders/hero.png"}]],
        )],
        create: Annotated[Optional[List[p4dam_m.P4DamCustomAttributeCreate]], Field(
            default=None,
            description="Attribute values to set. Each entry must include the template UUID and new value.",
            examples=[[{"uuid": "5ee7de6c-4cc5-4f8d-9939-82b115a1933d", "value": "audio"}]],
        )] = None,
        delete: Annotated[Optional[List[str]], Field(
            default=None,
            description="Template UUIDs of attributes to remove.",
            examples=[["eb42bb83-f90e-4213-9240-2cf817c11f3e"]],
        )] = None,
        propagatable: Annotated[bool, Field(
            default=True,
            description=(
                "When true (default), changes apply to the most recent revision and all future revisions. "
                "When false, changes apply only to the specific revision or the most recent revision."
            ),
        )] = True,
    ) -> dict:
        """Set or remove custom attribute values on one or more P4 DAM assets. Use
        query_p4dam_custom_attribute_templates first to discover available templates
        and their UUIDs. Supports individual files, specific revisions (identifier in
        path), and recursive folders (//depot/folder/...)."""
        params = p4dam_m.UpdateP4DamAssetCustomAttributesParams(
            paths=paths,
            create=create,
            delete=delete,
            propagatable=propagatable,
        )
        return await handle_with_logging(server, "modify", "update_p4dam_asset_custom_attributes", params, "update_p4dam_asset_custom_attributes", ctx)
