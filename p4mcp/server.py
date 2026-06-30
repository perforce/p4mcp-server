import json
import logging

from fastmcp import FastMCP, Context
from .core.config import Config
from .core.connection import P4ConnectionManager

from .handlers.handlers import Handlers
from .middleware.check_permission import CheckPermissionMiddleware
from .middleware.telemetry_middleware import TelemetryMiddleware
from .tools import ALL_REGISTRARS

logger = logging.getLogger(__name__)

class P4MCPServer:
    """Perforce MCP Server with improved structure"""

    def __init__(self, session_id: str = None, readonly: bool = True, toolsets: list = [], search_transform: str = None, ssl_verify=None, log_dir: str = None, max_results=None, max_scan_rows=None):
        self.readonly = readonly
        self.toolsets = toolsets
        self.session_id = session_id
        self.search_transform = search_transform

        # Load P4 config (logging is already configured in main.py)
        self.p4config = Config.load()

        # CLI args take priority over config/env for the result limits. Only
        # override when a CLI value is supplied; reuse the config validator so a
        # non-integer/negative CLI value fails fast with a clear message before
        # any P4 connection is attempted.
        if max_results is not None:
            self.p4config.max_results = Config._parse_positive_int(
                "--max-results", max_results, default=None
            )
        if max_scan_rows is not None:
            self.p4config.max_scan_rows = Config._parse_positive_int(
                "--max-scan-rows", max_scan_rows, default=None
            )

        self.p4_manager = P4ConnectionManager(self.p4config)

        # CLI args take priority over config/env for SSL verify
        if ssl_verify is not None:
            self.p4config.ssl_verify = ssl_verify

        if self.readonly:
            logger.info("Running in read-only mode. No write operations will be allowed.")
        else:
            logger.info("Running in read-write mode. Write operations are enabled.")
    
        logger.info(f"Enabled toolsets: {', '.join(self.toolsets) if self.toolsets else 'None'}")

        # Telemetry middleware is registered outermost (ahead of the permission
        # check) and only when telemetry consent is on (a session is active), so
        # nothing is exported when consent is off.
        middleware = []
        if self.session_id:
            middleware.append(TelemetryMiddleware())
        middleware.append(CheckPermissionMiddleware(self.p4_manager))

        self.mcp = FastMCP("P4 MCP Server", middleware=middleware)
        self._initialize_dependencies()
        self._apply_search_transforms()
    
    def _initialize_dependencies(self) -> None:
        """Initialize all dependencies with proper error handling"""
        try:
            self._initialize_handlers()
            self._register_tools()
        except Exception as e:
            logger.error(f"Failed to initialize dependencies: {e}")
            raise

    def _initialize_handlers(self) -> None:
        """Initialize handlers with all services from the services package.

        Services are imported explicitly rather than via ``pkgutil.iter_modules``
        so that discovery works inside PyInstaller binaries.
        """
        from .services import changelist_services
        from .services import file_services
        from .services import job_services
        from .services import review_services
        from .services import server_services
        from .services import shelve_services
        from .services import stream_services
        from .services import workspace_services

        _SERVICE_MODULES = [
            changelist_services,
            file_services,
            job_services,
            review_services,
            server_services,
            shelve_services,
            stream_services,
            workspace_services,
        ]

        all_services = {}
        for module in _SERVICE_MODULES:
            module_name = module.__name__.rsplit(".", 1)[-1]
            # e.g. "file_services" -> "FileServices"
            class_name = module_name.replace("_", " ").title().replace(" ", "")
            cls = getattr(module, class_name, None)
            if cls is None:
                continue
            if module_name == "review_services":
                all_services[module_name] = cls(self.p4_manager, verify_ssl=self.p4config.ssl_verify)
            else:
                all_services[module_name] = cls(self.p4_manager)

        self.handlers = Handlers(**all_services)

    def process_tool_logs(self, tool_name: str, result: dict, ctx: Context) -> dict:
        """Emit an application-log line for a tool call.

        Telemetry is now carried by OpenTelemetry spans (see
        ``TelemetryMiddleware``); this retains only the local app-log line.
        """
        response = {}
        response['mcp_client'] = ctx.session.client_params.clientInfo.name if ctx and ctx.session and ctx.session.client_params else "Unknown"
        response['toolset'] = tool_name.split('_')[1] if '_' in tool_name else "unknown"
        response['tool_name'] = tool_name
        response['tool_action'] = result.get('action', 'unknown')
        response['status'] = result.get('status', 'unknown')
        response['p4_version'] = getattr(self.p4config, 'p4version', 'Unknown')

        logger.info('tool_call: %s', json.dumps(response))

    def _register_tools(self):
        """Register all tools by delegating to per-toolset modules."""
        for registrar in ALL_REGISTRARS:
            registrar(self)

    def _apply_search_transforms(self):
        """Apply search-based tool discovery transforms based on configuration.

        When enabled, the MCP client sees lightweight search/call synthetic
        tools instead of the full catalog, reducing token overhead.
        ``query_server`` is always pinned so it remains directly visible.
        """
        if not self.search_transform:
            return

        from fastmcp.server.transforms.search import (
            RegexSearchTransform,
            BM25SearchTransform,
        )

        always_visible = ["query_server"]

        if self.search_transform == "regex":
            self.mcp.add_transform(RegexSearchTransform(
                always_visible=always_visible,
            ))
            logger.info("Search transform enabled: regex")

        elif self.search_transform == "bm25":
            self.mcp.add_transform(BM25SearchTransform(
                always_visible=always_visible,
            ))
            logger.info("Search transform enabled: bm25")

        elif self.search_transform == "both":
            self.mcp.add_transform(RegexSearchTransform(
                always_visible=always_visible,
                search_tool_name="regex_search_tools",
                call_tool_name="regex_call_tool",
            ))
            self.mcp.add_transform(BM25SearchTransform(
                always_visible=always_visible,
                search_tool_name="semantic_search_tools",
                call_tool_name="semantic_call_tool",
            ))
            logger.info("Search transforms enabled: both (regex + bm25)")

    def run(self, transport="stdio", **kwargs):
        """Run the MCP server"""
        self.mcp.run(transport=transport, **kwargs)