"""
P4 code review services layer

Complete implementation of Swarm API v11 Review endpoints

GET endpoints:
- list_reviews : GET /api/v11/reviews
- review_dashboard : GET /api/v11/reviews/dashboard
- get_review_transitions : GET /api/v11/reviews/{id}/transitions
- get_review_info : GET /api/v11/reviews/{id}
- get_review_files_readby : GET /api/v11/reviews/{id}/files/readby
- get_review_files : GET /api/v11/reviews/{id}/files?from={x}&to={y}
- get_review_activity : GET /api/v11/reviews/{id}/activity
- get_review_comments : GET /api/v11/reviews/{id}/comments

POST endpoints:
- create_review : POST /api/v11/reviews
- refresh_review_projects : POST /api/v11/reviews/{id}/refreshProjects
- vote_review : POST /api/v11/reviews/{id}/vote
- transition_review_state : POST /api/v11/reviews/{id}/transitions
- append_participants : POST /api/v11/reviews/{id}/participants
- add_review_comment : POST /api/v11/reviews/{id}/comments
- reply_to_comment : POST /api/v11/reviews/{id}/comments
- append_change_to_review : POST /api/v11/reviews/{id}/appendchange
- replace_review_with_change : POST /api/v11/reviews/{id}/replacewithchange
- join_review : POST /api/v11/reviews/{id}/join
- archive_inactive_reviews : POST /api/v11/reviews/archiveInactive

POST Comments endpoints:
- mark_comment_as_read : POST /api/v11/comments/{id}/read
- mark_comment_as_unread : POST /api/v11/comments/{id}/unread
- mark_all_comments_as_read : POST /api/v11/reviews/{id}/comments/read
- mark_all_comments_as_unread : POST /api/v11/reviews/{id}/comments/unread

PUT endpoints:
X - update_review_author : PUT /api/v11/reviews/{id}/author
- update_review_description : PUT /api/v11/reviews/{id}/description
- replace_participants : PUT /api/v11/reviews/{id}/participants

DELETE endpoints:
- delete_participants : DELETE /api/v11/reviews/{id}/participants
- leave_review : DELETE /api/v11/reviews/{id}/leave
- obliterate_review : DELETE /api/v11/reviews/{id}

"""

import logging
from typing import List, Dict, Any, Optional
from P4 import P4Exception

import requests
from requests.auth import HTTPBasicAuth

from ..core.connection import P4ConnectionManager
from ..models.review_models import CommentContext

logger = logging.getLogger(__name__)


