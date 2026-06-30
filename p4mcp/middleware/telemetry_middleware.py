"""FastMCP middleware that emits one OpenTelemetry span per tool call.

Registered outermost (ahead of ``CheckPermissionMiddleware``) and only when
telemetry consent is granted. Each ``on_call_tool`` starts exactly one
SERVER-kind span carrying the OTel MCP semantic-convention attributes, parents
it to any inbound trace context, and on failure marks the span ERROR with an
``error.type`` drawn from the taxonomy — without ever recording raw error
messages, tool arguments, tool results, resource URLs or resource contents.
"""
import logging
from typing import Optional, Tuple

from fastmcp.server.middleware import Middleware, MiddlewareContext
from opentelemetry.trace import SpanKind, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from ..telemetry.otel_setup import (
    categorize_error,
    get_tracer,
    record_span_and_maybe_flush,
)

logger = logging.getLogger(__name__)

# OTel gen_ai semantic-convention operation name for tool execution.
OPERATION_NAME = "execute_tool"

# W3C trace-context keys honoured from inbound requests.
_TRACE_KEYS = ("traceparent", "tracestate")


class TelemetryMiddleware(Middleware):
    """Emit one OTel SERVER span per tool call with MCP semconv attributes."""

    def __init__(self) -> None:
        super().__init__()
        self._propagator = TraceContextTextMapPropagator()

    def _build_carrier(self, context: MiddlewareContext) -> dict:
        """Collect W3C trace-context headers from the request.

        For stdio requests the keys arrive on ``_meta`` (``traceparent`` /
        ``tracestate``); for HTTP requests they arrive as W3C headers.

        Args:
            context: The middleware context for the tool call.

        Returns:
            A carrier dict suitable for the W3C propagator (may be empty).
        """
        carrier: dict = {}

        meta = getattr(context.message, "meta", None)
        if meta is not None:
            extra = getattr(meta, "model_extra", None) or {}
            for key in _TRACE_KEYS:
                value = extra.get(key)
                if value:
                    carrier[key] = value

        try:
            from fastmcp.server.dependencies import get_http_headers

            headers = get_http_headers() or {}
            for key in _TRACE_KEYS:
                if key not in carrier and headers.get(key):
                    carrier[key] = headers[key]
        except Exception:  # pragma: no cover - no active HTTP request
            pass

        return carrier

    def _extract_parent_context(self, context: MiddlewareContext):
        """Extract the parent OTel context from inbound trace metadata.

        Returns a context parented to the inbound trace when present, otherwise a
        context that yields a root span.
        """
        return self._propagator.extract(carrier=self._build_carrier(context))

    @staticmethod
    def _client_info(context: MiddlewareContext) -> Tuple[Optional[str], Optional[str]]:
        """Return ``(client_name, client_version)`` from the MCP session, if any."""
        try:
            client_info = context.fastmcp_context.session.client_params.clientInfo
            return client_info.name, client_info.version
        except Exception:
            return None, None

    @staticmethod
    def _result_error(result) -> Optional[dict]:
        """Return the structured error dict from a tool result, or ``None``.

        Handlers return ``{"status": "error", "code": ..., "error": ...}``; the
        payload may be nested under a ``result`` key by FastMCP.
        """
        structured = getattr(result, "structured_content", None)
        if not isinstance(structured, dict):
            return None
        # FastMCP-specific shape: a bare dict return may be nested under a
        # "result" key. If that wrapping ever changes we fall back to treating
        # the structured content itself as the payload (and a non-matching shape
        # simply yields no error — the span stays OK rather than crashing).
        payload = structured.get("result") if isinstance(structured.get("result"), dict) else structured
        if isinstance(payload, dict) and payload.get("status") == "error":
            return payload
        return None

    def _mark_error(self, span, error_msg: Optional[str], code: Optional[str]) -> None:
        """Mark a span as failed with an ``error.type`` taxonomy value.

        Only the taxonomy category is recorded — never the raw message/code.
        """
        span.set_attribute("error.type", categorize_error(error_msg, code))
        span.set_status(Status(StatusCode.ERROR))

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Wrap the tool call in a SERVER-kind span and export it."""
        tracer = get_tracer()
        if tracer is None:
            # Tracing not initialised (consent off) — export nothing.
            return await call_next(context)

        tool_name = context.message.name
        parent_context = self._extract_parent_context(context)

        attributes = {
            "mcp.method.name": context.method or "tools/call",
            "gen_ai.tool.name": tool_name,
            "gen_ai.operation.name": OPERATION_NAME,
        }
        client_name, client_version = self._client_info(context)
        if client_name:
            attributes["mcp.client.name"] = client_name
        if client_version:
            attributes["mcp.client.version"] = client_version

        span = tracer.start_span(
            name=f"{OPERATION_NAME} {tool_name}",
            context=parent_context,
            kind=SpanKind.SERVER,
            attributes=attributes,
        )
        try:
            result = await call_next(context)
        except Exception as exc:
            self._mark_error(span, str(exc), getattr(exc, "code", None))
            span.end()
            record_span_and_maybe_flush()
            raise
        else:
            error = self._result_error(result)
            if error is not None:
                self._mark_error(span, error.get("error"), error.get("code"))
            span.end()
            record_span_and_maybe_flush()
            return result
