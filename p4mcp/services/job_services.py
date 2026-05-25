"""
P4 changelist services layer

Read service for tools:
- get_change_jobs : Get jobs from changelist
- get_job_details : Get details of a specific job

Write service for tools:
- link_changelist_to_job : Link changelist to job
- unlink_changelist_from_job : Unlink changelist from job

"""

import logging
from typing import Dict, Any
from P4 import P4Exception
from .changelist_services import ChangelistServices

from ..core.connection import P4ConnectionManager

logger = logging.getLogger(__name__)

class JobServices:
    """Job services for job operations"""

    def __init__(self, connection_manager: P4ConnectionManager):
        self.connection_manager = connection_manager

    async def list_jobs_from_changelist(self, changelist_id: str, limit: int=50) -> Dict[str, Any]:
        """Get jobs associated with a specific changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if not changelist_id:
                    raise ValueError(f"Changelist '{changelist_id}' not found")
                if changelist_id and changelist_id == "default":
                    raise ValueError("Cannot get jobs for default changelist")
                if not await ChangelistServices.verify_changelist(p4, changelist_id):
                    raise ValueError(f"Changelist '{changelist_id}' does not exist or is not valid for update")
                result = p4.run("fixes", f"-m{limit}", "-c", changelist_id)
                return {"status": "success", "message": result}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get jobs for changelist '{changelist_id}': {e}")
                return {"status": "error", "message": "Failed to get jobs for changelist"}

    async def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get details of a specific job"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if not job_id:
                    raise ValueError("No job ID provided")
                result = p4.run("job", "-o", job_id)
                return {"status": "success", "message": {k: v for k, v in result[0].items()}}
            except P4Exception as e:
                logger.error(f"P4Error: Failed to get job details '{job_id}': {e}")
                return {"status": "error", "message": str(e)}

    async def link_job_to_changelist(self, changelist_id: str, job_id: str) -> None:
        """Link a changelist to a job"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if not await ChangelistServices.verify_changelist(p4, changelist_id):
                    raise ValueError(f"Changelist '{changelist_id}' does not exist or is not valid for update")
                if not job_id:
                    raise ValueError("No job ID provided to link to changelist")
                
                changelist = p4.fetch_change(changelist_id)
                if 'Jobs' not in changelist:
                    changelist._jobs = []
                if job_id not in changelist._jobs:
                    changelist._jobs.append(job_id)
                    result = p4.save_change(changelist)
                    return {"status": "success", "message": result}
                else:
                    raise ValueError(f"Job '{job_id}' is already linked to changelist '{changelist_id}'")
            except P4Exception as e:
                logger.error(f"P4Error: Failed to link changelist '{changelist_id}' to job '{job_id}': {e}")
                return {"status": "error", "message": str(e)}

    async def unlink_job_from_changelist(self, changelist_id: str, job_id: str) -> None:
        """Unlink a job from a changelist"""
        async with self.connection_manager.get_connection() as p4:
            try:
                if not await ChangelistServices.verify_changelist(p4, changelist_id):
                    raise ValueError(f"Changelist '{changelist_id}' does not exist or is not valid for update")
                if not job_id:
                    raise ValueError("No job ID provided to unlink from changelist")
                changelist = p4.fetch_change(changelist_id)
                if 'Jobs' in changelist and job_id in changelist._jobs:
                    changelist._jobs.remove(job_id)
                    result = p4.save_change(changelist)
                    return {"status": "success", "message": result}
                else:
                    raise ValueError(f"Job '{job_id}' is not linked to changelist '{changelist_id}'")
                
            except P4Exception as e:
                logger.error(f"P4Error: Failed to unlink changelist '{changelist_id}' from job '{job_id}': {e}")
                return {"status": "error", "message": str(e)}