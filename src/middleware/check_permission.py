from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
import logging
from ..core.connection import P4ConnectionManager
import time

logger = logging.getLogger(__name__)

class CheckPermissionMiddleware(Middleware):
    """Middleware to check tool permissions based on P4 properties"""

    def __init__(self, connection_manager: P4ConnectionManager):
        super().__init__()
        self.connection_manager = connection_manager
        self._property_cache = {}
        self._cache_timeout = 60  # 1 minute
        self._last_cache_update = 0

    def _parse_tool_info_from_tags(self, tool_name: str, tags: list) -> dict:
        """Extract tool information from tags instead of parsing tool name"""
        tool_info = {
            'operation_type': 'read',     # Default to read
            'toolset': 'unknown',
            'is_write_operation': False,
            'is_delete_operation': False,
        }

        # Extract operation type and toolset from tags
        for tag in tags:
            if tag in ['read', 'write', 'delete']:
                tool_info['operation_type'] = tag
                tool_info['is_write_operation'] = tag in ['write', 'delete']
                tool_info['is_delete_operation'] = tag == 'delete'
            elif tag in ['server', 'files', 'workspaces', 'changelists', 'shelves', 'jobs']:
                tool_info['toolset'] = tag

        # Fallback to parsing tool name if tags don't provide enough info
        if tool_info['toolset'] == 'unknown' and '_' in tool_name:
            tool_info['toolset'] = tool_name.split('_')[1]

        return tool_info

    async def _refresh_properties_cache(self):
        """Fetch all properties and cache them"""
        current_time = time.time()
        if (self._property_cache and
            current_time - self._last_cache_update < self._cache_timeout):
            return  # Cache is still valid

        try:
            async with self.connection_manager.get_connection() as p4:
                if not p4:
                    self._property_cache = {}
                    return
                result = p4.run("property", "-l")
                # Build a dict: {property_name: value}
                self._property_cache = {prop['name']: prop.get('value', '').strip() for prop in result}
                self._last_cache_update = current_time
        except Exception as e:
            logger.warning(f"Failed to refresh property cache: {e}")
            self._property_cache = {}

    async def _get_property_value(self, property_name):
        """Get property value from cached properties"""
        await self._refresh_properties_cache()
        return self._property_cache.get(property_name)

    async def _check_global_permissions(self, tool_info: dict):
        """Check global MCP permissions based on operation type from tags"""
        mcp_enabled = await self._get_property_value("mcp.enabled")
        if mcp_enabled is not None and mcp_enabled.lower() == "false":
            raise ToolError("P4 MCP server is disabled by the administrator")

        if tool_info['is_write_operation']:
            global_write = await self._get_property_value("mcp.toolsets.write")
            if global_write is not None and global_write.lower() == "false":
                raise ToolError("Write operations are disabled by the administrator")

        return True

    async def _check_toolset_permissions(self, tool_info: dict):
        """Check toolset-specific permissions using tag-based toolset"""
        toolset = tool_info['toolset']

        allowed_toolsets = await self._get_property_value("mcp.toolsets.allowed")
        if allowed_toolsets:
            allowed_list = [ts.strip() for ts in allowed_toolsets.split(",")]
            if toolset not in allowed_list:
                raise ToolError(f"Toolset '{toolset}' is disabled by the administrator")

        toolset_enabled = await self._get_property_value(f"mcp.toolset.{toolset}.enabled")
        if toolset_enabled is not None and toolset_enabled.lower() == "false":
            raise ToolError(f"Toolset '{toolset}' is disabled by the administrator")

        if tool_info['is_write_operation']:
            toolset_write = await self._get_property_value(f"mcp.toolset.{toolset}.write")
            if toolset_write is not None and toolset_write.lower() == "false":
                raise ToolError(f"Write operations disabled for toolset '{toolset}' by the administrator")

        return True

    async def _check_tool_permissions(self, tool_name, tool_info: dict):
        """Check specific tool permissions using tag-based toolset"""
        toolset = tool_info['toolset']

        allowed_tools = await self._get_property_value(f"mcp.toolset.{toolset}.tools")
        if allowed_tools:
            allowed_list = [tool.strip() for tool in allowed_tools.split(",")]
            if tool_name not in allowed_list:
                raise ToolError(f"Tool '{tool_name}' is disabled by the administrator")

        return True

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Check permissions before executing a tool"""
        if context.fastmcp_context:
            try:
                if not self.connection_manager:
                    raise ToolError("P4 connection manager not initialized")

                tool = await context.fastmcp_context.fastmcp.get_tool(context.message.name)
                tool_name = context.message.name

                # Parse tool information from tags
                tool_info = self._parse_tool_info_from_tags(tool_name, tool.tags)

                # Check global permissions
                await self._check_global_permissions(tool_info)

                # Check toolset permissions
                # await self._check_toolset_permissions(tool_info)

                # Check tool-specific permissions
                # await self._check_tool_permissions(tool_name, tool_info)

                # Check if tool is enabled
                if not tool.enabled:
                    raise ToolError("Tool is currently disabled")

                logger.info(f"Permission check passed for {tool_name} "
                            f"({tool_info['operation_type']} on {tool_info['toolset']})")

            except Exception as e:
                logger.error(f"Permission check failed: {e}")
                raise ToolError(f"Permission denied: {str(e)}")

        return await call_next(context)