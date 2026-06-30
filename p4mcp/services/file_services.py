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
from typing import List, Dict, Any, Optional
from P4 import P4Exception

from ..core.connection import P4ConnectionManager, clamp_to_maxresults

logger = logging.getLogger(__name__)

RESOLVE_MODE_FLAGS = {
    "auto": "-am",
    "safe": "-as",
    "force": "-af",
    "preview": "-n",
    "theirs": "-at",
    "yours": "-ay",
}


def _join_print_result(result: List[Any]) -> Dict[str, Any]:
    metadata: List[Dict[str, Any]] = []
    fragments: List[str] = []
    for entry in result:
        if isinstance(entry, dict):
            metadata.append(entry)
            continue
        if isinstance(entry, (bytes, bytearray)):
            fragments.append(entry.decode("utf-8", errors="replace"))
        else:
            fragments.append(str(entry))
    return {"content": "".join(fragments), "metadata": metadata}


def _serialize_depot_file(depot_file: Any) -> Dict[str, Any]:
    revisions: List[Dict[str, Any]] = []

    for rev in getattr(depot_file, "revisions", None) or []:
        time_value = getattr(rev, "time", None)

        integrations: List[Dict[str, Any]] = []
        for integ in getattr(rev, "integrations", None) or []:
            integrations.append({
                "how": getattr(integ, "how", None),
                "file": getattr(integ, "depotFile", None),
                "srev": getattr(integ, "srev", None),
                "erev": getattr(integ, "erev", None),
            })

        revisions.append({
            "depotFile": getattr(depot_file, "depotFile", None),
            "rev": getattr(rev, "rev", None),
            "change": getattr(rev, "change", None),
            "action": getattr(rev, "action", None),
            "type": getattr(rev, "type", None),
            "time": str(time_value) if time_value is not None else None,
            "user": getattr(rev, "user", None),
            "client": getattr(rev, "client", None),
            "desc": getattr(rev, "desc", None),
            "digest": getattr(rev, "digest", None),
            "fileSize": getattr(rev, "fileSize", None),
            "integrations": integrations,
        })

    return {
        "depotFile": getattr(depot_file, "depotFile", None),
        "revisions": revisions,
    }

