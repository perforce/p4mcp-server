def handle_errors(func):
    async def wrapper(self, params):
        try:
            return await func(self, params)
        except Exception as e:
            action = getattr(params, "action", None)
            resp = {"status": "error", "message": str(e)}
            if action is not None:
                resp["action"] = action
            return resp
    return wrapper