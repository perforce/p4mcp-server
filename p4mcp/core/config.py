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
    log_dir: Optional[str] = None

    # SSL/TLS settings for Swarm API connections.
    # True = verify with default CA bundle, False = disable verification,
    # str = path to a custom CA certificate bundle (PEM).
    ssl_verify: Union[bool, str] = True

    # P4 connection-level result limits (applied to the live P4 object).
    # max_results caps how many rows the server returns per command; it ships
    # on by default with a generous value so runaway queries are bounded out of
    # the box. A value of 0 disables the limit (server default in effect).
    # max_scan_rows caps how many rows the server scans per command; it is
    # unset by default so admin/group policy governs scan limits.
    max_results: Optional[int] = 10000
    max_scan_rows: Optional[int] = None

    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from file or environment variables"""

        # Default configuration
        config_data = {
            "p4port": os.getenv("P4PORT"),
            "p4user": os.getenv("P4USER"),
            "p4client": os.getenv("P4CLIENT"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "log_dir": os.getenv("P4MCP_LOG_DIR"),
            "ssl_verify": cls._parse_ssl_verify(),
            "max_results": cls._parse_positive_int(
                "P4MCP_MAX_RESULTS", os.getenv("P4MCP_MAX_RESULTS"), default=10000
            ),
            "max_scan_rows": cls._parse_positive_int(
                "P4MCP_MAX_SCAN_ROWS", os.getenv("P4MCP_MAX_SCAN_ROWS"), default=None
            ),
        }
        config_data = {k: v for k, v in config_data.items() if v is not None}
        return cls(**config_data)

    @staticmethod
    def _parse_positive_int(
        env_name: str, raw: Any, default: Optional[int]
    ) -> Optional[int]:
        """Parse a non-negative integer option from a raw value.

        Validation lives here, in the option-parsing layer, so the server fails
        fast with a clear message at startup — before any P4 connection is
        attempted. Accepts either a raw environment string or an already-parsed
        value (e.g. a CLI override) so both option sources share one rule.

        Args:
            env_name: Name of the source option (for error text).
            raw: Raw value from the environment or CLI, or None if unset.
            default: Value to return when ``raw`` is None/empty.

        Returns:
            The parsed non-negative ``int``, or ``default`` when unset.

        Raises:
            ValueError: If ``raw`` is not an integer or is negative.
        """
        if raw is None:
            return default

        # Already-parsed integer (e.g. a CLI override) — short-circuit.
        if isinstance(raw, int) and not isinstance(raw, bool):
            if raw < 0:
                raise ValueError(
                    f"{env_name} must be a non-negative integer, got: {raw}"
                )
            return raw

        text = str(raw).strip()
        if text == "":
            return default

        try:
            value = int(text)
        except (TypeError, ValueError):
            raise ValueError(
                f"{env_name} must be a non-negative integer, got: {text!r}"
            )

        if value < 0:
            raise ValueError(
                f"{env_name} must be a non-negative integer, got: {value}"
            )

        return value

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
            "log_dir": self.log_dir,
            "ssl_verify": self.ssl_verify,
            "max_results": self.max_results,
            "max_scan_rows": self.max_scan_rows,
        }