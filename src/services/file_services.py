"""
P4 file services layer

Read service for tools:
- get_file_content : Get file content
- get_file_history : Get file history
- get_file_info : Get file information
- get_file_metadata : Get file metadata
- diff_files : Diff files
- get_file_annotations : Get file annotations

Write service for tools:
- sync_files : Sync files from depot
- add_files : Add files to depot
- edit_files : Open files for edit
- delete_files : Mark files for delete
- move_files : Move/rename files
- revert_files : Revert file changes
- reconcile_files : Reconcile workspace
- resolve_files : Resolve file conflicts

"""

import logging
from typing import List, Dict, Any
from P4 import P4Exception

from ..core.connection import P4ConnectionManager

logger = logging.getLogger(__name__)

RESOLVE_MODE_FLAGS = {
    "auto": "-am",
    "safe": "-as",
    "force": "-af",
    "preview": "-n",
    "theirs": "-at",
    "yours": "-ay",
}

class FileServices:
    """File services for file operations"""
    
    def __init__(self, connection_manager: P4ConnectionManager):
        self.connection_manager = connection_manager

    async def get_file_content(self, file_path: str) -> str:
        """Get content of a file in the depot"""
        async with self.connection_manager.get_connection() as p4:
            try:
                content = p4.run("print", file_path)
                return {"status": "success", "message": content}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get file content '{file_path}': {e}")
                return {"status": "error", "message": str(e)}

    async def get_file_history(self, file_path: str, limit: int=100) -> List[Dict[str, Any]]:
        """Get history of a file in the depot"""
        async with self.connection_manager.get_connection() as p4:
            try:
                history = p4.run("filelog", f"-m{limit}", file_path)
                return {"status": "success", "message": [entry for entry in history if isinstance(entry, dict)]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get file history '{file_path}': {e}")
                return {"status": "error", "message": str(e)}

    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file in the depot"""
        async with self.connection_manager.get_connection() as p4:
            try:
                file_info = p4.run("fstat", file_path)
                if not file_info:
                    raise ValueError(f"File '{file_path}' not found")
                return {"status": "success", "message": file_info}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get file info '{file_path}': {e}")
                return {"status": "error", "message": str(e)}

    async def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata about a file in the depot"""
        async with self.connection_manager.get_connection() as p4:
            try:
                file_metadata = p4.run("fstat", "-Oal", file_path)
                if not file_metadata:
                    raise ValueError(f"File '{file_path}' not found")
                return {"status": "success", "message": file_metadata}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get file metadata '{file_path}': {e}")
                return {"status": "error", "message": str(e)}

    async def diff_files(self, file1: str, file2: str, diff2: bool) -> dict:
        """Diff two files in the depot or between depot and local"""
        async with self.connection_manager.get_connection() as p4:
            try:
                p4.tagged = False
                if diff2:
                    diff_result = p4.run("diff2", file1, file2)
                else:
                    # If diff2 is False, one of the files is local
                    diff_result = p4.run("diff", file1, file2)
                p4.tagged = True
                return {"status": "success", "message": diff_result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to diff files '{file1}' and '{file2}': {e}")
                return {"status": "error", "message": str(e)}

    async def get_file_annotations(self, file_path: str) -> List[Dict[str, Any]]:
        """Get annotations for a file in the depot"""
        async with self.connection_manager.get_connection() as p4:
            try:
                annotations = p4.run("annotate", file_path)
                return {"status": "success", "message": [entry for entry in annotations if isinstance(entry, dict)]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get file annotation '{file_path}': {e}")
                return {"status": "error", "message": str(e)}

    async def sync_files(self, file_paths: List[str], force: bool = False) -> Dict[str, Any]:
        """Sync files from depot"""
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["sync"]
                if force:
                    args.append("-f")
                args.extend(file_paths)
                result = p4.run(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                if "File(s) up-to-date" in str(e):
                    return {"status": "success", "message": "Workspace is already up-to-date"}
                else:
                    logger.error(f"P4Error: Failed to sync files: {e}")
                    return {"status": "error", "message": str(e)}

    async def add_files(self, file_paths: List[str], changelist: str) -> Dict[str, Any]:
        """Add files to depot"""
        async with self.connection_manager.get_connection() as p4:
            try:
                result = p4.run("add", "-c", changelist, *file_paths )
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to add files to changelist '{changelist}': {e}")
                return {"status": "error", "message": str(e)}

    async def edit_files(self, file_paths: List[str], changelist: str) -> Dict[str, Any]:
        """Open files for edit"""
        async with self.connection_manager.get_connection() as p4:
            try:
                result = p4.run("edit", "-c", changelist, *file_paths)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to edit files in changelist '{changelist}': {e}")
                return {"status": "error", "message": str(e)}

    async def delete_files(self, file_paths: List[str], changelist: str) -> Dict[str, Any]:
        """Mark files for delete"""
        async with self.connection_manager.get_connection() as p4:
            try:
                result = p4.run("delete", "-c", changelist, *file_paths)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to delete files in changelist '{changelist}': {e}")
                return {"status": "error", "message": str(e)}

    async def move_files(self, source_paths: List[str], target_paths: List[str], changelist: str) -> Dict[str, Any]:
        """Move/rename files"""
        if len(source_paths) != len(target_paths):
            raise ValueError("Source and target paths must have the same length")
        
        async with self.connection_manager.get_connection() as p4:
            try:
                result = []
                for src, tgt in zip(source_paths, target_paths):
                    result.append(p4.run("move", "-c", changelist, src, tgt))
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to move files in changelist '{changelist}': {e}")
                return {"status": "error", "message": str(e)}

    async def revert_files(self, file_paths: List[str], changelist: str) -> Dict[str, Any]:
        """Revert file changes"""
        async with self.connection_manager.get_connection() as p4:
            try:
                result = p4.run("revert", "-c", changelist, *file_paths)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to revert files in changelist '{changelist}': {e}")
                return {"status": "error", "message": str(e)}

    async def reconcile_files(self, file_paths: List[str], changelist: str) -> Dict[str, Any]:
        """Reconcile workspace files"""
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["reconcile", "-c", changelist]
                if len(file_paths) > 0:
                    args.extend(file_paths)
                result = p4.run(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to reconcile files in changelist '{changelist}': {e}")
                return {"status": "error", "message": str(e)}

    async def resolve_files(self, file_paths: List[str], changelist: str, mode: str) -> Dict[str, Any]:
        """Resolve file conflicts"""
        async with self.connection_manager.get_connection() as p4:
            try:
                
                args = ["resolve"]
                if mode:
                    if mode in RESOLVE_MODE_FLAGS:
                        args.append(RESOLVE_MODE_FLAGS[mode])
                    else:
                        raise ValueError(f"Invalid resolve mode: {mode}")
                if changelist and changelist != "default":
                    args.extend(["-c", changelist])
                if len(file_paths) > 0:
                    args.extend(file_paths)
                result = p4.run(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to resolve files in changelist '{changelist}': {e}")
                return {"status": "error", "message": str(e)}

    