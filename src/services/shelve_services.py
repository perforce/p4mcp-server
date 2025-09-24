"""
P4 shelve services layer

Read service for tools:
- list_shelves : List shelved changelists
- get_shelve_diff : Get shelve diff
- get_shelve_files : Get shelved files

Write service for tools:
- shelve_files : Shelve files
- unshelve_files : Unshelve files
- delete_shelve : Delete shelve
- update_shelve : Update shelve
- unshelve_to_changelist : Unshelve to changelist

"""

import logging
from typing import List, Dict, Any, Optional
from P4 import P4Exception

from ..core.connection import P4ConnectionManager

logger = logging.getLogger(__name__)

class ShelveServices:
    """Shelve services for shelve operations"""
    
    def __init__(self, connection_manager: P4ConnectionManager):
        self.connection_manager = connection_manager

    async def list_shelves(self, user: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List shelved changelists"""
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["changes", "-s", "shelved", f"-m{limit}"]
                if user:
                    args.append("-u")
                    args.append(user)
                shelves = p4.run(*args)
                return {"status": "success", "message": [{k: v for k, v in shelf.items()} for shelf in shelves]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to list shelves: {e}")
                return {"status": "error", "message": str(e)}

    async def get_shelve_diff(self, changelist_id: str) -> str:
        """Get diff of a shelved changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                current_tag = p4.tagged
                p4.tagged = False
                diff = p4.run("describe", "-a", "-S", "-dw", changelist_id)
                return {"status": "success", "message": diff}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get shelve diff for changelist '{changelist_id}': {e}")
                return {"status": "error", "message": str(e)}
            finally:
                p4.tagged = current_tag

    async def get_shelve_files(self, changelist_id: str) -> List[Dict[str, Any]]:
        """Get files in a shelved changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                current_tag = p4.tagged
                p4.tagged = True
                files = p4.run_describe( "-S", changelist_id)
                return {"status": "success", "message": [{k: v for k, v in file.items()} for file in files]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get shelved files for changelist '{changelist_id}': {e}")
                return {"status": "error", "message": str(e)}
            finally:
                p4.tagged = current_tag

    async def shelve_files(self, changelist_id: str, files: List[str], force: bool = False) -> Dict[str, Any]:
        """Shelve files in a changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if force:
                    shelved = p4.run("shelve", "-f", "-c", changelist_id, *files)
                else:
                    shelved = p4.run("shelve", "-c", changelist_id, *files)
                return {"status": "success", "message": shelved}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to shelve files in changelist '{changelist_id}': {e}")
                return {"status": "error", "message": str(e)}

    async def unshelve_files(self, changelist_id: str, files: List[str], force: bool = False) -> Dict[str, Any]:
        """Unshelve files from a shelved changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if force:
                    unshelved = p4.run("unshelve", "-f", "-s", changelist_id, *files)
                else:
                    unshelved = p4.run("unshelve", "-s", changelist_id, *files)
                return {"status": "success", "message": unshelved}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to unshelve files from changelist '{changelist_id}': {e}")
                return {"status": "error", "message": str(e)}

    async def delete_shelve(self, changelist_id: str, files: List[str]) -> None:
        """Delete a shelved changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["shelve", "-d", "-c", changelist_id]
                if files:
                    args.extend(files)
                result = p4.run(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to delete shelve '{changelist_id}': {e}")
                return {"status": "error", "message": str(e)}

    async def update_shelve(self, changelist_id: str, files: List[str], force: bool = False) -> Dict[str, Any]:
        """Update a shelved changelist with new files"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if force:
                    updated = p4.run("shelve", "-f", "-c", changelist_id, *files)
                else:
                    updated = p4.run("shelve", "-c", changelist_id, *files)
                return {"status": "success", "message": updated}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to update shelve '{changelist_id}': {e}")
                return {"status": "error", "message": str(e)}

    async def unshelve_to_changelist(self, changelist_id: str, target_changelist: str) -> Dict[str, Any]:
        """Unshelve files to a specific changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if target_changelist == "default":
                    unshelved = p4.run("unshelve", "-s", changelist_id)
                else:
                    unshelved = p4.run("unshelve", "-s", changelist_id, "-c", target_changelist)
                return {"status": "success", "message": unshelved}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to unshelve files from changelist '{changelist_id}' to '{target_changelist}': {e}")
                return {"status": "error", "message": str(e)}