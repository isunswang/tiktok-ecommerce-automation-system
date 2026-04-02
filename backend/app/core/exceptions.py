"""Custom exceptions and global exception handlers for FastAPI."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: int = 400, detail: str | None = None):
        self.message = message
        self.code = code
        self.detail = detail
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, resource: str = "Resource", detail: str | None = None):
        super().__init__(
            message=f"{resource} not found",
            code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class PermissionDeniedError(AppException):
    """Insufficient permissions."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            code=status.HTTP_403_FORBIDDEN,
        )


class ConflictError(AppException):
    """Resource conflict (e.g. duplicate)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            message=message,
            code=status.HTTP_409_CONFLICT,
        )


class ExternalAPIError(AppException):
    """Error calling external API (TikTok/1688)."""

    def __init__(self, service: str, detail: str | None = None):
        super().__init__(
            message=f"External API error: {service}",
            code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.code,
            content={
                "code": exc.code,
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "message": "Internal server error",
                "detail": str(exc) if app.state.settings.debug else None,
            },
        )
