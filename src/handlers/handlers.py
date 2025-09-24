import logging

logger = logging.getLogger(__name__)

def handle_errors(func):
    async def wrapper(self, params):
        try:
            return await func(self, params)
        except Exception as e:
            action = getattr(params, "action", None)
            resp = {"status": "error", "message": str(e)}
            if action is not None:
                resp["action"] = action
            return resp
    return wrapper

class Handlers:
    """Main handler class to process various operations with dispatch"""

    def __init__(self, server_services, workspace_services, file_services, changelist_services, shelve_services, job_services):
        self.server_services = server_services
        self.workspace_services = workspace_services
        self.file_services = file_services
        self.changelist_services = changelist_services
        self.shelve_services = shelve_services
        self.job_services = job_services

        # Dispatch table: (operation, sub-operation) -> handler
        self.dispatch = {
            ("query", "server"): self._handle_query_server,
            ("query", "workspaces"): self._handle_query_workspaces,
            ("query", "files"): self._handle_query_files,
            ("query", "changelists"): self._handle_query_changelists,
            ("query", "shelves"): self._handle_query_shelves,
            ("query", "jobs"): self._handle_query_jobs,
            ("modify", "workspaces"): self._handle_modify_workspaces,
            ("modify", "files"): self._handle_modify_files,
            ("modify", "changelists"): self._handle_modify_changelists,
            ("modify", "shelves"): self._handle_modify_shelves,
            ("modify", "jobs"): self._handle_modify_jobs,
        }

    async def handle(self, operation, sub_operation, params):
        handler = self.dispatch.get((operation, sub_operation))
        if not handler:
            logger.error(f"Unknown operation: {operation}/{sub_operation}")
            return {"status": "error", "message": f"Unknown operation: {operation}/{sub_operation}"}
        return await handler(params)

    @handle_errors
    async def _handle_query_server(self, params):
        if params.action == "server_info":
            result = await self.server_services.get_server_info()
        elif params.action == "current_user":
            result = await self.server_services.get_current_user()
        else:
            logger.error(f"Unknown server query action: {params.action}")
            raise ValueError(f"Unknown server query action: {params.action}")
        return {"status": "success", "action": params.action, "data": result}

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
    async def _handle_query_files(self, params):
        if params.action == "content":
            result = await self.file_services.get_file_content(params.file_path)
        elif params.action == "history":
            result = await self.file_services.get_file_history(params.file_path, params.max_results)
        elif params.action == "info":
            result = await self.file_services.get_file_info(params.file_path)
        elif params.action == "metadata":
            result = await self.file_services.get_file_metadata(params.file_path)
        elif params.action == "diff":
            result = await self.file_services.diff_files(params.file_path, params.file2, params.diff2)
        elif params.action == "annotations":
            result = await self.file_services.get_file_annotations(params.file_path)
        else:
            logger.error(f"Unknown file query action: {params.action}")
            raise ValueError(f"Unknown file query action: {params.action}")
        return {"status": result["status"], "action": params.action, "data": result}

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
    async def _handle_query_jobs(self, params):
        if not params.changelist_id and params.action == "list_jobs":
            logger.error(f"changelist_id is required for this {params.action} action")
            raise ValueError(f"changelist_id is required for this {params.action} action")
        if not params.job_id and params.action == "get_job":
            logger.error(f"job_id is required for this {params.action} action")
            raise ValueError(f"job_id is required for this {params.action} action")

        if params.action == "list_jobs":
            result = await self.job_services.list_jobs_from_changelist(params.changelist_id, params.max_results)
        elif params.action == "get_job":
            result = await self.job_services.get_job_details(params.job_id)
        else:
            logger.error(f"Unknown job query action: {params.action}")
            raise ValueError(f"Unknown job query action: {params.action}")
        return {"status": result["status"], "action": params.action, "message": result["message"]}

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

    @handle_errors
    async def _handle_modify_files(self, params):
        if not params.file_paths and params.action in ["add", "edit", "delete", "revert", "sync"]:
            logger.error(f"file_paths are required for this {params.action} action")
            raise ValueError(f"file_paths are required for this {params.action} action")


        if params.action == "add":
            result = await self.file_services.add_files(params.file_paths, params.changelist)
        elif params.action == "edit":
            result = await self.file_services.edit_files(params.file_paths, params.changelist)
        elif params.action == "move":
            if not params.source_paths or not params.target_paths:
                raise ValueError("source_paths and target_paths required for move action")
            result = await self.file_services.move_files(params.source_paths, params.target_paths, params.changelist)
        elif params.action == "delete":
            result = await self.file_services.delete_files(params.file_paths, params.changelist)
        elif params.action == "revert":
            result = await self.file_services.revert_files(params.file_paths, params.changelist)
        elif params.action == "reconcile":
            result = await self.file_services.reconcile_files(params.file_paths or [], params.changelist)
        elif params.action == "resolve":
            result = await self.file_services.resolve_files(params.file_paths or [], params.changelist, params.mode)
        elif params.action == "sync":
            result = await self.file_services.sync_files(params.file_paths, params.force)
        else:
            raise ValueError(f"Unknown file modify action: {params.action}")
        return {"status": result["status"], "action": params.action, "message": result["message"]}

    @handle_errors
    async def _handle_modify_changelists(self, params):
        if not params.changelist_id and params.action in ["update", "submit", "delete", "move_files", "link_job", "unlink_job"]:
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
    
    @handle_errors
    async def _handle_modify_jobs(self, params):
        if not params.changelist_id and not params.job_id and params.action in ["link_job", "unlink_job"]:
            logger.error(f"changelist_id and job_id are required for this {params.action} action")
            raise ValueError(f"changelist_id and job_id are required for this {params.action} action")
        if params.action == "link_job":
            result = await self.job_services.link_job_to_changelist(params.changelist_id, params.job_id)
        elif params.action == "unlink_job":
            result = await self.job_services.unlink_job_from_changelist(params.changelist_id, params.job_id)
        else:
            logger.error(f"Unknown job modify action: {params.action}")
            raise ValueError(f"Unknown job modify action: {params.action}")
        return {"status": result["status"], "action": params.action, "message": result["message"]}