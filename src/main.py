import sys
import logging
import argparse
import signal
from pathlib import Path
from src.telemetry.consent import consent_config_exist
from src.logging.global_logging import setup_logging
from src.logging.session_logging import start_session, end_session
from src.core.connection import __version__

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.server import P4MCPServer

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
        default=["files", "changelists", "shelves", "workspaces", "jobs"],
        help="List of toolsets to enable (default: files, changelists, shelves, workspaces, jobs)"
    )
    parser.add_argument(
        "--allow-usage",
        action="store_true",
        default=False,
        help="Allow usage data collection (default: False)"
    )

    return parser.parse_args()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info("Received shutdown signal, stopping server...")
    sys.exit(0)

def main() -> None:
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    server = None
    session_id = None
    args = None
    try:
        args = parse_args()
        logger.info("Parsed arguments: %s", args)
        if args.allow_usage==True:
            if consent_config_exist():
                logger.info("Telemetry consent config exists.")
                session_id = start_session()
        server = P4MCPServer(session_id=session_id, readonly=args.readonly, toolsets=args.toolsets)
        logger.info("Starting P4 MCP Server")
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