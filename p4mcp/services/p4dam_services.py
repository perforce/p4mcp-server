"""P4 DAM REST service layer.

Endpoints implemented:
- search_assets              : POST  <P4.HTH.URL>/api/search
- get_asset                  : GET   <P4.HTH.URL>/api/p4/tree
- list_projects              : GET   <P4.HTH.URL>/api/projects
- list_repositories          : GET   <P4.HTH.URL>/api/projects/:id/repositories
- list_helix_classic_branches: GET   <P4.HTH.URL>/api/projects/:id/repositories/:id/helix_classic_branches
- create_asset_bundle        : POST  <P4.HTH.URL>/api/asset_bundles
- update_asset_bundle        : PATCH <P4.HTH.URL>/api/asset_bundles/:uuid
- delete_asset_bundle        : DELETE <P4.HTH.URL>/api/asset_bundles/:uuid
- sync_asset_bundle          : p4 sync via P4CLIENT workspace
- list_file_reviews          : GET   <P4.HTH.URL>/api/projects/:id/file_reviews
- get_file_review            : GET   <P4.HTH.URL>/api/projects/:id/file_reviews/:uuid
- create_file_review         : POST  <P4.HTH.URL>/api/projects/:id/file_reviews
- update_file_review         : PATCH <P4.HTH.URL>/api/projects/:id/file_reviews/:uuid
- delete_file_review         : DELETE <P4.HTH.URL>/api/projects/:id/file_reviews/:uuid
- list_workflows             : GET   <P4.HTH.URL>/api/workflows
- get_workflow               : GET   <P4.HTH.URL>/api/workflows/:uuid
- list_workflow_states       : GET   <P4.HTH.URL>/api/workflows/:workflow_id/states
- update_asset_tags          : PUT   <P4.HTH.URL>/api/p4/batch/tags
- list_custom_attr_templates : GET   <P4.HTH.URL>/api/projects/:id/file_attribute_templates
- update_asset_custom_attrs  : PUT   <P4.HTH.URL>/api/p4/batch/custom_file_attributes
- regenerate_preview         : PUT   <P4.HTH.URL>/api/p4/commits/:id/regenerate_preview
- create_comment             : POST  <P4.HTH.URL>/api/comments

Auth: static API key from ``P4DAM_API_KEY``, sent as
``Authorization: account_key='<key>'`` per the P4 DAM v1 authentication module.

Base URL: discovered from the P4 property ``P4.HTH.URL`` (mirrors the
``P4.Swarm.URL`` pattern used by ``review_services``).
"""

import logging
from typing import Any, Dict, List, Optional, Union
import os
from urllib.parse import urlsplit

import requests
from P4 import P4Exception

from ..core.connection import P4ConnectionManager

logger = logging.getLogger(__name__)


_DEFAULT_ASSET_INCLUDE = [
    "commit", "latest_commit", "custom_attributes", "weblinks",
    "asset_bundle", "parent_asset_bundles", "asset_bundle_origin",
    "helix_classic_branch_matches", "stream_view_matches",
    "file_review", "sprite",
]