class ReviewServices:
    """
    P4 Code Reviews REST API Client (v11)
    Covers all major review endpoints from Swarm API 2025.2
    """

    def __init__(self, connection_manager: P4ConnectionManager, verify_ssl: bool = True):
        self.connection_manager = connection_manager
        self.verify_ssl = verify_ssl

    async def _get_auth(self):
        """Get authentication credentials from P4 connection"""
        async with self.connection_manager.get_connection() as p4:
            try:
                username = p4.user
                ticket = p4.password
                
                if not ticket or ticket.strip() == "":
                    logger.error(f"P4Error: No valid ticket found for user '{username}'. Please run 'p4 login'.")
                    raise Exception(f"No P4 ticket found for user '{username}'. Please run 'p4 login' first.")
                
                return HTTPBasicAuth(username, ticket)
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get authentication credentials: {e}")
                raise

    async def _get_api_base(self):
        async with self.connection_manager.get_connection() as p4:
            try:
                prop = p4.run("property", "-l", "-n", "P4.Swarm.URL")
                swarm_url = prop[0].get('value', None)
                if not swarm_url:
                    raise Exception("Swarm URL not configured on the server.")
                self.api_base = f"{swarm_url.rstrip('/')}/api/v11"
                return self.api_base
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get Swarm URL: {e}")
                raise

    def _handle_response(self, response):
        if response.ok:
            try:
                return response.json()
            except Exception:
                return {"message": response.text}
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        
    # ============================================================================
    # GET endpoints
    # ============================================================================
    
    async def list_reviews(
            self,
            max_results: int = 50,
            after: Optional[str] = None,
            after_updated: Optional[str] = None,
            result_order: Optional[str] = None,
            author: Optional[List[str]] = None,
            change: Optional[List[int]] = None,
            projects: Optional[List[str]] = None,
            state: Optional[List[str]] = None,
            keywords: Optional[str] = None,
            keywords_fields: Optional[List[str]] = None,
            fields: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
        """GET /api/v11/reviews - List reviews with optional filters (v11 compliant)"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews"
            params = {"max": max_results}

            # pagination
            if after:
                params["after"] = after
            if after_updated:
                params["afterUpdated"] = after_updated
            if result_order:
                params["resultOrder"] = result_order

            # filters
            if author:
                params["author[]"] = author
            if change:
                # v11 has no change[] param; use keywords + keywordsFields instead
                params["keywords"] = " ".join(str(c) for c in change)
                params["keywordsFields[]"] = ["changes"]
            if projects:
                params["project[]"] = projects
            if state:
                params["state[]"] = state
            if keywords:
                params["keywords"] = keywords
            if keywords_fields:
                params["keywordsFields[]"] = keywords_fields

            # limit returned fields
            if fields:
                params["fields[]"] = fields

            r = requests.get(url, auth=auth, params=params, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to list reviews: {e}")
            return {"status": "error", "message": str(e)}

    async def review_dashboard(
            self, 
            max_results: int = 10
        ) -> Dict[str, Any]:
        """GET /api/v11/reviews/dashboard - Get review dashboard for current user"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/dashboard"
            params = {"max": max_results}
            r = requests.get(url, auth=auth, params=params, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to get review dashboard: {e}")
            return {"status": "error", "message": str(e)}
        
    async def get_review_transitions(
            self, 
            review_id: int
        ) -> Dict[str, Any]:
        """GET /api/v11/reviews/{id}/transitions - Get transitions and blockers for a review"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/transitions"
            r = requests.get(url, auth=auth, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to get transitions for review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def get_review_info(
            self,
            review_id: int,
            fields: Optional[List[str]] = None,
            include_transitions: bool = False,
        ) -> Dict[str, Any]:
        """GET /api/v11/reviews/{id} - Get information about a review"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}"
            params = {}

            if fields:
                params["fields[]"] = fields
            if include_transitions:
                params["transitions"] = "true"

            r = requests.get(url, auth=auth, params=params if params else None, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to get review info for '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def get_review_files_readby(
            self, 
            review_id: int
        ) -> Dict[str, Any]:
        """GET /api/v11/reviews/{id}/files/readby - Get read status of review files"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/files/readby"
            r = requests.get(url, auth=auth, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to get review files readby for '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def get_review_files(
            self,
            review_id: int,
            from_version: Optional[int] = None,
            to_version: Optional[int] = None
        ) -> Dict[str, Any]:
        """GET /api/v11/reviews/{id}/files?from={x}&to={y}
        Get list of files that changed between specified versions of a review.
        """
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/files"
            params = {}

            if from_version is not None:
                params["from"] = from_version
            if to_version is not None:
                params["to"] = to_version

            r = requests.get(url, auth=auth, params=params if params else None, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to get review files for '{review_id}': {e}")
            return {"status": "error", "message": str(e)}
        
    async def get_review_activity(
            self, 
            review_id: int, 
            max_results: int = 100
        ) -> Dict[str, Any]:
        """GET /api/v11/reviews/{id}/activity - Get activity for a review"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/activity"

            params = {}
            if max_results:
                params["max"] = max_results

            r = requests.get(url, auth=auth, params=params if params else None, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to get activity for review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}
        
    async def get_review_comments(
            self, 
            review_id: int
        ) -> Dict[str, Any]:
        """GET /api/v11/reviews/{id}/comments - Get a list of comments on a review"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/comments"
            r = requests.get(url, auth=auth, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to get comments for review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # POST endpoints
    # ============================================================================

    async def create_review(
            self,
            change_id: int,
            description: Optional[str] = None,
            reviewers: Optional[List[str]] = None,
            required_reviewers: Optional[List[str]] = None,
            reviewer_groups: Optional[List[Dict[str, Any]]] = None,
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews - Create a new review
        
        Args:
            change_id = "12345"
            description = "This is the review description."
            reviewers = ["raj", "mei"]
            required_reviewers = ["vera", "dai"]
            reviewer_groups = [
                {"name":"WebDesigners", "required":"true", "quorum":"1"},
                {"name":"Developers", "required":"true"},
                {"name":"Administrators"}
            ]
            state = "needsReview"
        """
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews"
            payload: Dict[str, Any] = {"change": change_id}

            if description:
                payload["description"] = description

            if reviewers:
                payload["reviewers"] = reviewers

            if required_reviewers:
                payload["requiredReviewers"] = required_reviewers

            if reviewer_groups:
                payload["reviewerGroups"] = reviewer_groups

            r = requests.post(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to create review for changelist '{change_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def refresh_review_projects(
            self, 
            review_id: int
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/refreshProjects - Refresh project associations for a review"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/refreshProjects"
            r = requests.post(url, auth=auth, json={}, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to refresh projects for review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def vote_review(
            self,
            review_id: int,
            vote_value: str = "up",
            version: Optional[int] = None
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/vote - Vote on a review
        
        Args:
            review_id = "12345"
            vote_value = "up"|"down"|"clear"
            version = 1
        """
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/vote"
            payload = {"vote": vote_value}

            if version is not None:
                payload["version"] = version

            r = requests.post(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to vote on review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def transition_review_state(
            self,
            review_id: int,
            transition: str,
            jobs: Optional[List[str]] = None,
            fix_status: Optional[str] = None,
            cleanup: Optional[bool] = None,
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/transitions - Change review state
        
        Args:
            review_id = "12345"                 
            transition = "needsRevision"|"needsReview"|"approved"|"committed"|"approved:commit"|"rejected"|"archived"
            jobs = ["job000001", "job000015"]   
            fix_status = "closed"|"open"
            cleanup = True|False
        """
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/transitions"

            payload: Dict[str, Any] = {"transition": transition}

            if jobs:
                payload["jobs"] = jobs

            if fix_status:
                payload["fixStatus"] = fix_status

            if cleanup is not None:
                payload["cleanup"] = cleanup

            r = requests.post(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to transition review state for '{review_id}': {e}")
            return {"status": "error", "message": str(e)}
        
    async def append_participants(
            self,
            review_id: int,
            users: Optional[List[str]] = None,
            groups: Optional[List[str]] = None
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/participants - Append participants to review
        
        Args:            
            review_id = "12345"
            users = ["alice", "bob"]
            groups = ["dev-team", "qa-team"]
        """
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/participants"
            payload = {"participants": {}}

            if users:
                payload["participants"]["users"] = users

            if groups:
                payload["participants"]["groups"] = groups

            r = requests.post(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to append participants for review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def add_review_comment(
            self,
            review_id: int, 
            body: str,
            task_state: Optional[str] = None,
            notify: Optional[str] = None,
            context: Optional[CommentContext] = None,
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/comments - Add a comment to a review
        
        Args:
            review_id = "885"
            body = "This is a comment."
            task_state = "open"|"comment"
            notify = "delayed"|"immediate"
            context = {
                    "file": "//depot/path/to/file.txt",    # string, required if commenting on a file
                    "leftLine": 10,                        # integer, optional: left-side diff line number
                    "rightLine": 12,                       # integer, optional: right-side diff line number
                    "content": [                           # array of strings, optional: code context (lines)
                        "line n-4 text",
                        "line n-3 text",
                        "line n-2 text",
                        "line n-1 text",
                        "line n text"
                    ],
                    "version": 2,                           # integer, optional: review version
                    "attribute": "description",             # string, optional: comment on the review description
                    "comment": 99                           # integer, optional: replying to another comment
                }
        """
        
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/comments"
            params = {}
            if notify:
                params["notify"] = notify

            payload = {"body": body}

            if context:
                payload["context"] = {}
                if context.file:
                    payload["context"]["file"] = context.file
                if context.leftLine is not None:
                    payload["context"]["leftLine"] = context.leftLine
                if context.rightLine is not None:
                    payload["context"]["rightLine"] = context.rightLine
                if context.content:
                    # AI is adding random content so for now we skip adding empty content
                    payload["context"]["content"] = []
                if context.version is not None:
                    payload["context"]["version"] = context.version
                if context.attribute:
                    payload["context"]["attribute"] = context.attribute
                if context.comment is not None:
                    payload["context"]["comment"] = context.comment

            if task_state:
                payload["taskState"] = task_state

            r = requests.post(url, auth=auth, params=params, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to add comment to review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def reply_to_comment(
            self, 
            review_id: int, 
            comment_id: str,
            body: str
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/comments - Reply to a comment
        
        Args:
            review_id = "885"
            comment_id = "1234"
            body = "This is a reply to the comment."
        """
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/comments"
            payload = {"body": body, "context" : {}}
            payload["context"]["comment"] = int(comment_id)
            r = requests.post(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to reply to comment '{comment_id}' in review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}
        
    async def append_change_to_review(
            self, 
            review_id: int, 
            change_id: int
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/appendchange - Append a changelist to a pre-commit review"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/appendchange"
            payload = {"changeId": change_id}
            r = requests.post(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to append change '{change_id}' to review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}
        
    async def replace_review_with_change(
            self, 
            review_id: int, 
            change_id: int
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/replacewithchange - Replace review with a new change"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/replacewithchange"
            payload = {"changeId": change_id}
            r = requests.post(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}

        except Exception as e:
            logger.error(f"Failed to replace review '{review_id}' with change '{change_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def join_review(
            self, 
            review_id: int
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/join - Join a review as a participant"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/join"
            body = {
                        "participants": {
                            "users": {
                               auth.username : []
                            }
                        }
                    }
            r = requests.post(url, auth=auth, json=body, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to join review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def archive_inactive_reviews(
            self, 
            not_updated_since: str,
            max_reviews: int = 0,
            description: str = "Archiving inactive reviews"
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/archiveInactive - Archive inactive reviews
        
        Args:
            not_updated_since = "2023-06-06"
            max_reviews = 50
            description = "This is the description"
        """
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/archiveInactive"
            payload = {
                "notUpdatedSince": not_updated_since,
                "description": description
            }

            if max_reviews > 0:
                payload["max"] = max_reviews

            r = requests.post(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to archive inactive reviews: {e}")
            return {"status": "error", "message": str(e)}
        

    # ============================================================================
    # POST Comments endpoints
    # ============================================================================

    async def mark_comment_as_read(
            self, 
            comment_id: int
        ) -> Dict[str, Any]:
        """POST /api/v11/comments/{id}/read - Mark a comment as read"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/comments/{comment_id}/read"
            r = requests.post(url, auth=auth, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to mark comment '{comment_id}' as read: {e}")
            return {"status": "error", "message": str(e)}
        
    async def mark_comment_as_unread(
            self,
            comment_id: int
        ) -> Dict[str, Any]:
        """POST /api/v11/comments/{id}/unread - Mark a comment as unread"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/comments/{comment_id}/unread"
            r = requests.post(url, auth=auth, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to mark comment '{comment_id}' as unread: {e}")
            return {"status": "error", "message": str(e)}
        
    async def mark_all_comments_as_read(
            self,
            review_id: int
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/comments/read - Mark all comments in a review as read"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/comments/read"
            r = requests.post(url, auth=auth, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to mark all comments in review '{review_id}' as read: {e}")
            return {"status": "error", "message": str(e)}
        
    async def mark_all_comments_as_unread(
            self,
            review_id: int
        ) -> Dict[str, Any]:
        """POST /api/v11/reviews/{id}/comments/unread - Mark all comments in a review as unread"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/comments/unread"
            r = requests.post(url, auth=auth, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to mark all comments in review '{review_id}' as unread: {e}")
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # PUT endpoints
    # ============================================================================

    async def update_review_author(
            self, 
            review_id: int, 
            new_author: str
        ) -> Dict[str, Any]:
        """PUT /api/v11/reviews/{id}/author - Update review author

        Args:
            review_id: The review ID
            new_author: The new author username
        """
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/author"
            payload = {"author": new_author}
            r = requests.put(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to update author for review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def update_review_description(
            self, 
            review_id: int, 
            new_description: str
        ) -> Dict[str, Any]:
        """PUT /api/v11/reviews/{id}/description - Update review description

        Args:
            review_id: The review ID
            new_description: The new description text
        """
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/description"
            payload = {"description": new_description}
            r = requests.put(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to update description for review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def replace_participants(
            self, 
            review_id: int, 
            users: Optional[Dict[str, Dict[str, str]]] = None,
            groups: Optional[Dict[str, Dict[str, str]]] = None
        ) -> Dict[str, Any]:
        """PUT /api/v11/reviews/{id}/participants - Replace all participants
        
        Args:
            review_id: The review ID
            users: Dict of username -> {"required": "yes"|"no"}
            groups: Dict of groupname -> {"required": "none"|"all"|"one"}
        """
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/participants"
            payload = {"participants": {}}
            if users:
                payload["participants"]["users"] = users
            if groups:
                payload["participants"]["groups"] = groups
                        
            r = requests.put(url, auth=auth, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to replace participants for review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # DELETE endpoints
    # ============================================================================

    async def delete_participants(self, review_id: int,
                                 users: Optional[List[str]] = None,
                                 groups: Optional[List[str]] = None) -> Dict[str, Any]:
        """DELETE /api/v11/reviews/{id}/participants - Delete participants from review"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}/participants"

            body = {"participants": {}}

            if users:
                body["participants"]["users"] = {u: [] for u in users}

            if groups:
                body["participants"]["groups"] = {g: [] for g in groups}
                
            r = requests.delete(url, auth=auth, json=body, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to delete participants from review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def leave_review(self, review_id: int) -> Dict[str, Any]:
        """DELETE /api/v11/reviews/{id}/leave - Leave a review"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            body = {
                        "participants": {
                            "users": {
                               auth.username : []
                            }
                        }
                    }
            
            url = f"{api_base}/reviews/{review_id}/leave"
            r = requests.delete(url, auth=auth, json=body, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to leave review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}

    async def obliterate_review(self, review_id: int) -> Dict[str, Any]:
        """DELETE /api/v11/reviews/{id} - Obliterate (permanently delete) a review"""
        try:
            auth = await self._get_auth()
            api_base = await self._get_api_base()
            url = f"{api_base}/reviews/{review_id}"
            r = requests.delete(url, auth=auth, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error(f"Failed to obliterate review '{review_id}': {e}")
            return {"status": "error", "message": str(e)}