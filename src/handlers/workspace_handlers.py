"""Workspace query and modify handlers."""

import logging
from .utils import handle_errors

logger = logging.getLogger(__name__)


class WorkspacesHandlers:

    def __init__(self, workspace_services):
        self.workspace_services = workspace_services

    @handle_errors
    async def _handle_query_workspaces(self, params):

        if not params.workspace_name and params.action in ["get", "type", "status"]:
            logger.error(f"workspace name is required for this {params.action} action")
            raise ValueError(f"workspace_name is required for this {params.action} action")

        if params.action == "get":
            result = await self.workspace_services.get_workspace(params.workspace_name)
        elif params.action == "list":
            result = await self.workspace_services.list_workspaces(params.user, params.max_results)
        elif params.action == "type":
            result = await self.workspace_services.get_workspace_type(params.workspace_name)
        elif params.action == "status":
            result = await self.workspace_services.get_workspace_status(params.workspace_name)
        else:
            logger.error(f"Unknown workspace query action: {params.action}")
            raise ValueError(f"Unknown workspace query action: {params.action}")
        return {"status": "success", "action": params.action, "data": result}

    @handle_errors
    async def _handle_modify_workspaces(self, params):
        if not params.name and params.action in ["delete", "update", "switch"]:
            logger.error(f"name is required for this {params.action} action")
            raise ValueError(f"name is required for this {params.action} action")
        
        if not params.specs and params.action in ["create", "update"]:
            logger.error(f"specs are required for this {params.action} action")
            raise ValueError(f"specs are required for this {params.action} action")

        if params.action == "create":
            result = await self.workspace_services.create_workspace({k: v for k, v in params.specs.model_dump().items() if v is not None})
        elif params.action == "delete":
            result = await self.workspace_services.delete_workspace(params.name)
        elif params.action == "update":
            result = await self.workspace_services.update_workspace(params.name, {k: v for k, v in params.specs.model_dump().items() if v is not None})
        elif params.action == "switch":
            result = await self.workspace_services.switch_workspace(params.name)
        else:
            raise ValueError(f"Invalid action '{params.action}' for modify_workspaces")
        return {"status": result["status"], "action": params.action, "message": result["message"]}
