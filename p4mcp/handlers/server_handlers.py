"""Server query handlers."""

import logging
from .utils import handle_errors

logger = logging.getLogger(__name__)


class ServerHandlers:

    def __init__(self, server_services):
        self.server_services = server_services

    @handle_errors
    async def _handle_query_server(self, params):
        if params.action == "server_info":
            result = await self.server_services.get_server_info()
        elif params.action == "current_user":
            result = await self.server_services.get_current_user()
        else:
            logger.error(f"Unknown server query action: {params.action}")
            raise ValueError(f"Unknown server query action: {params.action}")
        return {"status": "success", "action": params.action, "data": result}
