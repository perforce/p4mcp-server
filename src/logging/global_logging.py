"""
Global logging configuration for P4 MCP server
"""
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import sys
import os
from typing import Optional

class LoggingConfig:
    """Configuration constants for logging"""
    DEFAULT_LOG_LEVEL = "INFO"
    WHEN = "midnight"
    DAY_INTERVAL = 1  # Rotate logs daily
    MAX_LOG_SIZE = 1024 * 1024 * 1024  # 1GB
    BACKUP_COUNT = 7
    ENCODING = "utf-8"
    
    NOISY_LOGGERS = [
        'urllib3', 'requests', 'asyncio', 'P4', 
        'fastmcp', 'mcp.server.lowlevel.server'
    ]

class GlobalLogger:
    """Handles global application logging"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._setup_complete = False
    
    def setup(self, log_level: str = LoggingConfig.DEFAULT_LOG_LEVEL, 
              log_file: Optional[str] = None, 
              disable_logging: bool = False) -> None:
        """Setup global logging configuration"""
        if disable_logging or log_level.upper() == "OFF":
            logging.disable(logging.CRITICAL)
            return
        
        if log_level.upper() == "QUIET":
            log_level = "CRITICAL"
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        root_logger.setLevel(numeric_level)
        
        # Setup global logging handlers
        self._setup_global_handlers(root_logger, log_file)
        self._suppress_noisy_loggers()
        self._setup_complete = True
    
    def _setup_global_handlers(self, root_logger: logging.Logger, log_file: Optional[str]) -> None:
        """Setup global logging handlers"""
        global_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )
        
        # Determine log file path
        if log_file is None:
            project_root = self._get_project_root()
            logs_dir = project_root / 'logs'
            log_file_path = logs_dir / "p4mcp.log"
        else:
            log_file_path = Path(log_file)
            logs_dir = log_file_path.parent
        
        # Create logs directory
        logs_dir.mkdir(exist_ok=True)
        
        # Add rotating file handler for global logs
        try:
            global_handler = TimedRotatingFileHandler(
                log_file_path,
                when=LoggingConfig.WHEN,
                interval=LoggingConfig.DAY_INTERVAL,
                backupCount=LoggingConfig.BACKUP_COUNT,
                encoding=LoggingConfig.ENCODING
            )
            self._add_handler(root_logger, global_handler, global_formatter)
        except Exception as e:
            print(f"Warning: Failed to create global log file {log_file_path}: {e}", file=sys.stderr)
        
        # Add console handler for global logs
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self._add_handler(root_logger, logging.StreamHandler(sys.stderr), console_formatter)
    
    def _suppress_noisy_loggers(self) -> None:
        """Suppress commonly noisy third-party loggers"""
        for logger_name in LoggingConfig.NOISY_LOGGERS:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    def _add_handler(self, logger: logging.Logger, handler: logging.Handler, formatter: logging.Formatter) -> None:
        """Helper function to configure and add a handler to the logger"""
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the global logger instance"""
        if not self._setup_complete:
            self.setup()  # Auto-setup with defaults if not already done
        return self._logger
    
    @staticmethod
    def _get_project_root() -> Path:
        """Get project root directory"""
        if getattr(sys, 'frozen', False):
            return Path(os.path.dirname(sys.executable))
        return Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Global instance
_global_logger = GlobalLogger()

# Public API
def setup_logging(log_level: str = LoggingConfig.DEFAULT_LOG_LEVEL, 
                  log_file: Optional[str] = None, 
                  disable_logging: bool = False) -> None:
    """Setup global logging configuration"""
    _global_logger.setup(log_level, log_file, disable_logging)

def get_logger() -> logging.Logger:
    """Get the global application logger"""
    return _global_logger.get_logger()

def disable_all_logging() -> None:
    """Completely disable all logging"""
    logging.disable(logging.CRITICAL)

def enable_logging() -> None:
    """Re-enable logging"""
    logging.disable(logging.NOTSET)