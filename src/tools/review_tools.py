"""Review query & modify tools."""

from __future__ import annotations

from typing import Annotated, Optional, List, Literal, TYPE_CHECKING

from pydantic import Field
from fastmcp import Context

from ..models import review_models as review_m
from .common import handle_with_logging, handle_modify_with_delete_gate

if TYPE_CHECKING:
    from ..server import P4MCPServer


def register(server: "P4MCPServer") -> None:
    if "reviews" not in server.toolsets:
        return

    # ── read ────────────────────────────────────────────────────────────
    @server.mcp.tool(tags=["read", "reviews"])
    async def query_reviews(
        action: Annotated[Literal[
            "list", "dashboard", "get", "transitions",
            "files_readby", "files", "comments", "activity",
        ], Field(
            description="Review query action: list all reviews, dashboard for current user, get specific review, transitions, files_readby, files, comments, activity"
        )],
        ctx: Context,
        review_id: Annotated[Optional[int], Field(
            default=None,
            description="Review ID - required for get, transitions, files_readby, files, comments, activity actions",
            examples=[12345, 67890],
        )] = None,
        fields: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of fields to return for list/get actions",
            examples=[["id", "description", "author", "state"], ["id", "author", "state", "participants", "commits"]],
        )] = None,
        comments_fields: Annotated[Optional[str], Field(
            default="id,body,user,time",
            description="Comma-separated list of fields to return for comments action",
            examples=["id,body,user,time", "id,user,time"],
        )] = "id,body,user,time",
        up_voters: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of up voters for transitions action",
            examples=[["alice", "bob"]],
        )] = None,
        from_version: Annotated[Optional[int], Field(
            default=None,
            description="Starting version for files action",
            examples=[1, 2],
        )] = None,
        to_version: Annotated[Optional[int], Field(
            default=None,
            description="Ending version for files action",
            examples=[2, 3],
        )] = None,
        max_results: Annotated[int, Field(
            default=10,
            description="Maximum number of results to return",
        )] = 10,
        after: Annotated[Optional[str], Field(
            default=None,
            description="Review ID to seek to for pagination (list action). Reviews up to and including this ID are excluded.",
            examples=["12344"],
        )] = None,
        after_updated: Annotated[Optional[str], Field(
            default=None,
            description="Return reviews updated on the day before this date/time in seconds since epoch (list action). Mutually exclusive with 'after'.",
            examples=["1606233362"],
        )] = None,
        result_order: Annotated[Optional[str], Field(
            default=None,
            description="Set to 'updated' to return most recently updated reviews first (list action)",
            examples=["updated"],
        )] = None,
        projects: Annotated[Optional[List[str]], Field(
            default=None,
            description="Filter by project name(s) (list action)",
            examples=[["myproject"]],
        )] = None,
        state: Annotated[Optional[List[str]], Field(
            default=None,
            description="Filter by review state(s) (list action). Valid: needsRevision, needsReview, approved, approved:isPending, approved:commit, approved:notPending, rejected, archived",
            examples=[["needsReview"]],
        )] = None,
        keywords: Annotated[Optional[str], Field(
            default=None,
            description="Search keyword(s) to filter reviews (list action). Use with keywords_fields.",
            examples=["bugfix", "12345"],
        )] = None,
        keywords_fields: Annotated[Optional[List[str]], Field(
            default=None,
            description="Fields to search keywords in (list action). Valid: changes, author, participants, hasReviewer, description, updated, projects, state, testStatus, pending, groups, id",
            examples=[["description"], ["author"], ["changes"]],
        )] = None,
        include_transitions: Annotated[Optional[bool], Field(
            default=None,
            description="Include allowed state transitions in get action response",
        )] = None,
    ) -> dict:
        """Get review details and list reviews (READ permission).
        Open review - state is 'approved but pending=true' or 'needsReview' or 'needsRevision'.
        Closed review - state is 'approved but pending=false' or 'rejected' or 'archived'.
        """
        params = review_m.QueryReviewsParams(
            action=action, review_id=review_id,
            fields=fields, comments_fields=comments_fields,
            up_voters=up_voters, from_version=from_version,
            to_version=to_version, max_results=max_results,
            after=after, after_updated=after_updated,
            result_order=result_order, projects=projects,
            state=state, keywords=keywords,
            keywords_fields=keywords_fields,
            include_transitions=include_transitions,
        )
        return await handle_with_logging(server, "query", "reviews", params, "query_reviews", ctx)

    # ── write ───────────────────────────────────────────────────────────
    if server.readonly:
        return

    @server.mcp.tool(tags=["write", "reviews"])
    async def modify_reviews(
        action: Annotated[Literal[
            "create", "refresh_projects", "vote", "transition",
            "append_participants", "add_comment", "reply_comment",
            "append_change", "replace_with_change", "join",
            "archive_inactive", "mark_comment_read", "mark_comment_unread",
            "mark_all_comments_read", "mark_all_comments_unread",
            "update_author", "update_description",
            "replace_participants", "delete_participants",
            "leave", "obliterate",
        ], Field(
            description="Review modification action. " \
            "To delete/obliterate review, use 'obliterate' action which requires approval"
        )],
        ctx: Context,
        review_id: Annotated[Optional[int], Field(
            default=None,
            description="Review ID (required for most actions except create, archive_inactive)",
            examples=[12345],
        )] = None,
        change_id: Annotated[Optional[int], Field(
            default=None,
            description="Changelist ID (required for create, append_change, replace_with_change)",
            examples=[67890],
        )] = None,
        description: Annotated[Optional[str], Field(
            default=None,
            description="Review description (optional on create)",
            examples=["Implement feature X"],
        )] = None,
        reviewers: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of reviewers",
            examples=[["alice", "bob"]],
        )] = None,
        required_reviewers: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of required reviewers",
            examples=[["carol"]],
        )] = None,
        reviewer_groups: Annotated[Optional[List[dict]], Field(
            default=None,
            description="Reviewer groups",
            examples=[[{"name": "Developers", "required": "true"}]],
        )] = None,
        context: Annotated[Optional[dict], Field(
            default=None,
            description="Comment context: file, leftLine, rightLine, content, version, attribute, comment",
            examples=[{"file": "//depot/path/file.txt", "rightLine": 42, "leftLine": 40}],
        )] = None,
        vote_value: Annotated[Optional[Literal["up", "down", "clear"]], Field(
            default=None,
            description="Vote value",
        )] = None,
        version: Annotated[Optional[int], Field(
            default=None,
            description="Review version (optional for vote)",
            examples=[2],
        )] = None,
        transition: Annotated[Optional[Literal[
            "needsRevision", "needsReview", "approved",
            "committed", "approved:commit", "rejected", "archived",
        ]], Field(
            default=None,
            description="Transition target state",
        )] = None,
        jobs: Annotated[Optional[List[str]], Field(
            default=None,
            description="Associated job IDs for transition",
            examples=[["job000123", "job000456"]],
        )] = None,
        fix_status: Annotated[Optional[Literal["open", "closed"]], Field(
            default=None,
            description="Job fix status when transitioning",
        )] = None,
        cleanup: Annotated[Optional[bool], Field(
            default=None,
            description="Perform cleanup for approved:commit/committed transitions",
        )] = None,
        users: Annotated[Optional[dict], Field(
            default=None,
            description="Usernames for append/replace/delete participants",
            examples=[{"alice": {"required": "yes"}, "bob": {"required": "no"}}],
        )] = None,
        groups: Annotated[Optional[dict], Field(
            default=None,
            description="Group names for append/replace/delete participants",
            examples=[{"dev-team": {"required": "all"}}],
        )] = None,
        body: Annotated[Optional[str], Field(
            default=None,
            description="Comment body (required for add_comment, reply_comment)",
            examples=["Looks good."],
        )] = None,
        task_state: Annotated[Optional[Literal["open", "comment"]], Field(
            default=None,
            description="Task state",
        )] = None,
        notify: Annotated[Optional[Literal["immediate", "delayed"]], Field(
            default=None,
            description="Notification mode",
        )] = None,
        comment_id: Annotated[Optional[int], Field(
            default=None,
            description="Parent comment ID (reply_comment, mark_comment_read/unread)",
            examples=[987],
        )] = None,
        not_updated_since: Annotated[Optional[str], Field(
            default=None,
            description="ISO date (YYYY-MM-DD) threshold for archive_inactive",
            examples=["2024-01-15"],
        )] = None,
        max_reviews: Annotated[int, Field(
            default=0,
            description="Maximum number of inactive reviews to archive (0 = no limit)",
        )] = 0,
        new_author: Annotated[Optional[str], Field(
            default=None,
            description="New author username (update_author)",
            examples=["dave"],
        )] = None,
        new_description: Annotated[Optional[str], Field(
            default=None,
            description="New review description (update_description)",
            examples=["Refined implementation details."],
        )] = None,
    ) -> dict:
        """Create/update/delete reviews (WRITE permission)"""
        comment_context = review_m.CommentContext(**context) if context else None
        params = review_m.ModifyReviewsParams(
            action=action, review_id=review_id, change_id=change_id,
            description=description, reviewers=reviewers,
            required_reviewers=required_reviewers, reviewer_groups=reviewer_groups,
            context=comment_context, vote_value=vote_value, version=version,
            transition=transition, jobs=jobs, fix_status=fix_status,
            cleanup=cleanup, users=users, groups=groups,
            body=body, task_state=task_state, notify=notify,
            comment_id=comment_id, not_updated_since=not_updated_since,
            max_reviews=max_reviews, new_author=new_author,
            new_description=new_description,
        )
        return await handle_modify_with_delete_gate(
            server, "reviews", params, "modify_reviews", ctx,
            f"Requires approval to obliterate review: {review_id}",
        )
