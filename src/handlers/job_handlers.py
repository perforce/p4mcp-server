"""Job query and modify handlers."""

import logging
from .utils import handle_errors

logger = logging.getLogger(__name__)


class JobsHandlers:

    def __init__(self, job_services):
        self.job_services = job_services

    @handle_errors
    async def _handle_query_jobs(self, params):
        if not params.changelist_id and params.action == "list_jobs":
            logger.error(f"changelist_id is required for this {params.action} action")
            raise ValueError(f"changelist_id is required for this {params.action} action")
        if not params.job_id and params.action == "get_job":
            logger.error(f"job_id is required for this {params.action} action")
            raise ValueError(f"job_id is required for this {params.action} action")

        if params.action == "list_jobs":
            result = await self.job_services.list_jobs_from_changelist(params.changelist_id, params.max_results)
        elif params.action == "get_job":
            result = await self.job_services.get_job_details(params.job_id)
        else:
            logger.error(f"Unknown job query action: {params.action}")
            raise ValueError(f"Unknown job query action: {params.action}")
        return {"status": result["status"], "action": params.action, "message": result["message"]}

    @handle_errors
    async def _handle_modify_jobs(self, params):
        if not params.changelist_id and not params.job_id and params.action in ["link_job", "unlink_job"]:
            logger.error(f"changelist_id and job_id are required for this {params.action} action")
            raise ValueError(f"changelist_id and job_id are required for this {params.action} action")
        if params.action == "link_job":
            result = await self.job_services.link_job_to_changelist(params.changelist_id, params.job_id)
        elif params.action == "unlink_job":
            result = await self.job_services.unlink_job_from_changelist(params.changelist_id, params.job_id)
        else:
            logger.error(f"Unknown job modify action: {params.action}")
            raise ValueError(f"Unknown job modify action: {params.action}")
        return {"status": result["status"], "action": params.action, "message": result["message"]}
