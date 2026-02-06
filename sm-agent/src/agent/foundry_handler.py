"""Foundry agent invocation handler.

Processes agent invocation requests from Azure AI Foundry, orchestrates
semantic model generation, and returns structured responses with artifacts.
"""

import asyncio
import httpx
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from pydantic import HttpUrl

from ..core.config import settings
from ..core.logging import get_logger, get_tracer, log_exception
from .schemas import (
    InvocationRequest,
    InvocationResponse,
    InvocationStatus,
    ArtifactUrls,
    DeploymentInfo,
    Diagnostics,
    ErrorResponse,
    CsvSchemaSource,
)


logger = get_logger(__name__)
tracer = get_tracer(__name__)
router = APIRouter()


class InvocationHandler:
    """Handles agent invocation orchestration.
    
    Coordinates:
    - Schema source validation and access checks
    - Workspace permissions validation
    - Semantic model generation (delegates to semantic_modeler)
    - Artifact generation and upload
    - Deployment execution (if deploy mode)
    """
    
    def __init__(self):
        """Initialize invocation handler."""
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    
    async def validate_schema_source(self, schema_source: CsvSchemaSource) -> bool:
        """Validate that schema source is accessible.
        
        For CSV URLs, performs HEAD request to check accessibility.
        For other source types, validation would be delegated to respective parsers.
        
        Args:
            schema_source: Schema source configuration
            
        Returns:
            True if accessible, raises HTTPException otherwise
            
        Raises:
            HTTPException: 400 if source is not accessible
        """
        if isinstance(schema_source, CsvSchemaSource):
            try:
                response = await self.client.head(str(schema_source.url))
                response.raise_for_status()
                logger.info(f"CSV source validated: {schema_source.url}")
                return True
            except httpx.HTTPStatusError as e:
                logger.warning(f"CSV source not accessible: {schema_source.url}, status={e.response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "INVALID_REQUEST",
                        "error_message": "Schema source URL is not accessible",
                        "details": {
                            "field": "schema_source.url",
                            "reason": f"HTTP {e.response.status_code} returned when attempting to fetch CSV",
                            "url": str(schema_source.url)
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Error validating CSV source: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "INVALID_REQUEST",
                        "error_message": f"Failed to validate schema source: {str(e)}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
        
        # For other source types, assume valid for now
        # TODO: Add validation for LakehouseSchemaSource and SqlSchemaSource
        return True
    
    async def invoke(
        self,
        request: InvocationRequest,
        correlation_id: Optional[str] = None
    ) -> InvocationResponse:
        """Execute agent invocation.
        
        Args:
            request: Validated invocation request
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            InvocationResponse with artifacts and status
            
        Raises:
            HTTPException: On validation or execution errors
        """
        invocation_id = uuid4()
        correlation_id = correlation_id or str(uuid4())
        start_time = datetime.now(timezone.utc)
        
        with tracer.start_as_current_span("agent_invocation") as span:
            span.set_attribute("invocation_id", str(invocation_id))
            span.set_attribute("correlation_id", correlation_id)
            span.set_attribute("deployment_mode", request.deployment_mode.value)
            
            logger.info(
                "Agent invocation started",
                extra={
                    "invocation_id": str(invocation_id),
                    "correlation_id": correlation_id,
                    "deployment_mode": request.deployment_mode.value,
                    "workspace_id": str(request.workspace_id)
                }
            )
            
            try:
                # Step 1: Validate schema source accessibility
                await self.validate_schema_source(request.schema_source)
                
                # Step 2: Validate workspace access (T021)
                # TODO: Implement workspace validation via Fabric client
                logger.info(f"Workspace validation pending implementation: {request.workspace_id}")
                
                # Step 3: Generate semantic model
                # TODO: Delegate to semantic_modeler.generate()
                logger.info("Semantic model generation pending implementation")
                
                # Step 4: Generate artifacts (placeholder URLs)
                # TODO: Upload artifacts to storage and generate SAS URLs
                artifact_urls = ArtifactUrls(
                    tmsl_url=HttpUrl("https://placeholder.blob.core.windows.net/artifacts/model.tmsl"),
                    tmdl_url=HttpUrl("https://placeholder.blob.core.windows.net/artifacts/model.tmdl"),
                    validation_report_url=HttpUrl("https://placeholder.blob.core.windows.net/reports/validation.json")
                )
                
                # Step 5: Execute deployment if requested
                deployment_info = None
                if request.deployment_mode.value == "deploy":
                    # TODO: Deploy to Fabric workspace
                    logger.info("Deployment execution pending implementation")
                    deployment_info = DeploymentInfo(
                        model_id=uuid4(),
                        workspace_id=request.workspace_id,
                        deployed_at=datetime.now(timezone.utc)
                    )
                
                # Calculate duration
                end_time = datetime.now(timezone.utc)
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # Build response
                response = InvocationResponse(
                    invocation_id=invocation_id,
                    status=InvocationStatus.SUCCEEDED,
                    duration_ms=duration_ms,
                    artifacts=artifact_urls,
                    deployment=deployment_info,
                    diagnostics=Diagnostics(
                        warnings=[],
                        anti_patterns=[]
                    )
                )
                
                logger.info(
                    "Agent invocation succeeded",
                    extra={
                        "invocation_id": str(invocation_id),
                        "correlation_id": correlation_id,
                        "duration_ms": duration_ms,
                        "status": "succeeded"
                    }
                )
                
                return response
                
            except HTTPException:
                # Re-raise HTTP exceptions (already formatted)
                raise
            except Exception as e:
                log_exception(logger, e, invocation_id=str(invocation_id), correlation_id=correlation_id)
                
                # Calculate duration even on failure
                end_time = datetime.now(timezone.utc)
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                logger.error(
                    "Agent invocation failed",
                    extra={
                        "invocation_id": str(invocation_id),
                        "correlation_id": correlation_id,
                        "duration_ms": duration_ms,
                        "status": "failed",
                        "error": str(e)
                    }
                )
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "INTERNAL_ERROR",
                        "error_message": f"Unexpected error during semantic model generation: {str(e)}",
                        "details": {
                            "invocation_id": str(invocation_id),
                            "diagnostic_string": str(e)
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
    
    async def close(self):
        """Close HTTP client and cleanup resources."""
        await self.client.aclose()


# Global handler instance
_handler: Optional[InvocationHandler] = None


def get_handler() -> InvocationHandler:
    """Get or create global InvocationHandler instance."""
    global _handler
    if _handler is None:
        _handler = InvocationHandler()
    return _handler


@router.post(
    "/invoke",
    response_model=InvocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Invoke Semantic Modeling Agent",
    description=(
        "Executes the semantic modeling agent with the provided schema source "
        "and configuration. Generates semantic model artifacts and optionally "
        "deploys to target Fabric workspace."
    ),
    responses={
        200: {"description": "Agent invocation completed successfully"},
        400: {"description": "Invalid request (malformed schema, missing parameters)"},
        403: {"description": "Permission denied (workspace access)"},
        500: {"description": "Internal server error"},
        504: {"description": "Request timed out (exceeded 3-minute limit)"},
    },
    tags=["Invocation"]
)
async def invoke_agent(
    request_payload: InvocationRequest,
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID"),
    response: Response = None
) -> InvocationResponse:
    """Invoke the semantic modeling agent.
    
    Args:
        request_payload: Invocation request with schema source and options
        x_correlation_id: Optional correlation ID for distributed tracing
        response: FastAPI response object
        
    Returns:
        InvocationResponse with artifacts and status
    """
    handler = get_handler()
    return await handler.invoke(request_payload, x_correlation_id)
