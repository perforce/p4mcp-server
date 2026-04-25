"""
Configuration management for P4 MCP server
"""
import os
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Configuration for P4 MCP server"""
    
    # P4 connection settings
    p4port: Optional[str] = None
    p4user: Optional[str] = None
    p4client: Optional[str] = None

    # Tool settings
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL, OFF, QUIET

    # SSL/TLS settings for Swarm API connections.
    # True = verify with default CA bundle, False = disable verification,
    # str = path to a custom CA certificate bundle (PEM).
    ssl_verify: Union[bool, str] = True

    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from file or environment variables"""
        
        # Default configuration
        config_data = {
            "p4port": os.getenv("P4PORT"),
            "p4user": os.getenv("P4USER"),
            "p4client": os.getenv("P4CLIENT"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "ssl_verify": cls._parse_ssl_verify(),
        }
        config_data = {k: v for k, v in config_data.items() if v is not None}
        return cls(**config_data)

    @staticmethod
    def _parse_ssl_verify() -> Union[bool, str]:
        """Parse SSL verification settings from environment variables.

        Priority order:
        1. P4MCP_CA_BUNDLE – path to a custom CA certificate bundle (PEM).
        2. P4MCP_SSL_VERIFY – "true" (default) or "false".

        Returns:
            str path, True, or False.
        """
        ca_bundle = os.getenv("P4MCP_CA_BUNDLE")
        if ca_bundle:
            if os.path.isfile(ca_bundle):
                logger.info("Using custom CA bundle for Swarm SSL: %s", ca_bundle)
                return ca_bundle
            logger.warning("P4MCP_CA_BUNDLE path does not exist: %s — ignoring", ca_bundle)

        ssl_flag = os.getenv("P4MCP_SSL_VERIFY", "true").strip().lower()
        if ssl_flag == "false":
            logger.info("Swarm SSL verification disabled via P4MCP_SSL_VERIFY=false")
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "p4port": self.p4port,
            "p4user": self.p4user,
            "p4client": self.p4client,
            "log_level": self.log_level,
            "ssl_verify": self.ssl_verify,
        }