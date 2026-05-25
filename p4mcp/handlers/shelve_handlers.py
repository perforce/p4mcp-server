"""Shelve query and modify handlers."""

import logging
from .utils import handle_errors

logger = logging.getLogger(__name__)


class ShelvesHandlers:

    def __init__(self, shelve_services):
        self.shelve_services = shelve_services

    @handle_errors
    async def _handle_query_shelves(self, params):
        if not params.changelist_id and params.action in ["diff", "files"]:
            logger.error(f"changelist_id is required for this {params.action} action")
            raise ValueError(f"changelist_id is required for this {params.action} action")
        if params.action == "list":
            result = await self.shelve_services.list_shelves(params.user, params.max_results)
        elif params.action == "diff":
            result = await self.shelve_services.get_shelve_diff(params.changelist_id)
        elif params.action == "files":
            result = await self.shelve_services.get_shelve_files(params.changelist_id)
        else:
            raise ValueError(f"Unknown shelve query action: {params.action}")
        return {"status": result["status"], "action": params.action, "message": result["message"]}

    @handle_errors
    async def _handle_modify_shelves(self, params):
        if not params.changelist_id:
            logger.error(f"changelist_id is required for {params.action} action")
            raise ValueError("changelist_id required for delete action")
        if params.action == "shelve":
            if not params.file_paths:
                logger.error("file_paths are required for shelve action")
                raise ValueError("file_paths required for shelve action")
            result = await self.shelve_services.shelve_files(params.changelist_id, params.file_paths, params.force)
        elif params.action == "unshelve":
            result = await self.shelve_services.unshelve_files(params.changelist_id, params.file_paths, params.force)
        elif params.action == "update":
            result = await self.shelve_services.update_shelve(params.changelist_id, params.file_paths, params.force)
        elif params.action == "delete":
            result = await self.shelve_services.delete_shelve(params.changelist_id, params.file_paths)
        elif params.action == "unshelve_to_changelist":
            result = await self.shelve_services.unshelve_to_changelist(params.changelist_id, params.target_changelist)
        else:
            logger.error(f"Unknown shelve modify action: {params.action}")
            raise ValueError(f"Unknown shelve modify action: {params.action}")
        return {"status": result["status"], "action": params.action, "message": result["message"]}
