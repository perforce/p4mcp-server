"""File query and modify handlers."""

import logging
from .utils import handle_errors

logger = logging.getLogger(__name__)


class FilesHandlers:

    def __init__(self, file_services):
        self.file_services = file_services

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
