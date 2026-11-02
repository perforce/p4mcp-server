import sys
import os
import logging
import argparse
import ipaddress
import signal
from pathlib import Path
from typing import Optional
from p4mcp.telemetry.consent import consent_config_exist
from p4mcp.logging.global_logging import setup_logging
from p4mcp.logging.session_logging import start_session, end_session
from p4mcp._version import __version__
from p4mcp.core.ssl_config import configure_tls_ca_mode, resolve_ssl_verify

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from p4mcp.server import P4MCPServer

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=__version__,
        help="Show program's version number"
    )
    parser.add_argument(
        "--readonly",
        action="store_true",
        default=False,
        help="Run in read-only mode"
    )
    parser.add_argument(
        "--toolsets",
        nargs='+',
        default=["files", "changelists", "shelves", "workspaces", "jobs", "reviews", "streams", "p4dam"],
        help="List of toolsets to enable (default: files, changelists, shelves, workspaces, jobs, reviews, streams, p4dam)"
    )
    parser.add_argument(
        "--allow-usage",
        action="store_true",
        default=False,
        help="Allow usage data collection (default: False)"
    )
    parser.add_argument(
        "--otel-console",
        action="store_true",
        default=False,
        help="Also export OpenTelemetry spans to the console (requires --allow-usage). "
             "Spans are exported to the console automatically when LOG_LEVEL=DEBUG."
    )
    parser.add_argument(
        "--ssl-no-verify",
        action="store_true",
        default=False,
        help="Disable SSL certificate verification for Swarm API requests"
    )
    parser.add_argument(
        "--ca-bundle",
        type=str,
        default=None,
        help="Path to a custom CA certificate bundle (PEM) for Swarm API requests"
    )

    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Directory for log files (default: <project_root>/logs). CLI argument takes precedence over P4MCP_LOG_DIR environment variable."
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Bind address for HTTP transport (default: 127.0.0.1, local connections only). "
             "Use 0.0.0.0 to accept connections from other machines; the HTTP transport has no authentication."
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Cap on rows the P4 server returns per command (p4.maxresults). "
             "Default: 10000; 0 disables the limit. Overrides P4MCP_MAX_RESULTS."
    )
    parser.add_argument(
        "--max-scan-rows",
        type=int,
        default=None,
        help="Cap on rows the P4 server scans per command (p4.maxscanrows). "
             "Unset by default. Overrides P4MCP_MAX_SCAN_ROWS."
    )
    parser.add_argument(
        "--search-transform",
        choices=["regex", "bm25", "both"],
        default=None,
        help="Enable search-based tool discovery: 'regex' for pattern matching, "
             "'bm25' for natural-language ranking, 'both' for both. "
             "Default (omitted) sends the full tool catalog."
    )
    return parser.parse_args()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info("Received shutdown signal, stopping server...")
    sys.exit(0)

def resolve_log_dir(args, config) -> Optional[str]:
    """Determine log directory setting from parsed CLI args and config.

    Priority: --log-dir > P4MCP_LOG_DIR env var > None (use default).

    Args:
        args: Parsed command-line arguments
        config: Loaded configuration (includes P4MCP_LOG_DIR from env)

    Returns:
        str path or None.
    """
    if args.log_dir:
        return args.log_dir
    if config.log_dir:
        return config.log_dir
    return None  # use default

def is_loopback_host(host: str) -> bool:
    """Check whether a bind address only accepts connections from the local machine.

    Args:
        host: Bind address passed to the HTTP transport (IP literal or hostname)

    Returns:
        True for "localhost" and loopback IPs (127.0.0.0/8, ::1); False otherwise.
    """
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False

def main() -> None:
    # Parse arguments first (before any logging)
    args = parse_args()

    # Load config to get environment variables (including P4MCP_LOG_DIR)
    from p4mcp.core.config import Config
    config = Config.load()

    # Resolve log directory with proper priority: CLI > env > default
    log_dir = resolve_log_dir(args, config)

    # Setup logging once with the correct log directory. LOG_LEVEL drives both
    # the log threshold and the OTel console-export gating, so honour it here
    # (default INFO) instead of hardcoding the level.
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    setup_logging(log_level, log_dir=log_dir)

    # Now that logging is configured, log startup messages
    configure_tls_ca_mode()
    logger.info("Parsed arguments: %s", args)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    server = None
    session_id = None
    try:
        if args.allow_usage:
            if consent_config_exist():
                logger.info("Telemetry consent config exists.")
                session_id = start_session(
                    otel_console=args.otel_console,
                    ca_bundle=args.ca_bundle,
                )
        # Determine SSL verify: --ca-bundle > --ssl-no-verify > env vars > default (True)
        ssl_verify = resolve_ssl_verify(args)
        p4dam_api_key = os.environ.get("P4DAM_API_KEY", "").strip() or None
        server = P4MCPServer(
            session_id=session_id,
            readonly=args.readonly,
            toolsets=args.toolsets,
            search_transform=args.search_transform,
            ssl_verify=ssl_verify,
            log_dir=log_dir,
            max_results=args.max_results,
            max_scan_rows=args.max_scan_rows,
            p4dam_api_key=p4dam_api_key,
        )
        if args.transport == "http":
            logger.info(f"Starting P4 MCP Server with HTTP transport on {args.host}:{args.port}")
            if not is_loopback_host(args.host):
                logger.warning(
                    f"HTTP transport is bound to {args.host}, which accepts connections from other machines, "
                    "and has no authentication: any client that can reach this port can use every tool "
                    "as the configured Perforce user."
                )
            server.run(transport="http", port=args.port, host=args.host)
        else:
            logger.info("Starting P4 MCP Server with stdio transport")
            server.run()
    except Exception as e:
        logger.error(f"An error occurred while starting the server: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
    finally:
        if args is not None and args.allow_usage and session_id:
            end_session(session_id)
            logger.info("Telemetry session ended; spans flushed.")

if __name__ == "__main__":
    main()