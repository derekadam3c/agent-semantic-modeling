"""Foundry agent invocation handler.

Processes agent invocation requests from Azure AI Foundry, orchestrates
the 8-step semantic modeling workflow, and returns structured responses.
"""

import asyncio
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..core.config import settings
from ..core.logging import get_logger, get_tracer
from ..core.schemas import (
    CsvUrlSource,
    DeploymentMode,
    ErrorDetail,
    ExecutionSummary,
    InvocationRequest,
    InvocationResponse,
    ProblemDetails,
    ResponseStatus,
    TMSLArtifact,
    WorkflowStatus,
)
from ..orchestration.error_handler import (
    ErrorHandler,
    TimeoutException,
    ValidationException,
    WorkflowException,
)
from ..orchestration.workflow_executor import WorkflowExecutor


logger = get_logger(__name__)
tracer = get_tracer(__name__)
router = APIRouter()


@router.post(
    "/invoke",
    response_model=InvocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Invoke Semantic Modeling Agent",
    description=(
        "Executes the 8-step semantic modeling workflow with the provided schema source. "
        "Generates TMSL artifacts, validates the model, and optionally deploys to Fabric workspace."
    ),
    responses={
        200: {
            "description": "Workflow completed successfully",
            "model": InvocationResponse,
        },
        400: {
            "description": "Request validation failed",
            "model": ProblemDetails,
        },
        500: {
            "description": "Workflow execution failed",
            "model": ProblemDetails,
        },
        504: {
            "description": "Workflow timeout (exceeded 5 minutes)",
            "model": ProblemDetails,
        },
    },
    tags=["Invocation"],
)
async def invoke_agent(
    request_payload: InvocationRequest,
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID"),
) -> InvocationResponse:
    """
    Invoke the semantic modeling agent.

    Orchestrates the complete 8-step workflow:
    1. Parse schema (CSV/SQL/Lakehouse)
    2. Classify fact/dimension tables
    3. Analyze relationships
    4. Build measures
    5. Detect hierarchies
    6. Generate TMSL
    7. Validate model
    8. Deploy (if requested)

    Args:
        request_payload: Invocation request with schema source and options
        x_correlation_id: Optional correlation ID for distributed tracing

    Returns:
        InvocationResponse with TMSL artifacts and execution summary

    Raises:
        HTTPException: On validation or execution errors (converted to RFC 7807)
    """
    # Extract or generate correlation ID
    correlation_id = UUID(x_correlation_id) if x_correlation_id else request_payload.correlation_id
    if not correlation_id:
        correlation_id = uuid4()

    with tracer.start_as_current_span("agent_invocation") as span:
        span.set_attribute("correlation_id", str(correlation_id))
        span.set_attribute("deployment_mode", request_payload.deployment_mode.value)
        span.set_attribute("workspace_id", str(request_payload.workspace_id))

        logger.info(
            "Agent invocation started",
            extra={
                "correlation_id": str(correlation_id),
                "deployment_mode": request_payload.deployment_mode.value,
                "workspace_id": str(request_payload.workspace_id),
                "schema_source_type": request_payload.schema_source.type,
            },
        )

        try:
            # Create workflow executor (5-minute timeout)
            executor = WorkflowExecutor(timeout_seconds=300)

            # Execute workflow
            workflow_result, execution_summary = await executor.execute(
                request=request_payload, correlation_id=correlation_id
            )

            # Build TMSL artifact from workflow result
            tmsl_data = workflow_result.get("generate_tmsl", {}).get("tmsl", {})
            tmsl_artifact = TMSLArtifact(
                model_name=tmsl_data.get("model_name", "GeneratedModel"),
                version=tmsl_data.get("version", "1.0"),
                tables=tmsl_data.get("tables", []),
                relationships=tmsl_data.get("relationships", []),
                measures=tmsl_data.get("measures", []),
                hierarchies=tmsl_data.get("hierarchies", []),
                metadata=tmsl_data.get("metadata", {}),
            )

            # Get validation results from workflow
            validation_data = workflow_result.get("validate_model", {})
            validation_results = validation_data.get("validation_results", [])

            # Build response
            response = InvocationResponse(
                correlation_id=correlation_id,
                status=ResponseStatus.SUCCESS,
                tmsl_output=tmsl_artifact,
                validation_results=validation_results,
                deployment_status=None,  # TODO: Add deployment status from workflow
                execution_summary=execution_summary,
            )

            logger.info(
                "Agent invocation succeeded",
                extra={
                    "correlation_id": str(correlation_id),
                    "duration_ms": execution_summary.duration_ms,
                    "completed_steps": execution_summary.completed_steps,
                    "status": "success",
                },
            )

            return response

        except ValidationError as exc:
            # Pydantic validation error (should be caught by FastAPI, but handle explicitly)
            logger.warning(
                "Request validation failed",
                extra={"correlation_id": str(correlation_id), "error": str(exc)},
            )
            return ErrorHandler.handle_validation_error(exc, correlation_id)

        except TimeoutException as exc:
            # Workflow timeout
            logger.error(
                "Workflow timeout",
                extra={
                    "correlation_id": str(correlation_id),
                    "step_name": exc.step_name,
                    "error": exc.message,
                },
            )
            return ErrorHandler.handle_workflow_error(exc, correlation_id)

        except WorkflowException as exc:
            # Workflow execution error
            logger.error(
                "Workflow execution failed",
                extra={
                    "correlation_id": str(correlation_id),
                    "step_name": exc.step_name,
                    "error": exc.message,
                },
            )
            return ErrorHandler.handle_workflow_error(exc, correlation_id)

        except Exception as exc:
            # Unexpected error
            logger.error(
                "Unexpected error in agent invocation",
                extra={"correlation_id": str(correlation_id), "error": str(exc)},
                exc_info=True,
            )
            return ErrorHandler.handle_generic_error(exc, correlation_id)

