"""Health check endpoint for Power BI Semantic Modeling Agent.

Provides health status with startup validation and dependency checks.
"""

import platform
from datetime import datetime, timezone
from typing import Dict, Any, Literal

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
import psutil

from ..core.config import settings
from ..core.logging import get_logger


logger = get_logger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model.
    
    Provides comprehensive health status including:
    - Overall health status
    - Agent version and environment
    - System resource utilization
    - Configuration validation
    - Timestamp
    """
    
    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        description="Overall health status"
    )
    version: str = Field(
        description="Agent version"
    )
    environment: str = Field(
        description="Deployment environment (development, staging, production)"
    )
    timestamp: datetime = Field(
        description="Health check timestamp (ISO 8601 UTC)"
    )
    system: Dict[str, Any] = Field(
        description="System resource information"
    )
    configuration: Dict[str, Any] = Field(
        description="Configuration validation status"
    )
    checks: Dict[str, bool] = Field(
        description="Individual health check results"
    )


def _get_system_info() -> Dict[str, Any]:
    """Get system resource information.
    
    Returns:
        Dictionary with CPU, memory, disk, and platform information
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": disk.percent,
        }
    except Exception as e:
        logger.warning(f"Failed to get system info: {e}")
        return {"error": str(e)}


def _validate_configuration() -> Dict[str, Any]:
    """Validate required configuration settings.
    
    Returns:
        Dictionary with validation status for each configuration area
    """
    checks = {
        "foundry_project_id": bool(settings.foundry_project_id),
        "foundry_endpoint": bool(settings.foundry_endpoint),
        "managed_identity": settings.use_managed_identity or bool(settings.azure_client_id),
        "app_insights": bool(settings.app_insights_connection_string),
    }
    
    return {
        "checks": checks,
        "all_passed": all(checks.values()),
        "dry_run_enabled": settings.dry_run_enabled,
    }


def _perform_health_checks() -> Dict[str, bool]:
    """Perform individual health checks.
    
    Returns:
        Dictionary mapping check names to pass/fail status
    """
    checks = {}
    
    # Configuration checks
    checks["config_foundry"] = bool(settings.foundry_project_id)
    checks["config_identity"] = settings.use_managed_identity or bool(settings.azure_client_id)
    
    # System resource checks (warning thresholds)
    try:
        memory = psutil.virtual_memory()
        checks["memory_ok"] = memory.percent < 90  # Warn if >90% memory used
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        checks["cpu_ok"] = cpu_percent < 95  # Warn if >95% CPU used
        
        disk = psutil.disk_usage('/')
        checks["disk_ok"] = disk.percent < 90  # Warn if >90% disk used
    except Exception as e:
        logger.warning(f"System checks failed: {e}")
        checks["system_ok"] = False
    
    return checks


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description=(
        "Returns health status of the agent including version, environment, "
        "system resources, and configuration validation. Used by container "
        "orchestration platforms and monitoring systems."
    ),
    responses={
        200: {
            "description": "Agent is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "environment": "production",
                        "timestamp": "2024-02-05T12:00:00Z",
                        "system": {
                            "cpu_percent": 25.5,
                            "memory_percent": 45.2,
                            "disk_percent": 60.1,
                        },
                        "configuration": {
                            "all_passed": True,
                            "dry_run_enabled": False,
                        },
                        "checks": {
                            "config_foundry": True,
                            "config_identity": True,
                            "memory_ok": True,
                            "cpu_ok": True,
                            "disk_ok": True,
                        }
                    }
                }
            }
        }
    }
)
async def health_check() -> HealthResponse:
    """Perform health check with comprehensive status.
    
    Validates:
    - Required configuration (Foundry project ID, identity)
    - System resources (CPU, memory, disk)
    - Application readiness
    
    Returns:
        HealthResponse with overall status and detailed checks
    """
    # Perform all health checks
    checks = _perform_health_checks()
    system_info = _get_system_info()
    config_validation = _validate_configuration()
    
    # Determine overall status
    critical_checks = ["config_foundry", "config_identity"]
    critical_passed = all(checks.get(c, False) for c in critical_checks)
    all_checks_passed = all(checks.values())
    
    if not critical_passed:
        overall_status = "unhealthy"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif not all_checks_passed:
        overall_status = "degraded"
        status_code = status.HTTP_200_OK
    else:
        overall_status = "healthy"
        status_code = status.HTTP_200_OK
    
    response = HealthResponse(
        status=overall_status,
        version=settings.version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc),
        system=system_info,
        configuration=config_validation,
        checks=checks,
    )
    
    # Log health check
    logger.debug(
        f"Health check: {overall_status}",
        extra={"checks": checks, "environment": settings.environment}
    )
    
    return response
