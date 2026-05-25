"""
P4 changelist services layer

Read service for tools:
- get_changelist : Get changelist details
- list_changelists : List changelists

Write service for tools:
- create_changelist : Create new changelist
- update_changelist : Update changelist
- submit_changelist : Submit changelist
- delete_changelist : Delete changelist
- move_files_to_changelist : Move files between changelists
"""

import logging
from typing import List, Dict, Any, Optional
from P4 import P4Exception

from ..core.connection import P4ConnectionManager

logger = logging.getLogger(__name__)

class ChangelistServices:
    """Changelist services for changelist operations"""
    
    def __init__(self, connection_manager: P4ConnectionManager):
        self.connection_manager = connection_manager

    async def get_changelist(self, changelist_id: str) -> Dict[str, Any]:
        """Get details of a specific changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if changelist_id and changelist_id == "default":
                    opened_files = p4.run("opened", "-c", "default")
                    return {"status": "success", "message": {"opened_files": opened_files}}
                changelist = p4.run("describe", changelist_id)
                if not changelist:
                    raise ValueError(f"Changelist '{changelist_id}' not found")
                return {"status": "success", "message": {k: v for k, v in changelist[0].items()}}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get changelist '{changelist_id}': {e}")
                return {"status": "error", "message": f"Failed to get changelist '{changelist_id}': {e}"}

    async def list_changelists(self, workspace_name: str, status: str, user: str, depot_path: str, limit: int=100) -> List[Dict[str, Any]]:
        """List recent changelists"""
        async with self.connection_manager.get_connection() as p4:
            try:
                # current_user = p4.run("info")[0]["userName"]
                args = ["changes", f"-m{limit}"]
                if status:
                    args.extend(["-s", status])
                if workspace_name:
                    args.extend(["-c", workspace_name])
                if user:
                    args.extend(["-u", user])
                if depot_path:
                    args.append(depot_path)
                changelists = p4.run(*args)
                return {"status": "success", "message": [{k: v for k, v in cl.items()} for cl in changelists if len(cl) > 0]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to list changelists: {e}")
                return {"status": "error", "message": str(e)}

    async def create_changelist(self, description: str) -> Dict[str, Any]:
        """Create a new changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                changelist = p4.fetch_change()
                changelist._description = description
                if 'Files' in changelist:
                    changelist._files = []
                result = p4.save_change(changelist)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to create changelist: {e}")
                return {"status": "error", "message": str(e)}

    async def update_changelist(self, changelist_id: str, description: str) -> List[str]:
        """Update an existing changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if not await self.verify_changelist(p4, changelist_id):
                    raise ValueError(f"Changelist '{changelist_id}' does not exist or is not valid for update")

                changelist = p4.fetch_change(changelist_id)
                changelist._description = description
                result = p4.save_change(changelist)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to update changelist '{changelist_id}': {e}")
                return {"status": "error", "message": f"Failed to update changelist '{changelist_id}': {e}"}
    
    async def submit_changelist(self, changelist_id: str) -> Dict[str, Any]:
        """Submit a changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if not await self.verify_changelist(p4, changelist_id):
                    raise ValueError(f"Changelist '{changelist_id}' does not exist or is not valid for submit")
                
                submit_result = p4.run_submit("-c", changelist_id)
                return {"status": "success", "message": {k: v for k, v in submit_result[0].items()}}

            except P4Exception as e:
                logger.error(f"P4Error: Failed to submit changelist '{changelist_id}': {e}")
                return {"status": "error", "message": str(e)}

    async def delete_changelist(self, changelist_id: str) -> List[str]:
        """Delete a changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if not await self.verify_changelist(p4,changelist_id):
                    raise ValueError(f"Changelist '{changelist_id}' does not exist or is not valid for delete")

                # Check for open files to ensure the changelist is empty before deletion
                open_files = p4.run("opened", "-c", changelist_id)
                if open_files:
                    raise ValueError(f"Cannot delete changelist '{changelist_id}': it contains open files")
                result = p4.run("change", "-d", changelist_id)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to delete changelist '{changelist_id}': {e}")
                return {"status": "error", "message": str(e)}

    async def move_files_to_changelist(self, changelist_id: str, files: List[str]) -> None:
        """Move files to a specific changelist"""
        async with self.connection_manager.get_connection() as p4:
            result = []
            try:
                if not await self.verify_changelist(p4, changelist_id):
                    raise ValueError(f"Changelist '{changelist_id}' does not exist or is not valid for move files")
                if not files or not isinstance(files, list):
                    raise ValueError("No files provided to move to changelist")
                for file in files:
                    result.append(p4.run("reopen", "-c", changelist_id, file))
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to move files to changelist '{changelist_id}': {e}")
                return {"status": "error", "message": str(e)}
            
    
    @staticmethod
    async def verify_changelist(p4, changelist_id: str) -> bool:
        """Verify if a changelist exists"""
        try:
            changelist = p4.run("describe", changelist_id)
            if not changelist:
                raise ValueError(f"Changelist '{changelist_id}' not found")
            changelist = changelist[0]
            if changelist['user'] != p4.run("info")[0]["userName"]:
                raise PermissionError(f"Cannot update changelist '{changelist_id}': not owned by current user")
            if changelist['status'] == 'submitted':
                raise ValueError(f"Cannot update submitted changelist '{changelist_id}'")
            return True
        except P4Exception as e:
            logger.error(f"P4Error: Failed to verify changelist '{changelist_id}': {e}")
            return False

    
