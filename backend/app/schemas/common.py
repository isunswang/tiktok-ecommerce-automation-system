"""Pydantic schemas for common types."""

from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel):
    """Standard paginated response."""
    items: list = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class ErrorResponse(BaseModel):
    """Standard error response."""
    code: int = 400
    message: str = ""
    detail: str | None = None
