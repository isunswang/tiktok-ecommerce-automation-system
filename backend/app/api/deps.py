"""Common API dependencies."""

from typing import Annotated

from fastapi import Depends, Query, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

# Re-export common dependencies
DbSession = Annotated[AsyncSession, Depends(get_db)]

# Security scheme
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user from JWT token (placeholder implementation)."""
    # TODO: Implement actual JWT token validation
    # For now, return a placeholder user ID
    return "current_user_placeholder"


# Type alias for current user dependency
CurrentUser = Annotated[str, Depends(get_current_user)]


class PaginationParams:
    """Common pagination parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
