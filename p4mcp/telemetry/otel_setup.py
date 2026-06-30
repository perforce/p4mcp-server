"""OpenTelemetry tracing setup for P4 MCP server telemetry.

Builds a ``TracerProvider`` that exports tool-call spans over OTLP/gRPC to the
shared Perforce collector, using OTel MCP semantic-convention attribute names so
telemetry can be dashboarded consistently across Perforce products.

``OTEL_EXPORTER_OTLP_ENDPOINT`` overrides the built-in collector endpoint.
``OTEL_EXPORTER_OTLP_PROTOCOL`` is read for awareness; only ``grpc`` is
supported — unsupported values emit a warning and fall back to grpc.

TLS verifies via the system trust store, independent of ``P4MCP_TLS_*`` /
``--ca-bundle``; ``--ca-bundle`` acts only as a channel-only fallback CA when no
OTel certificate is configured in-code.
"""
import logging
import os
import sys
import threading
from typing import Optional, Sequence

import grpc
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
    SpanExportResult,
)

from .._version import __version__

logger = logging.getLogger(__name__)

DEFAULT_OTLP_ENDPOINT = "https://grpc.public.prd.shared.perforce.com"
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", DEFAULT_OTLP_ENDPOINT)

# Only gRPC is supported (opentelemetry-exporter-otlp-proto-grpc).
# Read the standard var for awareness; unsupported values are warned about in
# init_tracing() where logging is already configured.
OTLP_PROTOCOL = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc").strip().lower() or "grpc"

SERVICE_NAME = "p4-mcp-server"

# Force-flush after this many tool-call spans so spans are not held indefinitely
# in long-running or low-traffic sessions.
FLUSH_INTERVAL = 100

# In-code OTel certificate (PEM bytes). ``None`` means "use the system trust
# store"; when set it takes precedence over the ``--ca-bundle`` fallback.
_OTEL_CERT: Optional[bytes] = None

# Error taxonomy exposed on spans via the ``error.type`` attribute (AC-2).
ERROR_TIMEOUT = "timeout"
ERROR_AUTH_FAILED = "auth_failed"
ERROR_RATE_LIMITED = "rate_limited"
ERROR_NOT_FOUND = "not_found"
ERROR_TOOL_ERROR = "tool_error"

# P4/handler error codes mapped directly to the taxonomy.
_CODE_TAXONOMY = {
    "P4_CONNECTION_ERROR": ERROR_TIMEOUT,
    "P4_ACCESS_DENIED": ERROR_AUTH_FAILED,
}


def categorize_error(error_msg: Optional[str] = None, code: Optional[str] = None) -> str:
    """Map a P4/handler error into the span ``error.type`` taxonomy.

    The taxonomy values are ``timeout``, ``auth_failed``, ``rate_limited``,
    ``not_found`` and ``tool_error``. The structured error ``code`` (when one is
    available) is consulted first, then the raw message is keyword-matched.

    Args:
        error_msg: Raw error message. Used only for classification — it is never
            written to a span attribute.
        code: Structured error code (e.g. ``P4_ACCESS_DENIED``) when available.

    Returns:
        One of the taxonomy strings; defaults to ``tool_error``.
    """
    code_norm = (code or "").upper()
    if code_norm in _CODE_TAXONOMY:
        return _CODE_TAXONOMY[code_norm]

    text = f"{code or ''} {error_msg or ''}".lower()

    # Checks run from most specific to most general and short-circuit on the
    # first match, so unambiguous intent words win over the broad connection
    # keywords that fall back to ``timeout`` last.
    if any(kw in text for kw in ("timeout", "timed out", "deadline")):
        return ERROR_TIMEOUT
    if any(kw in text for kw in ("permission", "access", "login", "authenticat", "credential", "password", "ticket", "denied", "unauthor", "forbidden")):
        return ERROR_AUTH_FAILED
    if any(kw in text for kw in ("rate limit", "too many", "throttle", "maxresults", "maxscanrows", "quota")):
        return ERROR_RATE_LIMITED
    if any(kw in text for kw in ("not found", "no such", "does not exist", "no file(s)", "nonexistent")):
        return ERROR_NOT_FOUND
    # Connection-level failures fall back to the closest taxonomy bucket.
    if any(kw in text for kw in ("connect", "unreachable", "socket")):
        return ERROR_TIMEOUT
    return ERROR_TOOL_ERROR


def _debug_logging_enabled() -> bool:
    """Return True when ``LOG_LEVEL=DEBUG`` is set in the environment.

    The env var is read directly rather than via ``logger.isEnabledFor(DEBUG)``
    because ``setup_logging`` configures the root logger at a fixed ``INFO``
    level; AC-4 keys console span export off the ``LOG_LEVEL`` env var itself.
    """
    return os.environ.get("LOG_LEVEL", "").upper() == "DEBUG"


def _build_grpc_credentials(ca_bundle: Optional[str] = None) -> grpc.ChannelCredentials:
    """Build gRPC channel credentials for the OTLP exporter.

    Verification uses the system trust store by default. An in-code OTel
    certificate (``_OTEL_CERT``) takes precedence; ``ca_bundle`` is honoured only
    as a channel-only fallback CA when no in-code certificate is configured.

    Args:
        ca_bundle: Optional path to a PEM CA bundle used as a fallback CA.

    Returns:
        gRPC channel credentials.
    """
    if _OTEL_CERT is not None:
        return grpc.ssl_channel_credentials(root_certificates=_OTEL_CERT)
    if ca_bundle:
        try:
            with open(ca_bundle, "rb") as cert_file:
                return grpc.ssl_channel_credentials(root_certificates=cert_file.read())
        except OSError as exc:
            logger.warning("Failed to read OTel fallback CA bundle %s: %s", ca_bundle, exc)
    # No explicit roots → gRPC verifies against the system trust store.
    return grpc.ssl_channel_credentials()


