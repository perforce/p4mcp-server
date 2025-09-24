"""
P4 Client/Workspace services layer

Read service for tools:
- get_workspace : Get workspace specification
- list_workspaces : List available workspaces
- get_workspace_type : Analyze workspace type
- get_workspace_status : Get workspace status
- sync_workspace : Sync workspace files

Write service for tools:
- create_workspace : Create new workspace
- update_workspace : Update workspace specification
- delete_workspace : Delete workspace
- switch_workspace : Switch active workspace
"""

import logging
from typing import List, Dict, Any
from P4 import P4Exception

from ..core.connection import P4ConnectionManager

logger = logging.getLogger(__name__)

class WorkspaceServices:
    """Workspace services for client operations"""
    
    def __init__(self, connection_manager: P4ConnectionManager):
        self.connection_manager = connection_manager

    async def get_workspace(self, workspace_name: str) -> Dict[str, Any]:
        """Get workspace specification"""
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["client", "-o"]
                if workspace_name and len(workspace_name) > 0:
                    clients = p4.run_clients("-e", workspace_name)
                    if len(clients) == 0:
                        return {"status": "not_found", "message": f"Workspace '{workspace_name}' not found"}
                    args.append(workspace_name)
                workspace_spec = p4.run(*args)

                return {
                    "status": "success",
                    "message": {
                        k: v if isinstance(v, str) else "\n".join(v) if isinstance(v, list) else v
                        for k, v in workspace_spec[0].items()
                        if isinstance(v, str) or isinstance(v, list)
                    }
                }
            
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get workspace: {e}")
                return {"status": "error", "message": str(e)}

    async def list_workspaces(self, user: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List available workspaces"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if user:
                    workspaces_raw = p4.run("clients", "-u", user, f"-m{limit}")
                else:
                    workspaces_raw = p4.run("clients", f"-m{limit}")
                return {"status": "success", "message": [{k: v for k, v in ws.items() if isinstance(v, str)} for ws in workspaces_raw]}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to list workspaces: {e}")
                return {"status": "error", "message": str(e)}

    async def get_workspace_type(self, workspace_name: str) -> str:
        """Analyze workspace type"""
        async with self.connection_manager.get_connection() as p4:
            try:
                workspace_spec = await self.get_workspace(workspace_name)
                if not workspace_spec:
                    return {"status": "error", "message": "Workspace not found"}

                # Example logic to determine workspace type
                if "View" in workspace_spec and "//depot/" in workspace_spec["View"]:
                    return {"status": "success", "message": "standard"}
                elif "Stream" in workspace_spec:
                    return {"status": "success", "message": "stream"}
                else:
                    return {"status": "success", "message": "custom"}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get workspace type: {e}")
                return {"status": "error", "message": str(e)}

    async def get_workspace_status(self, workspace_name: str) -> Dict[str, Any]:
        """Get workspace status"""

        #print current working directory

        async with self.connection_manager.get_connection() as p4:
            try:
                workspace_spec = await self.get_workspace(workspace_name)
                if not workspace_spec:
                    return {"status": "not_found", "message": f"Workspace '{workspace_name}' not found"}
                
                # Opened files
                opened_files = p4.run_opened()

                # Out-of-sync files
                try:
                    out_of_sync = p4.run_sync('-n')
                except P4Exception as e:
                    if "File(s) up-to-date" in str(e):
                        out_of_sync = []
                    else:
                        logger.error(f"P4Error: Failed to check out-of-sync files: {e}")
                        return {"status": "error", "message": str(e)}

                # Pending resolves
                try:
                    pending_resolves = p4.run_resolve('-n')
                except P4Exception as e:
                    if "No file(s) to resolve" in str(e):
                        pending_resolves = []
                    else:
                        logger.error(f"P4Error: Failed to check pending resolves: {e}")
                        return {"status": "error", "message": str(e)}

                # Last synced changelist
                synced_changes = p4.run_changes('-m1', '#have')
                last_synced_cl = synced_changes[0]['change'] if synced_changes else None

                status = {
                    "opened_files": [f['depotFile'] for f in opened_files] if opened_files else [],
                    "out_of_sync_files": [f['depotFile'] for f in out_of_sync if isinstance(f, dict) and 'depotFile' in f] if out_of_sync else [],
                    "sync_warnings": [f for f in out_of_sync if isinstance(f, str)] if out_of_sync else [],
                    "pending_resolves": [f['fromFile'] for f in pending_resolves] if pending_resolves else [],
                    "last_synced_cl": last_synced_cl
                }
                return {"status": "success", "message": status}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get workspace status: {e} ")
                return {"status": "error", "message": str(e)}

    async def sync_workspace(self, path: str, force: bool) -> Dict[str, Any]:
        """Sync workspace files"""
        async with self.connection_manager.get_connection() as p4:
            try:
                args = ["sync"]
                if force:
                    args.append("-f")
                if path or len(path) > 0:
                    args.append(path)
                result = p4.run(*args)  # Sync all files in the workspace
                return {"status": "success", "message": result}
            except P4Exception as e:
                if "File(s) up-to-date" in str(e):
                    return {"status": "success", "message": "Workspace is already up-to-date"}
                else:
                    logger.error(f"P4Error: Failed to sync workspace: {e}")
                    return {"status": "error", "message": str(e)}


    async def create_workspace(self, workspace_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create new workspace"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if not workspace_spec or "Name" not in workspace_spec:
                    raise ValueError("Workspace specification must include 'Name'")
                client_spec = p4.fetch_client(workspace_spec["Name"])
                for key in workspace_spec:
                    if key.lower() in client_spec.__dict__["_Spec__fields"]:
                        setattr(client_spec, f"_{key.lower()}", workspace_spec[key])
                p4.save_client(client_spec)
                return {"status": "success", "message": "Workspace created successfully"}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to create workspace: {e}")
                return {"status": "error", "message": str(e)}

    async def update_workspace(self, workspace_name: str, workspace_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update workspace specification"""
        async with self.connection_manager.get_connection() as p4:
            try:
                current_user = p4.run("info")[0]["userName"]
                client_spec = p4.fetch_client(workspace_name)
                client_owner = client_spec["Owner"]

                # Compare and update only if owner matches
                if client_owner == current_user:
                    client_spec = p4.fetch_client(workspace_name)
                    for key in workspace_spec:
                        if key.lower() in client_spec.__dict__["_Spec__fields"]:
                            setattr(client_spec, f"_{key.lower()}", workspace_spec[key])
                    p4.save_client(client_spec)
                    return {"status": "success", "message": f"Workspace '{workspace_name}' owned by '{current_user}' updated successfully"}
                else:
                    return {"status": "failed", "message": f"Workspace '{workspace_name}' is owned by '{client_owner}', not  '{current_user}'"}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to update workspace '{workspace_name}': {e}")
                return {"status": "error", "message": str(e)}

    async def delete_workspace(self, workspace_name: str) -> Dict[str, Any]:
        """Delete workspace"""
        async with self.connection_manager.get_connection() as p4:
            try:
                current_user = p4.run("info")[0]["userName"]
                client_spec = p4.fetch_client(workspace_name)
                client_owner = client_spec["Owner"]

                # Compare and delete only if owner matches
                if client_owner == current_user:
                    p4.run("client", "-d", workspace_name)
                    return {"status": "success", "message": f"Workspace '{workspace_name}' owned by '{current_user}' deleted successfully"}
                else:
                    return {"status": "failed", "message": f"Workspace '{workspace_name}' is owned by '{client_owner}', not  '{current_user}'"}
                
            except P4Exception as e:
                logger.error(f"P4Error: Failed to delete workspace '{workspace_name}': {e}")
                return {"status": "error", "message": str(e)}

    async def switch_workspace(self, workspace_name: str) -> Dict[str, Any]:
        """Switch active workspace"""
        async with self.connection_manager.get_connection() as p4:
            try:
                current_user = p4.run("info")[0]["userName"]
                client_spec = p4.fetch_client(workspace_name)
                client_owner = client_spec["Owner"]

                # Compare and switch only if owner matches
                if client_owner == current_user:
                    p4.client = workspace_name
                    return {"status": "success", "message": f"Switched to workspace '{workspace_name}' owned by '{current_user}'"}
                else:
                    return {"status": "failed", "message": f"Workspace '{workspace_name}' is owned by '{client_owner}', not  '{current_user}'"}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to switch to workspace '{workspace_name}': {e}")
                return {"status": "error", "message": str(e)}

    