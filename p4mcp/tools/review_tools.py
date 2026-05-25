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
        # Flat reviewer groups fields
        reviewer_group_names: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of reviewer group names",
            examples=[["Developers", "QA"]],
        )] = None,
        reviewer_groups_required: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of required reviewer groups",
            examples=[["Architects"]],
        )] = None,
        # Flat comment context fields
        comment_file_path: Annotated[Optional[str], Field(
            default=None,
            description="File path for inline comment",
            examples=["//depot/file.txt"],
        )] = None,
        comment_left_line: Annotated[Optional[int], Field(
            default=None,
            ge=1,
            description="Left diff line number for inline comment",
            examples=[40],
        )] = None,
        comment_right_line: Annotated[Optional[int], Field(
            default=None,
            ge=1,
            description="Right diff line number for inline comment",
            examples=[42],
        )] = None,
        comment_version: Annotated[Optional[int], Field(
            default=None,
            ge=1,
            description="Review version for comment attachment",
            examples=[1],
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
        # Flat participant user fields
        participant_user_names: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of participant usernames",
            examples=[["alice", "bob"]],
        )] = None,
        participant_users_required: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of required participant usernames",
            examples=[["carol"]],
        )] = None,
        # Flat participant group fields
        participant_group_names: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of participant group names",
            examples=[["dev-team"]],
        )] = None,
        participant_groups_required: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of required participant groups",
            examples=[["security-team"]],
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
        # Reconstruct reviewer_groups from flat fields
        reviewer_groups = None
        if reviewer_group_names or reviewer_groups_required:
            groups = []
            if reviewer_group_names:
                groups.extend([{"name": name, "required": "false"} for name in reviewer_group_names])
            if reviewer_groups_required:
                groups.extend([{"name": name, "required": "true"} for name in reviewer_groups_required])
            reviewer_groups = groups if groups else None

        # Reconstruct comment context from flat fields
        comment_context = None
        if any([comment_file_path, comment_left_line, comment_right_line, comment_version]):
            # Build context dict dynamically - only include non-None fields
            context_dict = {}
            if comment_file_path is not None:
                context_dict["file"] = comment_file_path
            if comment_left_line is not None:
                context_dict["leftLine"] = comment_left_line
            if comment_right_line is not None:
                context_dict["rightLine"] = comment_right_line
            if comment_version is not None:
                context_dict["version"] = comment_version
            comment_context = review_m.CommentContext(**context_dict) if context_dict else None

        # Reconstruct users dict from flat fields
        users = None
        if participant_user_names or participant_users_required:
            users = {}
            if participant_user_names:
                for username in participant_user_names:
                    users[username] = {"required": "no"}
            if participant_users_required:
                for username in participant_users_required:
                    users[username] = {"required": "yes"}

        # Reconstruct groups dict from flat fields
        groups = None
        if participant_group_names or participant_groups_required:
            groups = {}
            if participant_group_names:
                for groupname in participant_group_names:
                    groups[groupname] = {"required": "none"}
            if participant_groups_required:
                for groupname in participant_groups_required:
                    groups[groupname] = {"required": "all"}

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
            # Flat fields for schema compliance
            reviewer_group_names=reviewer_group_names,
            reviewer_groups_required=reviewer_groups_required,
            comment_file_path=comment_file_path,
            comment_left_line=comment_left_line,
            comment_right_line=comment_right_line,
            comment_version=comment_version,
            participant_user_names=participant_user_names,
            participant_users_required=participant_users_required,
            participant_group_names=participant_group_names,
            participant_groups_required=participant_groups_required,
        )
        return await handle_modify_with_delete_gate(
            server, "reviews", params, "modify_reviews", ctx,
            f"Requires approval to obliterate review: {review_id}",
        )