class LoggingOTLPSpanExporter(OTLPSpanExporter):
    """OTLP/gRPC exporter that logs the per-batch export outcome.

    ``BatchSpanProcessor`` exports on a background thread and discards the
    ``SpanExportResult``. OTLP/gRPC returns no response body, so the only
    available health signal is SUCCESS/FAILURE — this subclass surfaces it to
    the module logger. Only the span count and result are logged, never span
    contents.
    """

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export ``spans`` and log the outcome (count + result only)."""
        result = super().export(spans)
        if result == SpanExportResult.SUCCESS:
            logger.debug("OTLP export ok: %d spans (endpoint=%s)", len(spans), OTLP_ENDPOINT)
        else:
            logger.warning("OTLP export FAILED: %d spans (endpoint=%s)", len(spans), OTLP_ENDPOINT)
        return result


def _create_otlp_exporter(ca_bundle: Optional[str] = None) -> SpanExporter:
    """Create the OTLP/gRPC span exporter pointed at the fixed in-code endpoint.

    Args:
        ca_bundle: Optional fallback CA bundle path (see ``_build_grpc_credentials``).

    Returns:
        A configured ``LoggingOTLPSpanExporter``.
    """
    return LoggingOTLPSpanExporter(
        endpoint=OTLP_ENDPOINT,
        credentials=_build_grpc_credentials(ca_bundle),
    )


class TracingManager:
    """Owns the OTel ``TracerProvider`` lifecycle for the current session."""

    def __init__(self) -> None:
        self._provider: Optional[TracerProvider] = None
        self._tracer = None
        self._span_count = 0
        self._lock = threading.Lock()

    def init_tracing(self, otel_console: bool = False, ca_bundle: Optional[str] = None) -> None:
        """Initialise the tracer provider and its span processors.

        Idempotent: a second call while a provider is already active is a no-op.

        Args:
            otel_console: When True (or ``LOG_LEVEL=DEBUG``), also export spans to
                the console; default runs export only over OTLP/gRPC.
            ca_bundle: Optional fallback CA bundle path for the OTLP channel.
        """
        with self._lock:
            if self._provider is not None:
                return

            if OTLP_PROTOCOL != "grpc":
                logger.warning(
                    "OTEL_EXPORTER_OTLP_PROTOCOL=%r is not supported; only 'grpc' is available. Using grpc.",
                    OTLP_PROTOCOL,
                )

            resource = Resource.create({
                "service.name": SERVICE_NAME,
                "service.version": __version__,
            })
            provider = TracerProvider(resource=resource)
            provider.add_span_processor(BatchSpanProcessor(_create_otlp_exporter(ca_bundle)))

            if otel_console or _debug_logging_enabled():
                # stdout is the MCP JSON-RPC channel on the stdio transport;
                # console spans must go to stderr or they corrupt the protocol.
                provider.add_span_processor(
                    BatchSpanProcessor(ConsoleSpanExporter(out=sys.stderr))
                )

            self._provider = provider
            self._tracer = provider.get_tracer(SERVICE_NAME, __version__)
            self._span_count = 0
            logger.info("OpenTelemetry tracing initialised (endpoint=%s)", OTLP_ENDPOINT)

    def get_tracer(self):
        """Return the active tracer, or ``None`` when tracing is not initialised."""
        return self._tracer

    def record_span_and_maybe_flush(self) -> None:
        """Count an exported span and force-flush every ``FLUSH_INTERVAL`` spans."""
        with self._lock:
            self._span_count += 1
            if self._span_count >= FLUSH_INTERVAL:
                self._span_count = 0
                if self._provider is not None:
                    try:
                        flushed = self._provider.force_flush()
                        if flushed:
                            logger.debug("Span force-flush ok (every %d spans)", FLUSH_INTERVAL)
                        else:
                            logger.warning(
                                "Span force-flush timed out (every %d spans)", FLUSH_INTERVAL
                            )
                    except Exception as exc:  # pragma: no cover - defensive
                        logger.warning("Span force-flush failed: %s", exc)

    def shutdown_tracing(self) -> None:
        """Force-flush and shut down the tracer provider on session end."""
        with self._lock:
            if self._provider is None:
                return
            try:
                flushed = self._provider.force_flush()
                if flushed:
                    logger.debug("Span force-flush ok (session end)")
                else:
                    logger.warning("Span force-flush timed out (session end)")
                self._provider.shutdown()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Tracer provider shutdown failed: %s", exc)
            finally:
                self._provider = None
                self._tracer = None
                self._span_count = 0


# Global instance + public module-level API.
_tracing_manager = TracingManager()


def init_tracing(otel_console: bool = False, ca_bundle: Optional[str] = None) -> None:
    """Initialise OTel tracing for the current session."""
    _tracing_manager.init_tracing(otel_console=otel_console, ca_bundle=ca_bundle)


def get_tracer():
    """Return the active tracer, or ``None`` when tracing is not initialised."""
    return _tracing_manager.get_tracer()


def record_span_and_maybe_flush() -> None:
    """Count an exported span and force-flush every ``FLUSH_INTERVAL`` spans."""
    _tracing_manager.record_span_and_maybe_flush()


def shutdown_tracing() -> None:
    """Force-flush and shut down OTel tracing for the current session."""
    _tracing_manager.shutdown_tracing()
