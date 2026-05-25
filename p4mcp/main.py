import sys
import logging
import argparse
import signal
from pathlib import Path
from typing import Optional
from p4mcp.telemetry.consent import consent_config_exist
from p4mcp.logging.global_logging import setup_logging
from p4mcp.logging.session_logging import start_session, end_session
from p4mcp.core.connection import __version__
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
        default=["files", "changelists", "shelves", "workspaces", "jobs", "reviews", "streams"],
        help="List of toolsets to enable (default: files, changelists, shelves, workspaces, jobs, reviews, streams)"
    )
    parser.add_argument(
        "--allow-usage",
        action="store_true",
        default=False,
        help="Allow usage data collection (default: False)"
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

def main() -> None:
    # Parse arguments first (before any logging)
    args = parse_args()

    # Load config to get environment variables (including P4MCP_LOG_DIR)
    from p4mcp.core.config import Config
    config = Config.load()

    # Resolve log directory with proper priority: CLI > env > default
    log_dir = resolve_log_dir(args, config)

    # Setup logging once with the correct log directory
    setup_logging("INFO", log_dir=log_dir)

    # Now that logging is configured, log startup messages
    configure_tls_ca_mode()
    logger.info("Parsed arguments: %s", args)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    server = None
    session_id = None
    try:
        if args.allow_usage==True:
            if consent_config_exist():
                logger.info("Telemetry consent config exists.")
                session_id = start_session()
        # Determine SSL verify: --ca-bundle > --ssl-no-verify > env vars > default (True)
        ssl_verify = resolve_ssl_verify(args)
        server = P4MCPServer(
            session_id=session_id,
            readonly=args.readonly,
            toolsets=args.toolsets,
            search_transform=args.search_transform,
            ssl_verify=ssl_verify,
            log_dir=log_dir,
        )
        if args.transport == "http":
            logger.info(f"Starting P4 MCP Server with HTTP transport on port {args.port}")
            server.run(transport="http", port=args.port, host="0.0.0.0")
        else:
            logger.info("Starting P4 MCP Server with stdio transport")
            server.run()
    except Exception as e:
        logger.error(f"An error occurred while starting the server: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
    finally:
        if args is not None and args.allow_usage==True and session_id:
            end_session(session_id)
            logger.info("Uploading session log to server...")

if __name__ == "__main__":
    main()