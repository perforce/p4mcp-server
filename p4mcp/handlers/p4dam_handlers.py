import logging

from .utils import handle_errors

logger = logging.getLogger(__name__)


class P4DamHandlers:
    """Handler layer for P4 DAM tools — delegates to P4DamServices and shapes responses."""

    def __init__(self, p4dam_services):
        self.p4dam_services = p4dam_services

    @handle_errors
    async def _handle_query_p4dam_media(self, params):
        result = await self.p4dam_services.fetch_media(url=params.url)
        return {
            "status": result["status"],
            "action": "fetch_media",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_query_p4dam_assets(self, params):
        result = await self.p4dam_services.search_assets(
            search_term=params.search_term,
            project_ids=params.project_ids,
            repository_ids=params.repository_ids,
            path=params.path,
            name=params.name,
            tag=params.tag,
            file_extension=params.file_extension,
            exclude_file_extension=params.exclude_file_extension,
            user=params.user,
            from_size=params.from_size,
            to_size=params.to_size,
            from_date=params.from_date,
            to_date=params.to_date,
            all_revisions=params.all_revisions,
            limit=params.max_results,
            offset=params.offset,
        )
        return {
            "status": result["status"],
            "action": "search_assets",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_query_p4dam_asset(self, params):
        result = await self.p4dam_services.get_asset(
            depot_path=params.depot_path,
            path=params.path,
            stream_path=params.stream_path,
            identifier=params.identifier,
            project_id=params.project_id,
            repository_id=params.repository_id,
            include=params.include,
        )
        return {
            "status": result["status"],
            "action": "get_asset",
            "message": result["message"],
        }

    # ------------------------------------------------------------------
    # Navigation — projects, repositories, helix classic branches
    # ------------------------------------------------------------------

    @handle_errors
    async def _handle_query_p4dam_projects(self, params):
        result = await self.p4dam_services.list_projects(
            search_term=params.search_term,
            limit=params.limit,
            offset=params.offset,
        )
        return {
            "status": result["status"],
            "action": "list_projects",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_query_p4dam_repositories(self, params):
        result = await self.p4dam_services.list_repositories(
            project_id=params.project_id,
            search_term=params.search_term,
            limit=params.limit,
            offset=params.offset,
        )
        return {
            "status": result["status"],
            "action": "list_repositories",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_query_p4dam_helix_classic_branches(self, params):
        result = await self.p4dam_services.list_helix_classic_branches(
            project_id=params.project_id,
            repository_id=params.repository_id,
            limit=params.limit,
            offset=params.offset,
        )
        return {
            "status": result["status"],
            "action": "list_helix_classic_branches",
            "message": result["message"],
        }

    # ------------------------------------------------------------------
    # Asset bundle CRUD
    # ------------------------------------------------------------------

    @handle_errors
    async def _handle_modify_create_p4dam_asset_bundle(self, params):
        result = await self.p4dam_services.create_asset_bundle(
            depot_path=params.depot_path,
            project=params.project,
            repository=params.repository,
            view_paths=params.view_paths,
            stream_path=params.stream_path,
            helix_classic_branch=params.helix_classic_branch,
            description=params.description,
            hero_file_path=params.hero_file_path,
        )
        return {
            "status": result["status"],
            "action": "create_asset_bundle",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_modify_update_p4dam_asset_bundle(self, params):
        result = await self.p4dam_services.update_asset_bundle(
            bundle_id=params.bundle_id,
            description=params.description,
            view_paths=params.view_paths,
            hero_file_path=params.hero_file_path,
        )
        return {
            "status": result["status"],
            "action": "update_asset_bundle",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_modify_delete_p4dam_asset_bundle(self, params):
        result = await self.p4dam_services.delete_asset_bundle(
            bundle_id=params.bundle_id,
        )
        return {
            "status": result["status"],
            "action": "delete_asset_bundle",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_modify_sync_p4dam_asset_bundle(self, params):
        result = await self.p4dam_services.sync_asset_bundle(
            view_paths=params.view_paths,
        )
        return {
            "status": result["status"],
            "action": "sync_asset_bundle",
            "message": result["message"],
        }

    # ------------------------------------------------------------------
    # File review CRUD
    # ------------------------------------------------------------------

    @handle_errors
    async def _handle_query_p4dam_file_reviews(self, params):
        result = await self.p4dam_services.list_file_reviews(
            project_id=params.project_id,
            depot_path=params.depot_path,
            include=params.include,
            limit=params.limit,
            offset=params.offset,
        )
        return {
            "status": result["status"],
            "action": "list_file_reviews",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_query_p4dam_file_review(self, params):
        result = await self.p4dam_services.get_file_review(
            project_id=params.project_id,
            review_id=params.review_id,
        )
        return {
            "status": result["status"],
            "action": "get_file_review",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_modify_create_p4dam_file_review(self, params):
        result = await self.p4dam_services.create_file_review(
            project_id=params.project_id,
            name=params.name,
            depot_path=params.depot_path,
            view_paths=params.view_paths,
            state=params.state,
            repository=params.repository,
            helix_classic_branch=params.helix_classic_branch,
            asset_bundle=params.asset_bundle,
            hero_file_path=params.hero_file_path,
            description=params.description,
            position=params.position,
            base_commit_id=params.base_commit_id,
            head_commit_id=params.head_commit_id,
        )
        return {
            "status": result["status"],
            "action": "create_file_review",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_modify_update_p4dam_file_review(self, params):
        result = await self.p4dam_services.update_file_review(
            project_id=params.project_id,
            review_id=params.review_id,
            state=params.state,
            name=params.name,
            view_paths=params.view_paths,
            hero_file_path=params.hero_file_path,
            description=params.description,
            position=params.position,
        )
        return {
            "status": result["status"],
            "action": "update_file_review",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_modify_delete_p4dam_file_review(self, params):
        result = await self.p4dam_services.delete_file_review(
            project_id=params.project_id,
            review_id=params.review_id,
        )
        return {
            "status": result["status"],
            "action": "delete_file_review",
            "message": result["message"],
        }

    # ------------------------------------------------------------------
    # Workflows (read-only)
    # ------------------------------------------------------------------

    @handle_errors
    async def _handle_query_p4dam_workflows(self, params):
        result = await self.p4dam_services.list_workflows(
            include=params.include,
            limit=params.limit,
            offset=params.offset,
        )
        return {
            "status": result["status"],
            "action": "list_workflows",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_query_p4dam_workflow(self, params):
        result = await self.p4dam_services.get_workflow(
            workflow_id=params.workflow_id,
            include=params.include,
        )
        return {
            "status": result["status"],
            "action": "get_workflow",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_query_p4dam_workflow_states(self, params):
        result = await self.p4dam_services.list_workflow_states(
            workflow_id=params.workflow_id,
            limit=params.limit,
            offset=params.offset,
        )
        return {
            "status": result["status"],
            "action": "list_workflow_states",
            "message": result["message"],
        }

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    @handle_errors
    async def _handle_modify_create_p4dam_comment(self, params):
        result = await self.p4dam_services.create_comment(
            type=params.type,
            content=params.content,
            project=params.project,
            repository=params.repository,
            file_review=params.file_review,
            commit=params.commit,
            path=params.path,
            stream_path=params.stream_path,
            helix_classic_branch=params.helix_classic_branch,
            comment=params.comment,
        )
        return {
            "status": result["status"],
            "action": "create_comment",
            "message": result["message"],
        }

    # ------------------------------------------------------------------
    # Preview regeneration
    # ------------------------------------------------------------------

    @handle_errors
    async def _handle_modify_regenerate_p4dam_preview(self, params):
        result = await self.p4dam_services.regenerate_preview(
            depot_path=params.depot_path,
            commit_id=params.commit_id,
        )
        return {
            "status": result["status"],
            "action": "regenerate_preview",
            "message": result["message"],
        }

    # ------------------------------------------------------------------
    # Custom attribute templates
    # ------------------------------------------------------------------

    @handle_errors
    async def _handle_query_p4dam_custom_attribute_templates(self, params):
        result = await self.p4dam_services.list_custom_attribute_templates(
            project_id=params.project_id,
        )
        return {
            "status": result["status"],
            "action": "list_custom_attribute_templates",
            "message": result["message"],
        }

    @handle_errors
    async def _handle_modify_update_p4dam_asset_custom_attributes(self, params):
        result = await self.p4dam_services.update_asset_custom_attributes(
            paths=[p.model_dump(exclude_none=True) for p in params.paths],
            create=[{"uuid": c.uuid, "value": c.value} for c in params.create] if params.create else None,
            delete=[{"uuid": u} for u in params.delete] if params.delete else None,
            propagatable=params.propagatable,
        )
        return {
            "status": result["status"],
            "action": "update_asset_custom_attributes",
            "message": result["message"],
        }

    # ------------------------------------------------------------------
    # Asset tag management
    # ------------------------------------------------------------------

    @handle_errors
    async def _handle_modify_update_p4dam_asset_tags(self, params):
        result = await self.p4dam_services.update_asset_tags(
            paths=[p.model_dump(exclude_none=True) for p in params.paths],
            create=params.create,
            delete=params.delete,
            delete_auto=params.delete_auto,
            propagatable=params.propagatable,
            identifier=params.identifier,
        )
        return {
            "status": result["status"],
            "action": "update_asset_tags",
            "message": result["message"],
        }
