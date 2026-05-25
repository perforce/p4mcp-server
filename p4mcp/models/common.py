"""Base models and shared enums used across all resource-specific model modules."""

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# =============================================================================
# SHARED ENUMS
# =============================================================================

class ResolveMode(str, Enum):
    AUTO = "auto"       # -am
    SAFE = "safe"       # -as
    FORCE = "force"     # -af
    PREVIEW = "preview" # -n
    THEIRS = "theirs"   # -at
    YOURS = "yours"     # -ay


# =============================================================================
# BASE MODELS WITH COMMON PATTERNS
# =============================================================================

class BaseParams(BaseModel):
    """Base class for all parameter models with common configuration."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
        use_enum_values=True
    )


class PaginatedParams(BaseParams):
    """Base class for paginated queries."""
    max_results: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results to return"
    )
