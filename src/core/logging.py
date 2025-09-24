"""
Logging configuration for P4 MCP server
"""
import logging
from pathlib import Path
import sys
import os
import uuid
from typing import Optional

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None, disable_logging: bool = False):
    """
    Setup logging configuration with file output in logs directory
    
    If log_file is not specified, creates a 'p4mcp-{uuid}.log' file in the 'logs' directory
    relative to the current working directory. Creates the 'logs' directory if it doesn't exist.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL, OFF, QUIET)
        log_file: Optional log file path
        disable_logging: If True, completely disable all logging
    """
    
    # Handle logging disable options
    if disable_logging or log_level.upper() == "OFF":
        logging.disable(logging.CRITICAL)
        return
    
    # Handle quiet mode
    if log_level.upper() == "QUIET":
        log_level = "CRITICAL"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Determine log file path and create directory
    if log_file is None:
        if getattr(sys, 'frozen', False):
            project_root = Path(os.path.dirname(sys.executable))
        else:
            project_root = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
        logs_dir = project_root / 'logs'
        log_file = logs_dir / f"p4mcp-{uuid.uuid4()}.log"
    else:
        log_file = Path(log_file)
        logs_dir = log_file.parent
    
    # Create logs directory
    logs_dir.mkdir(exist_ok=True)
    
    # Add file handler
    try:
        _add_handler(root_logger, logging.FileHandler(log_file), formatter)
    except Exception as e:
        print(f"Warning: Failed to create log file {log_file}: {e}", file=sys.stderr)
    
    # Add console handler
    _add_handler(root_logger, logging.StreamHandler(sys.stderr), formatter)
    
    # Suppress noisy third-party loggers
    _suppress_noisy_loggers()

def _add_handler(logger: logging.Logger, handler: logging.Handler, formatter: logging.Formatter):
    """Helper function to configure and add a handler to the logger"""
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def _suppress_noisy_loggers():
    """Suppress commonly noisy third-party loggers"""
    noisy_loggers = [
        'urllib3',
        'requests',
        'asyncio',
        'P4',  # P4Python logger
        'fastmcp',  # FastMCP logger if it exists
        'mcp.server.lowlevel.server'  # MCP server logger
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

def disable_all_logging():
    """Completely disable all logging"""
    logging.disable(logging.CRITICAL)

def enable_logging():
    """Re-enable logging (reverses disable_all_logging)"""
    logging.disable(logging.NOTSET)