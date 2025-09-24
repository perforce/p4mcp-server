import json
import logging
from fastmcp import FastMCP, Context
from .core.config import Config
from .logging.global_logging import setup_logging
from .logging.session_logging import log_tool_call
from .core.connection import P4ConnectionManager

from .models import models as m
from .handlers.handlers import Handlers

from .services.file_services import FileServices
from .services.server_services import ServerServices
from .services.shelve_services import ShelveServices
from .services.workspace_services import WorkspaceServices
from .services.changelist_services import ChangelistServices
from .services.job_services import JobServices

from .middleware.check_permission import CheckPermissionMiddleware

logger = logging.getLogger(__name__)

class P4MCPServer:
    """Perforce MCP Server with improved structure"""

    def __init__(self, session_id: str = None, readonly: bool = True, toolsets: list = []):
        self.readonly = readonly
        self.toolsets = toolsets
        self.session_id = session_id

        setup_logging()
        self.p4config = Config.load()
        self.p4_manager = P4ConnectionManager(self.p4config)

        if self.readonly:
            logger.info("Running in read-only mode. No write operations will be allowed.")
        else:
            logger.info("Running in read-write mode. Write operations are enabled.")
    
        logger.info(f"Enabled toolsets: {', '.join(self.toolsets) if self.toolsets else 'None'}")

        self.mcp = FastMCP("P4 MCP Server", middleware=[CheckPermissionMiddleware(self.p4_manager)])
        self._initialize_dependencies()
    
    def _initialize_dependencies(self) -> None:
        """Initialize all dependencies with proper error handling"""
        try:
            self._initialize_handlers()
            self._register_tools()
        except Exception as e:
            logger.error(f"Failed to initialize dependencies: {e}")
            raise

    def _initialize_handlers(self) -> None:
        """Initialize handlers with all services"""
        self.handlers = Handlers(
            server_services=ServerServices(self.p4_manager),
            workspace_services=WorkspaceServices(self.p4_manager),
            file_services=FileServices(self.p4_manager),
            changelist_services=ChangelistServices(self.p4_manager),
            shelve_services=ShelveServices(self.p4_manager),
            job_services=JobServices(self.p4_manager)
        )

    def process_tool_logs(self, tool_name: str, result: dict, ctx: Context) -> dict:
        """Process incoming data and route to appropriate handler"""
        response = {}
        response['mcp_client'] = ctx.session.client_params.clientInfo.name if ctx and ctx.session and ctx.session.client_params else "Unknown"
        response['toolset'] = tool_name.split('_')[1] if '_' in tool_name else "unknown"
        response['tool_name'] = tool_name
        response['tool_action'] = result.get('action', 'unknown')
        response['status'] = result.get('status', 'unknown')
        response['p4_version'] = getattr(self.p4config, 'p4version', 'Unknown')

        logger.info('tool_call: %s', json.dumps(response))

        if self.session_id:
            log_tool_call(response, session_id=self.session_id)

    @staticmethod
    def requires_approval(func, params):
        """Handle dangerous operations that require user approval"""
        logger.warning(f"Approval required for dangerous operation: {params.action} on {func.split('_')[1]}")
        # Return a special response that forces MCP client to ask for approval
        return {
                "_meta": {
                    "requires_approval": True,
                    "approval_type": "dangerous_operation"
                },
                "type": "approval_required",
                "operation": f"delete_{func.split('_')[1]}",
                "message": f"⚠️ DANGER: This will permanently delete the {func.split('_')[1]}. \
                            This action cannot be undone. Next operation should not be executed until the user approves.",

                "details": {
                    "source_tool": func,
                    "action": params.action,
                    "params": params.model_dump()
                },
                
                "instruction": "User must explicitly approve this operation",
                "on_approval": "execute_delete"
        }

    def _register_tools(self):
        """Register read-only tools (always available)"""
        
        @self.mcp.tool(tags=["read", "server"])
        async def query_server(params: m.QueryServerParams, ctx: Context) -> dict:
            """Get server info and current user information (READ permission)"""
            result = await self.handlers.handle("query", "server", params)
            self.process_tool_logs("query_server", result, ctx)
            return result
        
        @self.mcp.tool(tags=["read", "workspaces"], enabled="workspaces" in self.toolsets)
        async def query_workspaces(params: m.QueryWorkspacesParams, ctx: Context) -> dict:
            """Get workspace details, list workspaces, check type and status (READ permission)"""
            result = await self.handlers.handle("query", "workspaces", params)
            self.process_tool_logs("query_workspaces", result, ctx)
            return result

        @self.mcp.tool(tags=["read", "files"], enabled="files" in self.toolsets)
        async def query_files(params: m.QueryFilesParams, ctx: Context) -> dict:
            """Get file content, history, info, diff, annotations (READ permission)"""
            result = await self.handlers.handle("query", "files", params)
            self.process_tool_logs("query_files", result, ctx)
            return result

        @self.mcp.tool(tags=["read", "changelists"], enabled="changelists" in self.toolsets)
        async def query_changelists(params: m.QueryChangelistsParams, ctx: Context) -> dict:
            """Get changelist details and list changelists (READ permission)"""
            result = await self.handlers.handle("query", "changelists", params)
            self.process_tool_logs("query_changelists", result, ctx)
            return result

        @self.mcp.tool(tags=["read", "shelves"], enabled="shelves" in self.toolsets)
        async def query_shelves(params: m.QueryShelvesParams, ctx: Context) -> dict:
            """List shelves, get shelve diff and files (READ permission)"""
            result = await self.handlers.handle("query", "shelves", params)
            self.process_tool_logs("query_shelves", result, ctx)
            return result

        @self.mcp.tool(tags=["read", "jobs"], enabled="jobs" in self.toolsets)
        async def query_jobs(params: m.QueryJobsParams, ctx: Context) -> dict:
            """Get jobs from changelist and get job details (READ permission)"""
            result = await self.handlers.handle("query", "jobs", params)
            self.process_tool_logs("query_jobs", result, ctx)
            return result

        @self.mcp.tool(tags=["write", "workspaces"], enabled=not self.readonly and "workspaces" in self.toolsets)
        async def modify_workspaces(params: m.ModifyWorkspacesParams, ctx: Context) -> dict:
            """Create/delete workspace, Update workspace specs, and switch active workspace (WRITE permission)"""
            if params.action == "delete":
                # Handle delete operation with approval
                result = {"status": "warning", "action": "delete", "message": "Requires approval to delete workspace."}
                self.process_tool_logs("modify_workspaces", result, ctx)
                return self.requires_approval("modify_workspaces", params)
            result = await self.handlers.handle("modify", "workspaces", params)
            self.process_tool_logs("modify_workspaces", result, ctx)
            return result

        @self.mcp.tool(tags=["write", "files"], enabled=not self.readonly and "files" in self.toolsets)
        async def modify_files(params: m.ModifyFilesParams, ctx: Context) -> dict:
            """Add, edit, move, delete, revert, reconcile, resolve, and sync files (WRITE permission)"""
            if params.action == "delete":
                # Handle delete operation with approval
                result = {"status": "warning", "action": "delete", "message": "Requires approval to delete files."}
                self.process_tool_logs("modify_files", result, ctx)
                return self.requires_approval("modify_files", params)
            result = await self.handlers.handle("modify", "files", params)
            self.process_tool_logs("modify_files", result, ctx)
            return result

        @self.mcp.tool(tags=["write", "changelists"], enabled=not self.readonly and "changelists" in self.toolsets)
        async def modify_changelists(params: m.ModifyChangelistsParams, ctx: Context) -> dict:
            """Create/delete changelists, update changelists and organize files/jobs (WRITE permission)"""
            if params.action == "delete":
                # Handle delete operation with approval
                result = {"status": "warning", "action": "delete", "message": "Requires approval to delete changelist."}
                self.process_tool_logs("modify_changelists", result, ctx)
                return self.requires_approval("modify_changelists", params)
            result = await self.handlers.handle("modify", "changelists", params)
            self.process_tool_logs("modify_changelists", result, ctx)
            return result

        @self.mcp.tool(tags=["write", "shelves"], enabled=not self.readonly and "shelves" in self.toolsets)
        async def modify_shelves(params: m.ModifyShelvesParams, ctx: Context) -> dict:
            """Create/delete, update shelves and unshelve files (WRITE permission)"""
            if params.action == "delete":
                # Handle delete operation with approval
                result = {"status": "warning", "action": "delete", "message": "Requires approval to delete shelve."}
                self.process_tool_logs("modify_shelves", result, ctx)
                return self.requires_approval("modify_shelves", params)
            result = await self.handlers.handle("modify", "shelves", params)
            self.process_tool_logs("modify_shelves", result, ctx)
            return result

        @self.mcp.tool(tags=["write", "jobs"], enabled=not self.readonly and "jobs" in self.toolsets)
        async def modify_jobs(params: m.ModifyJobsParams, ctx: Context) -> dict:
            """Link or unlink jobs (WRITE permission)"""
            result = await self.handlers.handle("modify", "jobs", params)
            self.process_tool_logs("modify_jobs", result, ctx)
            return result

        @self.mcp.tool(tags=["write", "delete"], enabled=not self.readonly and len(set(self.toolsets) - {"jobs"}) > 0)
        async def execute_delete(params: m.ExecuteDeleteParams, ctx: Context) -> dict:
            """Execute any approved delete operation from any tool (WRITE permission)"""
            if params.source_tool.split("_")[1] not in self.toolsets:
                result = {"status": "error", "action": "delete", "message": f"Toolset not allowed: {params.source_tool.split('_')[1]}"}
                self.process_tool_logs("execute_delete", result, ctx)
                return result
            # Route to appropriate handler based on source tool
            if params.source_tool == "modify_workspaces":
                workspace_params = m.ModifyWorkspacesParams(
                    action="delete", 
                    name=params.workspace_name
                )
                result = await self.handlers.handle("modify", "workspaces", workspace_params)
                self.process_tool_logs("execute_delete", result, ctx)
                return result
            
            elif params.source_tool == "modify_changelists":
                changelist_params = m.ModifyChangelistsParams(
                    action="delete", 
                    changelist_id=params.changelist_id
                )
                result = await self.handlers.handle("modify", "changelists", changelist_params)
                self.process_tool_logs("execute_delete", result, ctx)
                return result

            elif params.source_tool == "modify_files":
                file_params = m.ModifyFilesParams(
                    action="delete", 
                    file_paths=params.file_paths
                )
                result = await self.handlers.handle("modify", "files", file_params)
                self.process_tool_logs("execute_delete", result, ctx)
                return result

            elif params.source_tool == "modify_shelves":
                shelve_params = m.ModifyShelvesParams(
                    action="delete", 
                    changelist_id=params.changelist_id,
                    file_paths=params.file_paths
                )
                result = await self.handlers.handle("modify", "shelves", shelve_params)
                self.process_tool_logs("execute_delete", result, ctx)
                return result

            else:
                result = {"status": "error", "action": "delete", "message": f"Unknown source tool: {params.source_tool}"}
                self.process_tool_logs("execute_delete", result, ctx)
                return result
            
        

    def run(self):
        """Run the MCP server"""
        self.mcp.run()