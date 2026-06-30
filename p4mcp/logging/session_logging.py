"""
Session lifecycle for P4 MCP server telemetry.

The session wrappers drive the OpenTelemetry tracer-provider lifecycle:
``start_session`` initialises the provider and ``end_session`` force-flushes and
shuts it down. The public ``start_session``/``end_session`` signatures are kept
so ``main.py`` keeps working unchanged.
"""
import logging
import uuid
import threading
from typing import Optional

from p4mcp.telemetry.otel_setup import init_tracing, shutdown_tracing

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session state and the OpenTelemetry provider lifecycle."""

    def __init__(self):
        self._current_session_id: Optional[str] = None
        self._lock = threading.Lock()

    @property
    def current_session_id(self) -> Optional[str]:
        return self._current_session_id

    def start_session(
        self,
        session_id: Optional[str] = None,
        otel_console: bool = False,
        ca_bundle: Optional[str] = None,
    ) -> str:
        """Start a new telemetry session and initialise OTel tracing.

        Args:
            session_id: Optional explicit session id; a random id is generated
                when omitted.
            otel_console: Also export spans to the console (or with
                ``LOG_LEVEL=DEBUG``).
            ca_bundle: Optional fallback CA bundle path for the OTLP channel.

        Returns:
            The active session id.
        """
        with self._lock:
            if session_id is None:
                session_id = uuid.uuid4().hex[:16]

            self._current_session_id = session_id

            try:
                init_tracing(otel_console=otel_console, ca_bundle=ca_bundle)
                logger.info(f"Session started: {session_id}")
            except Exception as e:
                logger.error(f"Failed to start session {session_id}: {e}")
                raise

            return session_id

    def end_session(self, session_id: Optional[str] = None) -> None:
        """End a session: force-flush and shut down OTel tracing."""
        with self._lock:
            target_session_id = session_id or self._current_session_id
            if not target_session_id:
                return

            try:
                shutdown_tracing()
            except Exception as e:
                logger.error(f"Failed to shut down tracing for session {target_session_id}: {e}")

            logger.info(f"Session ended: {target_session_id}")

            if target_session_id == self._current_session_id:
                self._current_session_id = None


# Global instance
_session_manager = SessionManager()


# Public API
def start_session(
    session_id: Optional[str] = None,
    otel_console: bool = False,
    ca_bundle: Optional[str] = None,
) -> str:
    """Start a new session and initialise OTel tracing."""
    return _session_manager.start_session(
        session_id=session_id, otel_console=otel_console, ca_bundle=ca_bundle
    )


def end_session(session_id: Optional[str] = None) -> None:
    """End the current session and shut down OTel tracing."""
    _session_manager.end_session(session_id)


def get_current_session_id() -> Optional[str]:
    """Get current session ID"""
    return _session_manager.current_session_id