class FileServices:
    """File services for file operations"""
    
    def __init__(self, connection_manager: P4ConnectionManager):
        self.connection_manager = connection_manager

    async def get_file_content(self, file_path: str) -> str:
        """Get content of a file in the depot."""
        async with self.connection_manager.get_connection() as p4:
            try:
                result = p4.run_print(file_path)
                joined = _join_print_result(result)
                return {"status": "success", "message": joined["content"], "metadata": joined["metadata"]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get file content '{file_path}': {e}")
                return {"status": "error", "message": str(e), "metadata": []}

    async def get_file_history(self, file_path: str, limit: int=100) -> List[Dict[str, Any]]:
        """Get history of a file in the depot."""
        async with self.connection_manager.get_connection() as p4:
            try:
                history = p4.run_filelog(f"-m{limit}", file_path)
                return {"status": "success", "message": [_serialize_depot_file(entry) for entry in history]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get file history '{file_path}': {e}")
                return {"status": "error", "message": str(e)}

    async def get_file_info(self, file_path: str, max_results: Optional[int] = None) -> Dict[str, Any]:
        """Get information about a file in the depot

        Args:
            file_path: Depot or local file path to stat.
            max_results: Optional upper bound on returned file entries. When set,
                'p4 fstat -m N' is issued (N before the path). Must be >= 1.
        """
        if max_results is not None and max_results < 1:
            raise ValueError("max_results must be a positive integer")
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["fstat"]
                note = None
                if max_results is not None:
                    effective, note = clamp_to_maxresults(p4, max_results)
                    args.extend(["-m", str(effective)])
                args.append(file_path)
                file_info = p4.run(*args)
                if not file_info:
                    return {"status": "not_found", "message": f"File '{file_path}' not found"}
                response = {"status": "success", "message": file_info}
                if note:
                    response["note"] = note
                return response
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get file info '{file_path}': {e}")
                return {"status": "error", "message": str(e)}

    async def get_file_metadata(self, file_path: str, max_results: Optional[int] = None) -> Dict[str, Any]:
        """Get metadata about a file in the depot

        Args:
            file_path: Depot or local file path to stat.
            max_results: Optional upper bound on returned file entries. When set,
                'p4 fstat -Oal -m N' is issued (N before the path). Must be >= 1.
        """
        if max_results is not None and max_results < 1:
            raise ValueError("max_results must be a positive integer")
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["fstat", "-Oal"]
                note = None
                if max_results is not None:
                    effective, note = clamp_to_maxresults(p4, max_results)
                    args.extend(["-m", str(effective)])
                args.append(file_path)
                file_metadata = p4.run(*args)
                if not file_metadata:
                    return {"status": "not_found", "message": f"File '{file_path}' not found"}
                response = {"status": "success", "message": file_metadata}
                if note:
                    response["note"] = note
                return response
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

    async def search_files(self, depot_path: str, pattern: str, max_results: int) -> Dict[str, Any]:
        """Search for files by name pattern using p4 files"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if depot_path.endswith('...'):
                    base = depot_path[:-3]
                    search_patterns = [f"{base}{pattern}", f"{base}.../{pattern}"]
                elif depot_path.endswith('/'):
                    search_patterns = [f"{depot_path}{pattern}"]
                else:
                    search_patterns = [f"{depot_path}/{pattern}"]


                all_files = []
                for sp in search_patterns:
                    try:
                        result = p4.run("files", "-m", str(max_results), sp)
                        all_files.extend(entry for entry in result if isinstance(entry, dict))
                    except P4Exception as e:
                        if "no such file(s)" not in str(e).lower():
                            raise

                return {"status": "success", "message": all_files[:max_results]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to search files with pattern '{pattern}' in '{depot_path}': {e}")
                return {"status": "error", "message": str(e)}

    async def grep_files(self, depot_path: str, pattern: str, case_insensitive: bool, max_results: int) -> Dict[str, Any]:
        """Search for files by content pattern using p4 grep"""
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["grep", "-n"]
                if case_insensitive:
                    args.append("-i")
                args.extend(["-e", pattern, depot_path])

                saved_exception_level = p4.exception_level
                p4.exception_level = 0
                result = p4.run(*args)
                errors = list(p4.errors)
                p4.exception_level = saved_exception_level

                real_errors = [e for e in errors if "maximum line length" not in e]
                if real_errors:
                    raise P4Exception("\n".join(real_errors))

                matches = [entry for entry in result if isinstance(entry, dict)]

                if len(matches) > max_results:
                    matches = matches[:max_results]

                response: Dict[str, Any] = {"status": "success", "message": matches}
                skipped_count = sum(1 for e in errors if "maximum line length" in e)
                if skipped_count:
                    response["warnings"] = [
                        f"{skipped_count} file(s) skipped: line length exceeds p4 grep limit of 4096 characters"
                    ]
                return response
            except P4Exception as e:
                logger.error(f"P4Error: Failed to grep files with pattern '{pattern}' in '{depot_path}': {e}")
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
                # Under exception_level=1 a benign "file(s) up-to-date" outcome
                # no longer raises; it is surfaced via the additive top-level
                # `warnings` field instead of being reported as an error here.
                return {"status": "success", "message": result}
            except P4Exception as e:
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

                args = []
                if mode:
                    if mode in RESOLVE_MODE_FLAGS:
                        args.append(RESOLVE_MODE_FLAGS[mode])
                    else:
                        raise ValueError(f"Invalid resolve mode: {mode}")
                if changelist and changelist != "default":
                    args.extend(["-c", changelist])
                if len(file_paths) > 0:
                    args.extend(file_paths)
                result = p4.run_resolve(*args)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to resolve files in changelist '{changelist}': {e}")
                return {"status": "error", "message": str(e)}

    