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