import logging
from .utils import handle_errors

logger = logging.getLogger(__name__)

class ReviewsHandlers:

    def __init__(self, review_services):
        self.review_services = review_services

    @handle_errors
    async def _handle_query_reviews(self, params):
        actions_requiring_id = [
            "get", "transitions", "files_readby", "files",
            "activity", "archive", "comments"
        ]

        if params.action in actions_requiring_id and not params.review_id:
            logger.error(f"review_id is required for action: {params.action}")
            raise ValueError(f"review_id is required for action: {params.action}")

        if params.action == "list":
            result = await self.review_services.list_reviews(
                max_results=params.max_results,
                after=params.after,
                after_updated=params.after_updated,
                result_order=params.result_order,
                projects=params.projects,
                state=params.state,
                keywords=params.keywords,
                keywords_fields=params.keywords_fields,
                fields=params.fields,
            )

        elif params.action == "dashboard":
            # review_dashboard(max_results)
            result = await self.review_services.review_dashboard(
                getattr(params, "max_results", None)
            )

        elif params.action == "transitions":
            # get_review_transitions(review_id)
            result = await self.review_services.get_review_transitions(
                params.review_id
            )

        elif params.action == "get":
            result = await self.review_services.get_review_info(
                params.review_id,
                params.fields,
                params.include_transitions or False,
            )

        elif params.action == "files_readby":
            # get_review_files_readby(review_id)
            result = await self.review_services.get_review_files_readby(
                params.review_id
            )

        elif params.action == "files":
            # get_review_files(review_id, from_version, to_version)
            result = await self.review_services.get_review_files(
                params.review_id,
                getattr(params, "from_version", None),
                getattr(params, "to_version", None)
            )

        elif params.action == "activity":
            # get_review_activity(review_id, max_results, after, fields)
            result = await self.review_services.get_review_activity(
                params.review_id,
                getattr(params, "max_results", None),
            )

        elif params.action == "comments":
            # get_review_comments(review_id)
            result = await self.review_services.get_review_comments(
                params.review_id
            )

        else:
            logger.error(f"Unknown review query action: {params.action}")
            raise ValueError(f"Unknown review query action: {params.action}")

        return {
            "status": result["status"],
            "action": params.action,
            "message": result["message"]
        }

    @handle_errors
    async def _handle_modify_reviews(self, params):
        # Validation helpers
        def require(attr, label=None):
            if not getattr(params, attr, None):
                lbl = label or attr
                logger.error(f"{lbl} is required for {params.action} action")
                raise ValueError(f"{lbl} is required for {params.action} action")

        action = params.action

        # POST actions
        if action == "create":
            require("change_id", "change_id")
            result = await self.review_services.create_review(
                change_id=params.change_id,
                description=getattr(params, "description", None),
                reviewers=getattr(params, "reviewers", None),
                required_reviewers=getattr(params, "required_reviewers", None),
                reviewer_groups=getattr(params, "reviewer_groups", None),
            )

        elif action == "refresh_projects":
            require("review_id")
            result = await self.review_services.refresh_review_projects(params.review_id)

        elif action == "vote":
            require("review_id")
            require("vote_value", "vote_value")
            result = await self.review_services.vote_review(
                params.review_id,
                getattr(params, "vote_value", "up"),
                getattr(params, "version", None)
            )

        elif action == "transition":
            require("review_id")
            require("transition", "transition")
            result = await self.review_services.transition_review_state(
                params.review_id,
                params.transition,
                getattr(params, "jobs", None),
                getattr(params, "fix_status", None),
                getattr(params, "cleanup", None)
            )

        elif action == "append_participants":
            require("review_id")
            result = await self.review_services.append_participants(
                params.review_id,
                getattr(params, "users", None),
                getattr(params, "groups", None)
            )

        elif action == "add_comment":
            require("review_id")
            require("body", "body")
            result = await self.review_services.add_review_comment(
                params.review_id,
                params.body,
                getattr(params, "task_state", None),
                getattr(params, "notify", None),
                getattr(params, "context", None)
            )

        elif action == "reply_comment":
            require("review_id")
            require("comment_id", "comment_id")
            require("body", "body")
            result = await self.review_services.reply_to_comment(
                params.review_id,
                params.comment_id,
                params.body
            )

        elif action == "append_change":
            require("review_id")
            require("change_id", "change_id")
            result = await self.review_services.append_change_to_review(
                params.review_id,
                params.change_id
            )

        elif action == "replace_with_change":
            require("review_id")
            require("change_id", "change_id")
            result = await self.review_services.replace_review_with_change(
                params.review_id,
                params.change_id
            )

        elif action == "join":
            require("review_id")
            result = await self.review_services.join_review(params.review_id)

        elif action == "archive_inactive":
            require("not_updated_since", "not_updated_since")
            result = await self.review_services.archive_inactive_reviews(
                params.not_updated_since,
                getattr(params, "max_reviews", 0),
                getattr(params, "description", "Archiving inactive reviews")
            )

        # POST Comments actions
        elif action == "mark_comment_read":
            require("comment_id", "comment_id")
            result = await self.review_services.mark_comment_as_read(
                params.comment_id
            )

        elif action == "mark_comment_unread":
            require("comment_id", "comment_id")
            result = await self.review_services.mark_comment_as_unread(
                params.comment_id
            )

        elif action == "mark_all_comments_read":
            require("review_id")
            result = await self.review_services.mark_all_comments_as_read(
                params.review_id
            )

        elif action == "mark_all_comments_unread":
            require("review_id")
            result = await self.review_services.mark_all_comments_as_unread(
                params.review_id
            )

        # PUT actions
        elif action == "update_author":
            require("review_id")
            require("new_author", "new_author")
            result = await self.review_services.update_review_author(
                params.review_id,
                params.new_author
            )

        elif action == "update_description":
            require("review_id")
            require("new_description", "new_description")
            result = await self.review_services.update_review_description(
                params.review_id,
                params.new_description
            )

        elif action == "replace_participants":
            require("review_id")
            result = await self.review_services.replace_participants(
                params.review_id,
                getattr(params, "users", None),
                getattr(params, "groups", None)
            )

        # DELETE actions
        elif action == "delete_participants":
            require("review_id")
            result = await self.review_services.delete_participants(
                params.review_id,
                getattr(params, "users", None),
                getattr(params, "groups", None)
            )

        elif action == "leave":
            require("review_id")
            result = await self.review_services.leave_review(params.review_id)

        elif action == "obliterate":
            require("review_id")
            result = await self.review_services.obliterate_review(params.review_id)

        else:
            logger.error(f"Unknown review modify action: {action}")
            raise ValueError(f"Unknown review modify action: {action}")

        return {"status": result["status"], "action": action, "message": result["message"]}