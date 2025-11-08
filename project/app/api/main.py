"""
FastAPI main application (TASK-029).

Creates and configures the FastAPI application with all routes,
middleware, and error handlers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse  # noqa: E501

from app.api.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from app.api.routes import documents, health, ingestion, query, trends
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.

    Handles startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info(
        f"FastAPI application starting: "
        f"title={config.api_title}, version={config.api_version}"
    )
    logger.info(f"API server will run on {config.api_host}:{config.api_port}")
    if config.api_key:
        logger.info("API key authentication enabled")
    else:
        logger.warning("API key authentication disabled (no API_KEY configured)")

    yield

    # Shutdown
    logger.info("FastAPI application shutting down")


# Create FastAPI application
app = FastAPI(
    title=config.api_title,
    version=config.api_version,
    description="RESTful API for Financial Research Assistant RAG system",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
cors_origins = (
    config.api_cors_origins.split(",") if config.api_cors_origins != "*" else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(query.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(trends.router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root() -> dict:
    """
    Root endpoint with API information.

    Returns:
        API information and links
    """
    return {
        "name": config.api_title,
        "version": config.api_version,
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "query": "/api/v1/query",
            "ingest": "/api/v1/ingest",
            "documents": "/api/v1/documents",
            "health": "/api/v1/health",
            "metrics": "/api/v1/health/metrics",
            "trends": "/api/v1/trends",
        },
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.

    Args:
        request: FastAPI request object
        exc: Exception that was raised

    Returns:
        JSON error response
    """
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}: {str(exc)}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": (
                str(exc)
                if config.log_level == "DEBUG"
                else "An unexpected error occurred"
            ),
        },
    )
