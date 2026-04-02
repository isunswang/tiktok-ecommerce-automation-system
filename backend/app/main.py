"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.redis import close_redis

logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()
    app.state.settings = settings
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")
    yield
    logger.info("Shutting down...")
    await close_redis()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="TikTok跨境电商全自动运营系统",
        description="TikTok Cross-border E-commerce Automated Operation System API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if get_settings().debug else None,
        redoc_url="/redoc" if get_settings().debug else None,
    )

    # CORS
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Health check
    @app.get("/v1/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "version": "0.1.0",
            "environment": settings.app_env,
        }

    # Register API routers
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
