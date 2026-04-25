"""Changelist query and modify handlers."""

import logging
from .utils import handle_errors

logger = logging.getLogger(__name__)


class ChangelistsHandlers:

    def __init__(self, changelist_services):
        self.changelist_services = changelist_services

    @handle_errors
    async def _handle_query_changelists(self, params):
        if params.action == "get":
            if not params.changelist_id:
                logger.error("changelist_id is required for get action")
                raise ValueError("changelist_id required for get action")
            result = await self.changelist_services.get_changelist(params.changelist_id)
        elif params.action == "list":
            result = await self.changelist_services.list_changelists(params.workspace_name, params.status, params.user, params.depot_path, params.max_results)
        else:
            logger.error(f"Unknown changelist query action: {params.action}")
            raise ValueError(f"Unknown changelist query action: {params.action}")
        return {"status": result["status"], "action": params.action, "message": result["message"]}

    @handle_errors
    async def _handle_modify_changelists(self, params):
        if not params.changelist_id and params.action in ["update", "submit", "delete", "move_files"]:
            logger.error(f"changelist_id is required for this {params.action} action")
            raise ValueError(f"changelist_id is required for this {params.action} action")
        
        if not params.description and params.action in ["create", "update"]:
            logger.error(f"description is required for this {params.action} action")
            raise ValueError(f"description is required for this {params.action} action")

        if params.action == "create":
            result = await self.changelist_services.create_changelist(params.description)
        elif params.action == "update":
            result = await self.changelist_services.update_changelist(params.changelist_id, params.description)
        elif params.action == "submit":
            result = await self.changelist_services.submit_changelist(params.changelist_id)
        elif params.action == "delete":
            result = await self.changelist_services.delete_changelist(params.changelist_id)
        elif params.action == "move_files":
            if not params.file_paths:
                raise ValueError("file_paths required for move_files action")
            result = await self.changelist_services.move_files_to_changelist(params.changelist_id, params.file_paths)
        else:
            raise ValueError(f"Unknown changelist modify action: {params.action}")
        return {"status": result["status"], "action": params.action, "message": result}
