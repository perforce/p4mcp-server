# P4Python message severity at or above which a P4Exception is raised under
# exception_level=1. P4 severities: 0=E_EMPTY/E_INFO, 1=E_WARN, 2 (also warning),
# 3=E_FAILED, 4=E_FATAL. Only severities >= E_FAILED represent genuine failures.
E_FAILED = 3


def collect_warnings(p4) -> list:
    """Collect benign P4 info/warning messages from a connection.

    Under ``exception_level=1`` the P4Python connection no longer raises for
    info/warning outcomes (e.g. "file(s) up-to-date", "not on client"); those
    messages instead accumulate on ``p4.messages``. This helper extracts the
    text of the non-error messages so callers can surface them in an additive
    ``warnings`` field rather than misreading them as failures.

    Args:
        p4: Live P4 connection object exposing a ``messages`` sequence of
            ``P4Message`` objects (each with a ``.severity`` attribute).

    Returns:
        List of message texts for messages whose severity is in the warning
        range ``0 < severity < E_FAILED`` (i.e. 1..2). Severity 0 (info/empty)
        and severity >= E_FAILED (genuine failures) are dropped. Returns an
        empty list when ``p4.messages`` is empty or absent.
    """
    messages = getattr(p4, "messages", None) or []
    warnings = []
    for message in messages:
        severity = getattr(message, "severity", 0)
        if 0 < severity < E_FAILED:
            warnings.append(str(message))
    return warnings


def classify_p4_error(error_msg: str) -> str:
    """Classify P4Exception by keyword matching.

    Returns:
        Error code: P4_CONNECTION_ERROR, P4_ACCESS_DENIED, or P4_INVALID_INPUT
    """
    msg_lower = str(error_msg).lower()

    # Connection errors
    if any(kw in msg_lower for kw in ["connect", "connection", "tcp", "socket", "port", "unreachable"]):
        return "P4_CONNECTION_ERROR"

    # Access/permission errors
    if any(kw in msg_lower for kw in ["permission", "access", "login", "authenticat", "credential", "password", "ticket"]):
        return "P4_ACCESS_DENIED"

    # Default to invalid input
    return "P4_INVALID_INPUT"


def handle_errors(func):
    async def wrapper(self, params):
        try:
            return await func(self, params)
        except Exception as e:
            # Check if it's a P4Exception
            from P4 import P4Exception

            action = getattr(params, "action", None)

            if isinstance(e, P4Exception):
                # Structured error for P4 exceptions
                error_code = classify_p4_error(str(e))
                resp = {
                    "status": "error",
                    "code": error_code,
                    "error": str(e)
                }
            else:
                # Generic error for other exceptions
                resp = {
                    "status": "error",
                    "code": "UNKNOWN_ERROR",
                    "error": str(e)
                }

            if action is not None:
                resp["action"] = action
            return resp
    return wrapper