from typing import Any, Dict, List, Optional
from .models import BaseParams, PaginatedParams
from pydantic import Field, model_validator, field_validator
from enum import Enum
import re

class ReviewTransition(str, Enum):
    NEEDS_REVISION = "needsRevision"
    NEEDS_REVIEW = "needsReview"
    APPROVED = "approved"
    COMMITTED = "committed"
    APPROVED_COMMIT = "approved:commit"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class VoteValue(str, Enum):
    UP = "up"
    DOWN = "down"
    CLEAR = "clear"

class ReviewAction(str, Enum):
    LIST = "list"
    DASHBOARD = "dashboard"
    GET = "get"
    TRANSITIONS = "transitions"
    FILES_READBY = "files_readby"
    FILES = "files"
    ACTIVITY = "activity"
    COMMENTS = "comments"

class QueryReviewsParams(PaginatedParams):
    """Review query parameters."""

    action: ReviewAction = Field(
        description=(
            "Review query action: "
            "'list' to search/filter reviews (supports author, change, project, state, keywords filters), "
            "'dashboard' for reviews needing the authenticated user's attention (reviews to act on, not all authored reviews), "
            "'get' for a specific review by ID, "
            "'transitions', 'files_readby', 'files', 'comments', 'activity' for review details"
        ),
        examples=["list", "dashboard", "get", "transitions", "files_readby", "files", "comments", "activity"],
    )
    review_id: Optional[int] = Field(
        default=None,
        description="Review ID — required for get, transitions, files_readby, files, comments, and activity actions",
        examples=[12345, 67890],
    )
    author: Optional[List[str]] = Field(
        default=None,
        description="Filter by review author(s) — for list action only",
        examples=[["alice"], ["alice", "bob"]],
    )
    change: Optional[List[int]] = Field(
        default=None,
        description="Filter by associated changelist number(s) — for list action only. "
                    "Use this to find the review for a specific changelist.",
        examples=[[12345], [12345, 67890]],
    )
    review_fields: Optional[str] = Field(
        default=None,
        description="Comma-separated list of fields to return for list/get actions",
        examples=["id,description,author,state", "id,author,state,participants,commits"],
    )
    comments_fields: Optional[str] = Field(
        default="id,body,user,time",
        description="Comma-separated list of fields to return for comments action",
        examples=["id,body,user,time", "id,user,time"],
    )
    up_voters: Optional[List[str]] = Field(
        default=None,
        description="List of up voters for transitions action",
        examples=[["alice", "bob"]],
    )
    from_version: Optional[int] = Field(
        default=None,
        description="Starting version for files action",
        examples=[1, 2],
    )
    to_version: Optional[int] = Field(
        default=None,
        description="Ending version for files action",
        examples=[2, 3],
    )
    max_results: Optional[int] = Field(
        default=10,
        description="Maximum number of results to return",
        examples=[10, 20, 50],
    )

    @model_validator(mode="after")
    def validate_review_id_required(self):
        """Ensure review_id is provided for specific actions requiring it."""
        required_actions = {
            ReviewAction.GET,
            ReviewAction.TRANSITIONS,
            ReviewAction.FILES_READBY,
            ReviewAction.FILES,
            ReviewAction.COMMENTS,
        }

        if self.action in required_actions and not self.review_id:
            raise ValueError(f"review_id is required for action: {self.action.value}")

        return self

class ReviewModifyAction(str, Enum):
    CREATE = "create"
    REFRESH_PROJECTS = "refresh_projects"
    VOTE = "vote"
    TRANSITION = "transition"
    APPEND_PARTICIPANTS = "append_participants"
    ADD_COMMENT = "add_comment"
    REPLY_COMMENT = "reply_comment"
    APPEND_CHANGE = "append_change"
    REPLACE_WITH_CHANGE = "replace_with_change"
    JOIN = "join"
    ARCHIVE_INACTIVE = "archive_inactive"
    MARK_COMMENT_READ = "mark_comment_read"
    MARK_COMMENT_UNREAD = "mark_comment_unread"
    MARK_ALL_COMMENTS_READ = "mark_all_comments_read"
    MARK_ALL_COMMENTS_UNREAD = "mark_all_comments_unread"
    UPDATE_AUTHOR = "update_author"
    UPDATE_DESCRIPTION = "update_description"
    REPLACE_PARTICIPANTS = "replace_participants"
    DELETE_PARTICIPANTS = "delete_participants"
    LEAVE = "leave"
    OBLITERATE = "obliterate"

class FixStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"

class TaskState(str, Enum):
    OPEN = "open"
    COMMENT = "comment"

class NotifyMode(str, Enum):
    IMMEDIATE = "immediate"
    DELAYED = "delayed"

class CommentContext(BaseParams):
    """Context payload for creating or replying to review comments."""

    file: Optional[str] = Field(
        default=None,
        description="file mandatory unless attribute or comment are set: File to comment on. " \
        "Valid only for changes and reviews topics",
        examples=["//depot/path/to/file.txt"]
    )
    leftLine: Optional[int] = Field(
        default="null",
        ge=1,
        description="leftline optional, but if specified, you must also specify the rightline and " \
        "content parameters. Integer: Left-side diff line number to attach the inline comment to. " \
        "Valid only for changes and reviews topics."
    )
    rightLine: Optional[int] = Field(
        default="null",
        ge=1,
        description="rightline optional, but if specified, you must also specify the leftline and " \
        "content parameters. Integer: Right-side diff line number to attach the inline comment to. " \
        "Valid only for changes and reviews topics."
    )
    content: Optional[List[str]] = Field(
        default="null",
        description="content optional, but if specified, you must also specify the leftline and rightline " \
        "parameters. Array of strings: Provide the content of the codeline the comment is on and the four " \
        "preceding codelines. Always add a newline character ('\n') to the end of each line in the array. ",
        examples=[["line1\n", "line2\n", "line3\n", "line4\n", "line5\n"]]
    )
    version: Optional[int] = Field(
        default=None,
        ge=1,
        description="integer: With a reviews topic, this field specifies which version to attach the comment to."
    )
    attribute: Optional[str] = Field(
        default=None,
        description="Set to description to comment on the review description"
    )
    comment: Optional[int] = Field(
        default=None,
        ge=1,
        description="integer: Set to the comment id this comment is replying to."
    )

    @field_validator("file")
    @classmethod
    def validate_depot_file(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.startswith("//"):
            raise ValueError("file must be a depot path starting with //")
        # basic depot path sanity check
        if not re.match(r"^//[\w./-]+$", v):
            raise ValueError("Invalid depot file path format")
        return v

    @model_validator(mode="after")
    def validate_context_semantics(self):
        """Validate context semantics."""
        if (self.leftLine is not None or self.rightLine is not None or self.content is not None):
            if self.leftLine is None or self.rightLine is None or self.content is None:
                raise ValueError("leftLine, rightLine, and content must all be specified together")
        return self

class ModifyReviewsParams(BaseParams):
    """Review modification parameters."""
    action: ReviewModifyAction = Field(
        description="Review modification action",
        examples=["create", "vote", "transition", "append_participants"]
    )

    # Common identifiers
    review_id: Optional[int] = Field(
        default=None,
        description="Review ID (required for most actions except create, archive_inactive)",
        examples=[12345]
    )
    change_id: Optional[int] = Field(
        default=None,
        description="Changelist ID (required for create, append_change, replace_with_change)",
        examples=[67890]
    )

    # Create
    description: Optional[str] = Field(
        default=None,
        description="Review description (optional on create)",
        examples=["Implement feature X"]
    )
    reviewers: Optional[List[str]] = Field(
        default=None,
        description="List of reviewers (create_participants)",
        examples=[["alice", "bob"]]
    )
    required_reviewers: Optional[List[str]] = Field(
        default=None,
        description="List of required reviewers (create_participants)",
        examples=[["carol"]]
    )
    reviewer_groups: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Reviewer groups (create_participants)",
        examples=[[{"name": "Developers", "required": "true"}]]
    )

    context: Optional[CommentContext] = Field(
        default=None,
        description="Cp",
        examples=[{"file": "//depot/path/file.txt", 
                   "rightLine": 42,
                   "leftLine": 40,
                   "content": ["def example_function():\n", "    pass\n"],
                   "version": 1,
                   "attribute": "description",
                   "comment": 22}]
    )

    # Vote
    vote_value: Optional[VoteValue] = Field(
        default=None,
        description="Vote value (vote action)",
        examples=["up", "down", "clear"]
    )
    version: Optional[int] = Field(
        default=None,
        ge=1,
        description="Review version (optional for vote)",
        examples=[2]
    )

    # Transition
    transition: Optional[ReviewTransition] = Field(
        default=None,
        description="Transition target state",
        examples=["approved"]
    )
    jobs: Optional[List[str]] = Field(
        default=None,
        description="Associated job IDs for transition",
        examples=[["job000123", "job000456"]]
    )
    fix_status: Optional[FixStatus] = Field(
        default=None,
        description="Job fix status when transitioning",
        examples=["closed"]
    )
    cleanup: Optional[bool] = Field(
        default=None,
        description="Perform cleanup for approved:commit/committed transitions",
        examples=[True]
    )

    # Participants (structured form)
    users: Optional[Dict[str, Dict[str, str]]] = Field(
        default=None,
        description="Usernames for append/replace/delete participants (username -> {'required': 'yes'|'no'})",
        examples=[{"alice": {"required": "yes"}, "bob": {"required": "no"}}]
    )
    groups: Optional[Dict[str, Dict[str, str]]] = Field(
        default=None,
        description="Group names for append/replace/delete participants (group -> {'required': 'none'|'one'|'all'})",
        examples=[{"dev-team": {"required": "all"}}]
    )

    # Comments
    body: Optional[str] = Field(
        default=None,
        description="Comment body (required for add_comment, reply_comment)",
        examples=["Looks good."]
    )
    task_state: Optional[TaskState] = Field(
        default=None,
        description="Task state (optional for add_comment)",
        examples=["open"]
    )
    notify: Optional[NotifyMode] = Field(
        default=None,
        description="Notification mode (optional for add_comment)",
        examples=["delayed"]
    )

    comment_id: Optional[int] = Field(
        default=None,
        description="Parent comment ID (reply_comment)",
        examples=[987]
    )

    # Archive inactive
    not_updated_since: Optional[str] = Field(
        default=None,
        description="ISO date (YYYY-MM-DD) threshold for archive_inactive",
        examples=["2024-01-15"]
    )
    max_reviews: Optional[int] = Field(
        default=0,
        ge=0,
        description="Maximum number of inactive reviews to archive (0 = no limit)",
        examples=[50]
    )

    # Update author/description
    new_author: Optional[str] = Field(
        default=None,
        description="New author username (update_author)",
        examples=["dave"]
    )
    new_description: Optional[str] = Field(
        default=None,
        description="New review description (update_description)",
        examples=["Refined implementation details."]
    )

    @model_validator(mode="after")
    def validate_required_fields(self):
        a = self.action

        def need(field: Any, label: Optional[str] = None):
            if not getattr(self, field, None):
                raise ValueError(f"{label or field} is required for action: {a}")

        # Actions requiring review_id
        if a not in [ReviewModifyAction.CREATE, ReviewModifyAction.ARCHIVE_INACTIVE] and a != ReviewModifyAction.CREATE:
            if a not in [ReviewModifyAction.ARCHIVE_INACTIVE] and not self.review_id:
                raise ValueError(f"review_id is required for action: {a}")

        if a == ReviewModifyAction.CREATE:
            need("change_id", "change_id")

        elif a in [ReviewModifyAction.APPEND_CHANGE, ReviewModifyAction.REPLACE_WITH_CHANGE]:
            need("review_id")
            need("change_id", "change_id")

        elif a == ReviewModifyAction.VOTE:
            need("review_id")
            need("vote_value", "vote_value")

        elif a == ReviewModifyAction.TRANSITION:
            need("review_id")
            need("transition", "transition")

        elif a == ReviewModifyAction.ADD_COMMENT:
            need("review_id")
            need("body", "body")

        elif a == ReviewModifyAction.REPLY_COMMENT:
            need("review_id")
            need("comment_id", "comment_id")
            need("body", "body")

        elif a == ReviewModifyAction.ARCHIVE_INACTIVE:
            need("not_updated_since", "not_updated_since")

        elif a == ReviewModifyAction.UPDATE_AUTHOR:
            need("review_id")
            need("new_author", "new_author")

        elif a == ReviewModifyAction.UPDATE_DESCRIPTION:
            need("review_id")
            need("new_description", "new_description")

        elif a == ReviewModifyAction.MARK_COMMENT_READ:
            need("comment_id", "comment_id")

        elif a == ReviewModifyAction.MARK_COMMENT_UNREAD:
            need("comment_id", "comment_id")

        elif a == ReviewModifyAction.MARK_ALL_COMMENTS_READ:
            need("review_id")

        elif a == ReviewModifyAction.MARK_ALL_COMMENTS_UNREAD:
            need("review_id")

        elif a == ReviewModifyAction.DELETE_PARTICIPANTS:
            need("review_id")
            if not self.users and not self.groups:
                raise ValueError("At least one of users or groups required for delete_participants action")

        return self
