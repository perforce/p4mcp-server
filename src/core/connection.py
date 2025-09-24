"""
P4Python connection management with session tracking
"""
import logging
import uuid
import time
import os
import json
from typing import Optional, Dict, Any, Union
from contextlib import asynccontextmanager
from P4 import P4, P4Exception
from .config import Config

logger = logging.getLogger(__name__)

__version__ = "2025.1.2830393"

class P4Session:
    """Manages P4 session with tracking and logging"""
    
    def __init__(self, config: Config, save_to_file: bool = False, session_id: str = None):
        """Initialize P4 session
        
        Args:
            config: Configuration object with P4 connection details
            save_to_file: If True, save session details to a file
            session_id: Optional session ID to use (will generate one if not provided)
        """
        self.config = config
        self.p4 = P4(cwd=os.getcwd())
        # Use provided session_id or generate a new one
        self.session_id = session_id or str(uuid.uuid4())
        self.start_time = time.time()
        self.save_to_file = save_to_file
        self.session_file = f".p4session_{self.session_id}.json"
        self._is_connected = False
        
        # Set up logger with session context
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # Add session filter to ensure session_id is included in logs
        for handler in logging.getLogger().handlers:
            for filter in handler.filters:
                if hasattr(filter, 'set_session_id'):
                    filter.set_session_id(self.session_id)

        env_set = True 
        
        # Prefer explicit MCP config values; otherwise defer to P4CONFIG / env
        if hasattr(self.config, 'p4port') and self.config.p4port:
            self.p4.port = self.config.p4port
        else:
            env_set = False
            self.logger.warning(
                'P4PORT not specified in MCP config; falling back to P4CONFIG file or environment variables'
            )

        if hasattr(self.config, 'p4user') and self.config.p4user:
            self.p4.user = self.config.p4user
        else:
            env_set = False
            self.logger.warning(
                'P4USER not specified in MCP config; falling back to P4CONFIG file or environment variables'
            )

        # Optional: client may intentionally be omitted for auto-discovery
        if hasattr(self.config, 'p4client') and self.config.p4client:
            self.p4.client = self.config.p4client

        # If any primary fields were missing, describe how remaining values are sourced
        if not env_set:
            p4config_path = self.p4.p4config_file
            if not p4config_path or p4config_path == 'noconfig':
                self.logger.warning(
                    'No P4CONFIG file detected; using only current process environment for unset values'
                )
            else:
                self.logger.info(f'Detected P4CONFIG file: {p4config_path}')

        # Summarize final connection parameters
        if self.p4.port and self.p4.user:
            self.logger.info(
                f'Using P4 connection parameters: P4PORT="{self.p4.port}", P4USER="{self.p4.user}"'
            )
        else:
            self.logger.warning(
                'P4PORT and/or P4USER still unset; Perforce connection may fail'
            )

        # Set program name and version for server logging
        self.p4.prog = "P4-MCP-Server"
        self.p4.version = __version__

    async def connect(self):
        """Establish P4 connection and record session"""
        try:
            self.logger.info(f"Connecting to P4 server")
            res = self.p4.connect()
            self.logger.info(f"P4 connection status: {res}")

            # Handle authentication if needed
            if self.p4.ticket_file:
                self.p4.run("login", "-s")

            info = self.p4.run("info")[0]
            server_version = info["serverVersion"].split(" ")[0]

            parts = server_version.split("/")
            self.config.p4version = f"{parts[2]}.{parts[3]}" if len(parts) >= 4 else None

            self._is_connected = True
            
            # Record session information
            self._record_session()
            return True
            
        except P4Exception as e:
            self.logger.error(f"P4Error: Failed to connect to P4 server: {e}")
            self._is_connected = False
            raise
    
    async def disconnect(self):
        """Disconnect P4 session and clean up"""
        if self._is_connected:
            try:
                if self.p4.connected():
                    self.p4.disconnect()
                logger.info(f"P4 session ended (Duration: {time.time() - self.start_time:.2f}s)")
            except P4Exception as e:
                logger.error(f"P4Error: Error ending P4 session: {e}")
            finally:
                self._is_connected = False
                self._cleanup_session()
    
    def _record_session(self):
        """Record and save session information"""
        # Get server info if connected
        server_info = {}
        if self._is_connected and self.p4.connected():
            try:
                server_info = self.p4.run('info')[0]
            except P4Exception:
                pass

        session_info = {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'config': self.config.to_dict(),
            'connection_info': {
                'server': self.p4.port,
                'user': self.p4.user,
                'client': getattr(self.p4, 'client', None),
                'connected': self._is_connected,
                'connection_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'server_info': server_info
            },
            'pid': os.getpid()
        }
        
        if self.save_to_file:
            try:
                with open(self.session_file, 'w') as f:
                    json.dump(session_info, f, indent=2, default=str)
                self.logger.debug(f"Session data saved to session file")
            except IOError as e:
                self.logger.error(f"Could not save session file: {e}")

        return session_info
    def _cleanup_session(self):
        """Clean up session resources"""
        if self.save_to_file and os.path.exists(self.session_file):
            try:
                os.remove(self.session_file)
            except OSError as e:
                logger.warning(f"Could not remove session file: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if the session is connected"""
        return self._is_connected and self.p4.connected()
    
    def __str__(self):
        return f"P4Session({self.session_id}, {self.p4.port}, {self.p4.user})"

class P4ConnectionManager:
    """Manages P4Python connections with session tracking and proper cleanup"""
    
    def __init__(self, config: Config, save_session_to_file: bool = False):
        """Initialize P4 connection manager
        
        Args:
            config: Configuration object with P4 connection details
            save_session_to_file: If True, saves session details to a file
        """
        self.config = config
        self._connection: Optional[P4] = None
        self._is_connected = False
        self._session = P4Session(config, save_to_file=save_session_to_file)
        self.session_id = self._session.session_id
    
    async def initialize(self):
        """Initialize P4 connection"""
        try:
            if not self._is_connected:
                self._connection = self._session.p4
                await self._session.connect()
                self._is_connected = True
            
        except P4Exception as e:
            logger.error(f"P4Error: Failed to connect to P4: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get P4 connection context manager"""
        if not self._is_connected and not self._connection:
            await self.initialize()
        
        try:
            # Verify connection is still valid
            if not self._connection.connected():
                self._connection.connect()

            if self._connection.ticket_file:
                self._connection.run("login", "-s")
            
            yield self._connection
            
        except P4Exception as e:
            logger.error(f"P4Error: P4 operation error: {e}")
            # Try to reconnect
            try:
                self._connection.disconnect()
                self._connection.connect()
            except:
                pass
            raise
    
    async def cleanup(self):
        """Cleanup P4 connection and session"""
        if self._is_connected:
            logger.info(f"Cleaning up P4 session")
            await self._session.disconnect()
        
        self._is_connected = False
        self._connection = None