class P4DamServices:
    """P4 DAM REST API client."""

    def __init__(
        self,
        connection_manager: P4ConnectionManager,
        api_key: Optional[str] = None,
        verify_ssl: Union[bool, str] = True,
    ):
        """
        Args:
            connection_manager: P4 connection manager (used for URL discovery).
            api_key: Static P4 DAM API key (account_key). Required at call
                time; when missing the service errors with a clear message
                rather than failing at startup.
            verify_ssl: SSL verification for P4 DAM API requests. Shares the
                same knobs as Swarm/reviews.
                True – verify with default CA bundle (default).
                False – disable verification entirely.
                str – path to a custom CA certificate bundle (PEM).
        """
        self.connection_manager = connection_manager
        self.api_key = api_key
        self.verify_ssl = verify_ssl

    async def _get_api_base(self) -> str:
        async with self.connection_manager.get_connection() as p4:
            try:
                prop = p4.run("property", "-l", "-n", "P4.HTH.URL")
                prop_dicts = [p for p in prop if isinstance(p, dict)]
                dam_url = prop_dicts[0].get("value") if prop_dicts else None
                if not dam_url:
                    raise Exception(
                        "P4 DAM URL not configured on the server "
                        "(P4.HTH.URL property is not set)."
                    )
                return dam_url.rstrip("/")
            except P4Exception as e:
                logger.error("P4Error: Failed to get P4 DAM URL: %s", e)
                raise

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise Exception(
                "P4 DAM API key is not configured. "
                "Set P4DAM_API_KEY to enable P4 DAM tools."
            )
        return {
            "Authorization": f"account_key='{self.api_key}'",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _handle_response(self, response: requests.Response) -> Any:
        if response.ok:
            try:
                return response.json()
            except Exception:
                return {"message": response.text}
        if response.status_code == 401 and "P4 Server session expired" in response.text:
            raise Exception(
                "P4 DAM's cached P4 Server ticket has expired. Log in to the P4 DAM UI, or use P4 DAM API to refresh it. "
                "Note: this is the P4 Server ticket belonging to the account for whom P4DAM_API_KEY was configured"
            )
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------

    async def get_asset(
        self,
        depot_path: Optional[str] = None,
        path: Optional[str] = None,
        stream_path: Optional[str] = None,
        identifier: Optional[str] = None,
        project_id: Optional[str] = None,
        repository_id: Optional[str] = None,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """GET /api/p4/tree - Fetch detailed metadata for a single asset."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            params: Dict[str, str] = {
                "include": ",".join(include if include is not None else _DEFAULT_ASSET_INCLUDE),
            }
            if path is not None:
                params["path"] = path
            elif depot_path is not None:
                params["depot_path"] = depot_path
            if stream_path is not None:
                params["stream_path"] = stream_path
            if identifier is not None:
                params["identifier"] = identifier
            if project_id is not None:
                params["project_id"] = project_id
            if repository_id is not None:
                params["repository_id"] = repository_id
            r = requests.get(f"{base}/api/p4/tree", headers=headers,
                             params=params, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to get P4 DAM asset: %s", e)
            return {"status": "error", "message": str(e)}

    async def search_assets(
        self,
        search_term: Optional[str] = None,
        project_ids: Optional[List[str]] = None,
        repository_ids: Optional[List[str]] = None,
        path: Optional[List[str]] = None,
        name: Optional[str] = None,
        tag: Optional[List[str]] = None,
        file_extension: Optional[List[str]] = None,
        exclude_file_extension: Optional[List[str]] = None,
        user: Optional[List[str]] = None,
        from_size: Optional[int] = None,
        to_size: Optional[int] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        all_revisions: bool = False,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """POST /api/search - Search for P4 DAM assets (files)."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            url = f"{base}/api/search"
            payload = {
                "limit": limit,
                "offset": offset,
                "types": ["files"],
                "source": "helix",
                "path": path or [],
                "project_ids": project_ids or [],
                "repository_ids": repository_ids or [],
                "tag": tag or [],
                "search_term": search_term or "",
                "file_extension": file_extension or [],
                "user": user or [],
                "all_revisions": all_revisions,
            }
            if name:
                payload["name"] = name
            if exclude_file_extension:
                payload["exclude_file_extension"] = exclude_file_extension
            if from_size is not None:
                payload["from_size"] = from_size
            if to_size is not None:
                payload["to_size"] = to_size
            if from_date:
                payload["from_date"] = from_date
            if to_date:
                payload["to_date"] = to_date
            r = requests.post(url, headers=headers, json=payload, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to search P4 DAM assets: %s", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    async def list_projects(
        self,
        search_term: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """GET /api/projects - List P4 DAM projects."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            params: Dict[str, Any] = {"limit": limit, "offset": offset}
            if search_term:
                params["search_term"] = search_term
            r = requests.get(f"{base}/api/projects", headers=headers,
                             params=params, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to list P4 DAM projects: %s", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Repositories
    # ------------------------------------------------------------------

    async def list_repositories(
        self,
        project_id: str,
        search_term: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """GET /api/projects/:project_id/repositories - List repositories in a project."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            params: Dict[str, Any] = {"limit": limit, "offset": offset}
            if search_term:
                params["search_term"] = search_term
            r = requests.get(f"{base}/api/projects/{project_id}/repositories",
                             headers=headers, params=params, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to list P4 DAM repositories: %s", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Helix Classic Branches
    # ------------------------------------------------------------------

    async def list_helix_classic_branches(
        self,
        project_id: str,
        repository_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """GET /api/projects/:project_id/repositories/:repository_id/helix_classic_branches"""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            params: Dict[str, Any] = {"limit": limit, "offset": offset}
            r = requests.get(
                f"{base}/api/projects/{project_id}/repositories/{repository_id}/helix_classic_branches",
                headers=headers, params=params, verify=self.verify_ssl,
            )
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to list P4 DAM helix classic branches: %s", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Asset Bundle CRUD
    # ------------------------------------------------------------------

    async def create_asset_bundle(
        self,
        depot_path: str,
        project: str,
        repository: str,
        view_paths: List[str],
        stream_path: Optional[str] = None,
        helix_classic_branch: Optional[str] = None,
        description: Optional[str] = None,
        hero_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/asset_bundles - Create an asset bundle."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            body: Dict[str, Any] = {
                "asset_bundle": {
                    "depot_path": depot_path,
                    "project": project,
                    "repository": repository,
                    "view_paths": view_paths,
                }
            }
            if stream_path is not None:
                body["asset_bundle"]["stream_path"] = stream_path
            if helix_classic_branch is not None:
                body["asset_bundle"]["helix_classic_branch"] = helix_classic_branch
            if description is not None:
                body["asset_bundle"]["description"] = description
            if hero_file_path is not None:
                body["asset_bundle"]["hero_file_path"] = hero_file_path
            r = requests.post(f"{base}/api/asset_bundles", headers=headers,
                              json=body, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to create P4 DAM asset bundle: %s", e)
            return {"status": "error", "message": str(e)}

    async def update_asset_bundle(
        self,
        bundle_id: str,
        description: Optional[str] = None,
        view_paths: Optional[List[str]] = None,
        hero_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """PATCH /api/asset_bundles/:uuid - Update an asset bundle."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            body: Dict[str, Any] = {"asset_bundle": {}}
            if description is not None:
                body["asset_bundle"]["description"] = description
            if view_paths is not None:
                body["asset_bundle"]["view_paths"] = view_paths
            if hero_file_path is not None:
                body["asset_bundle"]["hero_file_path"] = hero_file_path
            r = requests.patch(f"{base}/api/asset_bundles/{bundle_id}", headers=headers,
                               json=body, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to update P4 DAM asset bundle: %s", e)
            return {"status": "error", "message": str(e)}

    async def delete_asset_bundle(
        self,
        bundle_id: str,
    ) -> Dict[str, Any]:
        """DELETE /api/asset_bundles/:uuid - Delete an asset bundle."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            r = requests.delete(f"{base}/api/asset_bundles/{bundle_id}", headers=headers,
                                verify=self.verify_ssl)
            if r.status_code == 204:
                return {"status": "success", "message": "Asset bundle deleted."}
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to delete P4 DAM asset bundle: %s", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # File Reviews
    # ------------------------------------------------------------------

    async def list_file_reviews(
        self,
        project_id: str,
        depot_path: Optional[str] = None,
        include: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """GET /api/projects/:project_id/file_reviews - List file reviews in a project."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            params: Dict[str, Any] = {"limit": limit, "offset": offset}
            if depot_path is not None:
                params["depot_path"] = depot_path
            if include:
                params["include"] = ",".join(include)
            r = requests.get(
                f"{base}/api/projects/{project_id}/file_reviews",
                headers=headers, params=params, verify=self.verify_ssl,
            )
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to list P4 DAM file reviews: %s", e)
            return {"status": "error", "message": str(e)}

    async def get_file_review(
        self,
        project_id: str,
        review_id: str,
    ) -> Dict[str, Any]:
        """GET /api/projects/:project_id/file_reviews/:uuid - Get a single file review."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            r = requests.get(
                f"{base}/api/projects/{project_id}/file_reviews/{review_id}",
                headers=headers, verify=self.verify_ssl,
            )
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to get P4 DAM file review: %s", e)
            return {"status": "error", "message": str(e)}

    async def create_file_review(
        self,
        project_id: str,
        name: str,
        depot_path: str,
        view_paths: List[str],
        state: str,
        repository: Optional[str] = None,
        helix_classic_branch: Optional[str] = None,
        asset_bundle: Optional[str] = None,
        hero_file_path: Optional[str] = None,
        description: Optional[str] = None,
        position: Optional[int] = None,
        base_commit_id: Optional[str] = None,
        head_commit_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/projects/:project_id/file_reviews - Create a file review."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            inner: Dict[str, Any] = {
                "name": name,
                "depot_path": depot_path,
                "view_paths": view_paths,
                "state": state,
            }
            if repository is not None:
                inner["repository"] = repository
            if helix_classic_branch is not None:
                inner["helix_classic_branch"] = helix_classic_branch
            if asset_bundle is not None:
                inner["asset_bundle"] = asset_bundle
            if hero_file_path is not None:
                inner["hero_file_path"] = hero_file_path
            if description is not None:
                inner["description"] = description
            if position is not None:
                inner["position"] = position
            if base_commit_id is not None:
                inner["base_commit_id"] = base_commit_id
            if head_commit_id is not None:
                inner["head_commit_id"] = head_commit_id
            r = requests.post(
                f"{base}/api/projects/{project_id}/file_reviews",
                headers=headers, json={"file_review": inner}, verify=self.verify_ssl,
            )
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to create P4 DAM file review: %s", e)
            return {"status": "error", "message": str(e)}

    async def update_file_review(
        self,
        project_id: str,
        review_id: str,
        state: Optional[str] = None,
        name: Optional[str] = None,
        view_paths: Optional[List[str]] = None,
        hero_file_path: Optional[str] = None,
        description: Optional[str] = None,
        position: Optional[int] = None,
    ) -> Dict[str, Any]:
        """PATCH /api/projects/:project_id/file_reviews/:uuid - Update a file review.

        The PATCH body is sent flat (not nested under file_review).
        """
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            body: Dict[str, Any] = {}
            if state is not None:
                body["state"] = state
            if name is not None:
                body["name"] = name
            if view_paths is not None:
                body["view_paths"] = view_paths
            if hero_file_path is not None:
                body["hero_file_path"] = hero_file_path
            if description is not None:
                body["description"] = description
            if position is not None:
                body["position"] = position
            r = requests.patch(
                f"{base}/api/projects/{project_id}/file_reviews/{review_id}",
                headers=headers, json=body, verify=self.verify_ssl,
            )
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to update P4 DAM file review: %s", e)
            return {"status": "error", "message": str(e)}

    async def delete_file_review(
        self,
        project_id: str,
        review_id: str,
    ) -> Dict[str, Any]:
        """DELETE /api/projects/:project_id/file_reviews/:uuid - Delete a file review."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            r = requests.delete(
                f"{base}/api/projects/{project_id}/file_reviews/{review_id}",
                headers=headers, verify=self.verify_ssl,
            )
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to delete P4 DAM file review: %s", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Workflows (read-only)
    # ------------------------------------------------------------------

    async def list_workflows(
        self,
        include: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """GET /api/workflows - List workflows."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            params: Dict[str, Any] = {"limit": limit, "offset": offset}
            if include:
                params["include"] = ",".join(include)
            r = requests.get(f"{base}/api/workflows", headers=headers,
                             params=params, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to list P4 DAM workflows: %s", e)
            return {"status": "error", "message": str(e)}

    async def get_workflow(
        self,
        workflow_id: str,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """GET /api/workflows/:uuid - Get a single workflow."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            params: Dict[str, Any] = {}
            if include:
                params["include"] = ",".join(include)
            r = requests.get(f"{base}/api/workflows/{workflow_id}", headers=headers,
                             params=params, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to get P4 DAM workflow: %s", e)
            return {"status": "error", "message": str(e)}

    async def list_workflow_states(
        self,
        workflow_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """GET /api/workflows/:workflow_id/states - List states for a workflow."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            params: Dict[str, Any] = {"limit": limit, "offset": offset}
            r = requests.get(f"{base}/api/workflows/{workflow_id}/states", headers=headers,
                             params=params, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to list P4 DAM workflow states: %s", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Asset Tag Management
    # ------------------------------------------------------------------

    async def list_custom_attribute_templates(
        self,
        project_id: str,
    ) -> Dict[str, Any]:
        """GET /api/projects/:project_id/file_attribute_templates - List attribute templates for a project."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            r = requests.get(
                f"{base}/api/projects/{project_id}/file_attribute_templates",
                headers=headers, verify=self.verify_ssl,
            )
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to list P4 DAM custom attribute templates: %s", e)
            return {"status": "error", "message": str(e)}

    async def update_asset_custom_attributes(
        self,
        paths: List[Dict[str, Any]],
        create: Optional[List[Dict[str, Any]]] = None,
        delete: Optional[List[Dict[str, str]]] = None,
        propagatable: bool = False,
    ) -> Dict[str, Any]:
        """PUT /api/p4/batch/custom_file_attributes - Set/remove custom attribute values on assets."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            body: Dict[str, Any] = {
                "paths": paths,
                "propagatable": propagatable,
            }
            if create:
                body["create"] = create
            if delete:
                body["delete"] = delete
            r = requests.put(
                f"{base}/api/p4/batch/custom_file_attributes",
                headers=headers, json=body, verify=self.verify_ssl,
            )
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to update P4 DAM asset custom attributes: %s", e)
            return {"status": "error", "message": str(e)}

    async def regenerate_preview(
        self,
        depot_path: str,
        commit_id: str,
    ) -> Dict[str, Any]:
        """PUT /api/p4/commits/:id/regenerate_preview - Trigger P4Search to regenerate thumbnail and preview."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            r = requests.put(
                f"{base}/api/p4/commits/{commit_id}/regenerate_preview",
                headers=headers,
                json={"depot_path": depot_path},
                verify=self.verify_ssl,
            )
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to regenerate P4 DAM preview: %s", e)
            return {"status": "error", "message": str(e)}

    async def update_asset_tags(
        self,
        paths: List[Dict[str, Any]],
        create: Optional[List[str]] = None,
        delete: Optional[List[str]] = None,
        delete_auto: Optional[List[str]] = None,
        propagatable: bool = False,
        identifier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """PUT /api/p4/batch/tags - Add/remove user tags and auto-tags on one or more assets."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            body: Dict[str, Any] = {
                "paths": paths,
                "propagatable": propagatable,
            }
            if create:
                body["create"] = create
            if delete:
                body["delete"] = delete
            if delete_auto:
                body["delete_auto"] = delete_auto
            if identifier is not None:
                body["identifier"] = identifier
            r = requests.put(f"{base}/api/p4/batch/tags", headers=headers,
                             json=body, verify=self.verify_ssl)
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to update P4 DAM asset tags: %s", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    async def create_comment(
        self,
        type: str,
        content: str,
        project: Optional[str] = None,
        repository: Optional[str] = None,
        file_review: Optional[str] = None,
        commit: Optional[str] = None,
        path: Optional[str] = None,
        stream_path: Optional[str] = None,
        helix_classic_branch: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/comments — create a comment of the given type."""
        try:
            headers = self._get_headers()
            base = await self._get_api_base()
            body: Dict[str, Any] = {
                "type": type,
                "content": content,
            }
            if project is not None:
                body["project"] = project
            if repository is not None:
                body["repository"] = repository
            if file_review is not None:
                body["file_review"] = file_review
            if commit is not None:
                body["commit"] = commit
            if path is not None:
                body["path"] = path
            if stream_path is not None:
                body["stream_path"] = stream_path
            if helix_classic_branch is not None:
                body["helix_classic_branch"] = helix_classic_branch
            if comment is not None:
                body["comment"] = comment
            r = requests.post(
                f"{base}/api/comments",
                headers=headers,
                json={"comment": body},
                verify=self.verify_ssl,
            )
            return {"status": "success", "message": self._handle_response(r)}
        except Exception as e:
            logger.error("Failed to create P4 DAM comment: %s", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Media fetch (thumbnail, preview, file)
    # ------------------------------------------------------------------

    async def fetch_media(self, url: str) -> Dict[str, Any]:
        """GET any P4 DAM media URL (thumbnail_url, preview_url, file_url) and return base64 content."""
        import base64
        try:
            base = await self._get_api_base()
            parsed = urlsplit(url)
            parsed_base = urlsplit(base)
            if parsed.scheme != parsed_base.scheme or parsed.netloc != parsed_base.netloc:
                raise ValueError(
                    f"URL host does not match the configured P4 DAM host ({parsed_base.netloc}). "
                    "Only URLs returned by P4 DAM tools may be fetched."
                )
            headers = self._get_headers()
            r = requests.get(url, headers=headers, verify=self.verify_ssl)
            if not r.ok:
                raise Exception(f"HTTP {r.status_code}: {r.text[:200]}")
            mime = r.headers.get("Content-Type", "application/octet-stream").split(";")[0].strip()
            if mime == "image/jpg":
                mime = "image/jpeg"
            return {"status": "success", "message": {
                "data_b64": base64.b64encode(r.content).decode(),
                "mime_type": mime,
                "size": len(r.content),
            }}
        except Exception as e:
            logger.error("Failed to fetch P4 DAM media: %s", e)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Asset Bundle Sync
    # ------------------------------------------------------------------

    async def sync_asset_bundle(
        self,
        view_paths: List[str],
    ) -> Dict[str, Any]:
        """Run p4 sync scoped to view_paths using the active P4 client workspace."""
        try:
            async with self.connection_manager.get_connection() as p4:
                for i, path in enumerate(view_paths):
                    p4.set_var(f"limitMap{i}", path)
                try:
                    result = p4.run("sync", "//...")
                finally:
                    for i in range(len(view_paths)):
                        p4.set_var(f"limitMap{i}", "")
                return {
                    "status": "success",
                    "message": {"client": p4.client, "result": result},
                }
        except Exception as e:
            logger.error("Failed to sync P4 DAM asset bundle: %s", e)
            return {"status": "error", "message": str(e)}
