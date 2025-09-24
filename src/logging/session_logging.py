"""
Session logging configuration for P4 MCP server telemetry
"""
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import sys
import os
import uuid
from typing import Optional, Dict, Any
import threading
import json
import platform
import requests
from src.telemetry.upload_logs import upload_logs

logger = logging.getLogger(__name__)

class SessionConfig:
    """Configuration constants for session logging"""
    REQUEST_TIMEOUT = 5
    TELEMETRY_CONSENT_FILE = '.p4mcp_telemetry_consent.json'
    WHEN = "midnight"
    DAY_INTERVAL = 1  # Rotate logs daily
    MAX_LOG_SIZE = 100 * 1024 * 1024  # 100MB
    BACKUP_COUNT = 7
    ENCODING = "utf-8"

class SessionManager:
    """Manages session state and telemetry logging"""
    
    def __init__(self):
        self._current_session_id: Optional[str] = None
        self._session_loggers: Dict[str, logging.Logger] = {}
        self._lock = threading.Lock()
        self._user_details: Optional[Dict[str, Any]] = None
    
    @property
    def current_session_id(self) -> Optional[str]:
        return self._current_session_id
    
    def _get_user_id(self) -> str:
        """Get user ID from consent file"""
        consent_path = Path.home() / SessionConfig.TELEMETRY_CONSENT_FILE
        if not consent_path.exists():
            return 'unknown'
        
        try:
            with open(consent_path, 'r') as f:
                consent_data = json.load(f)
                return consent_data.get('user_id', 'unknown')
        except (json.JSONDecodeError, IOError, KeyError):
            return 'unknown'
    
    def _get_public_ip(self) -> str:
        """Get public IP address with error handling"""
        try:
            response = requests.get('https://api.ipify.org', timeout=SessionConfig.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text.strip()
        except (requests.RequestException, requests.Timeout):
            return "unknown"
    
    def get_user_details(self) -> Dict[str, Any]:
        """Get cached user details"""
        if self._user_details is None:
            self._user_details = {
                "id": self._get_user_id(),
                "os": platform.system(),
                "os_ver": platform.release()
            }
        return self._user_details
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new session with proper cleanup"""
        with self._lock:
            if session_id is None:
                session_id = uuid.uuid4().hex[:16]
            
            # End existing session if any
            if self._current_session_id:
                self._end_session_internal(self._current_session_id)
            
            self._current_session_id = session_id
            
            try:
                self._create_session_logger(session_id)
                logger.info(f"Session started: {session_id}")
            except Exception as e:
                logger().error(f"Failed to start session {session_id}: {e}")
                raise
            
            return session_id
    
    def _create_session_logger(self, session_id: str) -> None:
        """Create session-specific logger for telemetry data only"""
        session_logger = logging.getLogger(f"session.{session_id}")
        session_logger.handlers.clear()
        session_logger.setLevel(logging.INFO)
        session_logger.propagate = False  # Don't propagate to global logger
        
        # Create session log directory and file
        project_root = self._get_project_root()
        sessions_dir = project_root / 'logs' / 'sessions'
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        session_log_file = sessions_dir / f"{session_id}.log"
        session_formatter = SessionJsonFormatter(session_id, self)

        session_handler = TimedRotatingFileHandler(
            session_log_file, 
            when=SessionConfig.WHEN, 
            interval=SessionConfig.DAY_INTERVAL, 
            backupCount=SessionConfig.BACKUP_COUNT, 
            encoding=SessionConfig.ENCODING
        )
        session_handler.setFormatter(session_formatter)
        session_logger.addHandler(session_handler)
        
        self._session_loggers[session_id] = session_logger
    
    def end_session(self, session_id: Optional[str] = None) -> None:
        """End session with proper cleanup"""
        with self._lock:
            target_session_id = session_id or self._current_session_id
            if target_session_id:
                self._end_session_internal(target_session_id)
    
    def _end_session_internal(self, session_id: str) -> None:
        """Internal session cleanup"""
        if session_id in self._session_loggers:
            session_logger = self._session_loggers[session_id]
            
            # Close handlers
            for handler in session_logger.handlers[:]:
                handler.close()
                session_logger.removeHandler(handler)
            
            del self._session_loggers[session_id]
            
            # Upload session log
            try:
                self._upload_session_log(session_id)
            except Exception as e:
                logger.error(f"Failed to upload session log {session_id}: {e}")

            logger.info(f"Session ended: {session_id}")

            if session_id == self._current_session_id:
                self._current_session_id = None
    
    def _upload_session_log(self, session_id: str) -> None:
        """Upload session log file"""
        project_root = self._get_project_root()
        log_file = project_root / 'logs' / 'sessions' / f"{session_id}.log"
        if log_file.exists():
            upload_logs(str(log_file))

    def get_session_logger(self, session_id: Optional[str] = None) -> Optional[logging.Logger]:
        """Get session-specific logger (returns None if no session)"""
        target_session_id = session_id or self._current_session_id
        if target_session_id and target_session_id in self._session_loggers:
            return self._session_loggers[target_session_id]
        return None
    
    def log_tool_call(self, tool_data: Dict[str, Any], session_id: Optional[str] = None) -> None:
        """Log tool call data to session log only"""
        session_logger = self.get_session_logger(session_id)
        if not session_logger:
            logger.warning(f"No active session for tool call logging: {tool_data.get('tool_name', 'unknown')}")
            return
        
        # Ensure tool_data has expected structure
        formatted_tool_call = {
            "mcp_client": tool_data.get("mcp_client", "unknown"),
            "toolset": tool_data.get("toolset", "unknown"),
            "tool_name": tool_data.get("tool_name", "unknown"),
            "tool_action": tool_data.get("tool_action", "unknown"),
            "status": tool_data.get("status", "unknown"),
            "p4_version": tool_data.get("p4_version", "unknown")
        }
        
        session_logger.info(json.dumps(formatted_tool_call))
    
    @staticmethod
    def _get_project_root() -> Path:
        """Get project root directory"""
        if getattr(sys, 'frozen', False):
            return Path(os.path.dirname(sys.executable))
        return Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class SessionJsonFormatter(logging.Formatter):
    """Custom JSON formatter for session logs only"""
    
    def __init__(self, session_id: str, session_manager: SessionManager):
        super().__init__()
        self.session_id = session_id
        self.session_manager = session_manager
    
    def format(self, record) -> str:
        """Format log record as JSON for session telemetry"""
        try:
            # Try to parse message as JSON first (for tool calls)
            message = record.getMessage()
            try:
                tool_call = json.loads(message)
            except json.JSONDecodeError:
                tool_call = message
            
            log_entry = {
                "session_id": self.session_id,
                "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
                "tool_call": tool_call,
                "user": self.session_manager.get_user_details()
            }
            return json.dumps(log_entry)
        except Exception as e:
            # Fallback to simple string format if JSON formatting fails
            return f"JSON_FORMAT_ERROR: {record.getMessage()} | Error: {e}"

# Global instance
_session_manager = SessionManager()

# Public API
def start_session(session_id: Optional[str] = None) -> str:
    """Start a new session"""
    return _session_manager.start_session(session_id)

def end_session(session_id: Optional[str] = None) -> None:
    """End the current session"""
    _session_manager.end_session(session_id)

def get_session_logger(session_id: Optional[str] = None) -> Optional[logging.Logger]:
    """Get session-specific logger (returns None if no session)"""
    return _session_manager.get_session_logger(session_id)

def log_tool_call(tool_data: Dict[str, Any], session_id: Optional[str] = None) -> None:
    """Log tool call data to session log"""
    _session_manager.log_tool_call(tool_data, session_id)

def get_current_session_id() -> Optional[str]:
    """Get current session ID"""
    return _session_manager.current_session_id
        