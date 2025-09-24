"""
P4 Server services layer
Services for tools:
- get_server_info
- get_current_user
"""
import logging
from typing import List, Dict, Any, Optional
from P4 import P4Exception

from ..core.connection import P4ConnectionManager

logger = logging.getLogger(__name__)

class ServerServices:
    """Server services for server operations"""
    
    def __init__(self, connection_manager: P4ConnectionManager):
        self.connection_manager = connection_manager

    async def get_server_info(self) -> Dict[str, Any]:
        """Get information about the Perforce/P4 server"""
        async with self.connection_manager.get_connection() as p4:
            try:
                server_info = p4.run("info")
                print(server_info[0])
                return {"status": "success", "message": {k: v for k, v in server_info[0].items() if isinstance(v, str)}}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get server info: {e}")
                return {"status": "error", "message": str(e)}

    async def get_current_user(self) -> Dict[str, Any]:
        """Get information about the current user"""
        async with self.connection_manager.get_connection() as p4:
            try:
                user_info = p4.run("user", "-o")
                if not user_info:
                    raise ValueError("Current user not found")
                return {"status": "success", "message": {k: v for k, v in user_info[0].items() if isinstance(v, str)}}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get current user: {e}")
                return {"status": "error", "message": str(e)}