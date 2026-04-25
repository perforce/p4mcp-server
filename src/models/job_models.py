"""Job query and modify models."""

from typing import Optional
from enum import Enum
from pydantic import Field, model_validator
from .common import BaseParams, PaginatedParams


class JobAction(str, Enum):
    LIST_JOBS = "list_jobs"
    GET_JOB = "get_job"


class JobModifyAction(str, Enum):
    LINK_JOB = "link_job"
    UNLINK_JOB = "unlink_job"


class QueryJobsParams(PaginatedParams):
    """Job query parameters."""
    action: JobAction = Field(
        description="Job query action",
        examples=["list_jobs", "get_job"]
    )
    changelist_id: Optional[str] = Field(
        default=None,
        description="Changelist ID - required for list_jobs action",
        examples=["job2345"]
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Job ID - required for get_job action",
        examples=["job67890"]
    )

    @model_validator(mode='after')
    def validate_changelist_id_required(self):
        """Validate changelist_id is provided when required."""
        if self.action == JobAction.LIST_JOBS and not self.changelist_id:
            raise ValueError('changelist_id is required for list_jobs action')
        return self

    @model_validator(mode='after')
    def validate_job_id_required(self):
        """Validate job_id is provided when required."""
        if self.action == JobAction.GET_JOB and not self.job_id:
            raise ValueError('job_id is required for get_job action')
        return self


class ModifyJobsParams(BaseParams):
    action: JobModifyAction = Field(
        description="Job modification action",
        examples=["link_job", "unlink_job"]
    )
    changelist_id: str = Field(
        default=None,
        description="Changelist ID - required for link_job/unlink_job actions",
        examples=["12345"]
    )
    job_id: str = Field(
        default=None,
        description="Job ID - required for link_job/unlink_job actions",
        examples=["job67890"]
    )

    @model_validator(mode='after')
    def validate_changelist_id_and_job_id(self):
        """Validate changelist_id and job_id are provided when required."""
        if not self.changelist_id and not self.job_id and self.action in ["link_job", "unlink_job"]:
            raise ValueError(f"changelist_id and job_id are required for this {self.action} action")
        return self
