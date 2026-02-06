"""FastAPI application entry point for Power BI Semantic Modeling Agent.

This module provides the main FastAPI application with:
- Health check endpoint
- Agent invocation endpoint
- Application Insights telemetry
- Lifecycle management (startup/shutdown)
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from ..core.config import settings
from ..core.logging import setup_logging, get_logger


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager.
    
    Handles startup and shutdown:
    - Startup: Initialize logging, validate configuration
    - Shutdown: Cleanup resources, flush telemetry
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None during application runtime
    """
    # Startup
    logger.info(
        "Starting Power BI Semantic Modeling Agent",
        extra={
            "version": settings.version,
            "environment": settings.environment,
            "foundry_project_id": settings.foundry_project_id,
        }
    )
    
    # Validate required configuration
    if not settings.foundry_project_id:
        logger.error("FOUNDRY_PROJECT_ID is required but not set")
        raise ValueError("FOUNDRY_PROJECT_ID environment variable is required")
    
    logger.info("Agent startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down agent gracefully")


# Create FastAPI application
app = FastAPI(
    title="Power BI Semantic Modeling Agent",
    description=(
        "Azure AI Foundry agent for automated semantic model generation and deployment. "
        "Provides AI-driven analysis of data schemas and automated creation of "
        "Power BI semantic models with best-practice modeling patterns."
    ),
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument with OpenTelemetry for Application Insights
FastAPIInstrumentor.instrument_app(app)


# Import routers after app creation to avoid circular imports
from . import health  # noqa: E402

app.include_router(health.router, tags=["Health"])


# Development server entry point
if __name__ == "__main__":
    import uvicorn
    
    setup_logging()
    
    logger.info(
        f"Starting development server on {settings.host}:{settings.port}",
        extra={"dry_run": settings.dry_run_enabled}
    )
    
    uvicorn.run(
        "src.agent.__main__:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
