"""
Error handling and RFC 7807 Problem Details mapping.

This module provides exception handling and error response generation
for the Agent Invocation Handler, implementing RFC 7807 Problem Details standard.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..core.schemas import ErrorDetail, ProblemDetails


class WorkflowException(Exception):
    """Base exception for workflow execution errors."""

    def __init__(
        self,
        message: str,
        step_name: Optional[str] = None,
        affected_objects: Optional[list[str]] = None,
        remediation: Optional[str] = None,
    ):
        """
        Initialize workflow exception.

        Args:
            message: Error message
            step_name: Name of failed workflow step
            affected_objects: List of affected entities (tables, columns, etc.)
            remediation: Suggested remediation steps
        """
        super().__init__(message)
        self.message = message
        self.step_name = step_name
        self.affected_objects = affected_objects or []
        self.remediation = remediation


class ValidationException(WorkflowException):
    """Exception for validation errors during workflow execution."""

    pass


class TimeoutException(WorkflowException):
    """Exception for workflow timeout."""

    pass


class ErrorHandler:
    """Centralized error handling and RFC 7807 response generation."""

    @staticmethod
    def create_problem_details(
        exc: Exception,
        status_code: int,
        correlation_id: Optional[UUID] = None,
        instance: str = "/invoke",
    ) -> ProblemDetails:
        """
        Create RFC 7807 Problem Details from exception.

        Args:
            exc: The exception to convert
            status_code: HTTP status code
            correlation_id: Request correlation ID
            instance: URI reference to the request

        Returns:
            ProblemDetails object with error information
        """
        # Determine error type and title based on exception class
        if isinstance(exc, ValidationError):
            error_type = "https://agent.fabric.microsoft.com/errors/validation-error"
            title = "Request Validation Failed"
            detail = str(exc)
            field_errors = {
                err["loc"][0] if err["loc"] else "unknown": err["msg"]
                for err in exc.errors()
            }
        elif isinstance(exc, ValidationException):
            error_type = "https://agent.fabric.microsoft.com/errors/workflow-validation"
            title = "Workflow Validation Error"
            detail = exc.message
            field_errors = None
        elif isinstance(exc, TimeoutException):
            error_type = "https://agent.fabric.microsoft.com/errors/timeout"
            title = "Workflow Timeout"
            detail = exc.message
            field_errors = None
        elif isinstance(exc, WorkflowException):
            error_type = "https://agent.fabric.microsoft.com/errors/workflow-failure"
            title = "Workflow Execution Failed"
            detail = exc.message
            field_errors = None
        elif isinstance(exc, HTTPException):
            error_type = f"https://agent.fabric.microsoft.com/errors/http-{exc.status_code}"
            title = "HTTP Error"
            detail = exc.detail
            field_errors = None
        else:
            error_type = "https://agent.fabric.microsoft.com/errors/internal-error"
            title = "Internal Server Error"
            detail = str(exc)
            field_errors = None

        # Build ProblemDetails
        problem = ProblemDetails(
            type=error_type,
            title=title,
            status=status_code,
            detail=detail,
            instance=instance,
            correlation_id=correlation_id,
            field_errors=field_errors,
            failed_at=datetime.utcnow(),
        )

        # Add workflow-specific fields if available
        if isinstance(exc, WorkflowException):
            problem.workflow_step = exc.step_name
            problem.remediation = exc.remediation

        return problem

    @staticmethod
    def handle_validation_error(
        exc: ValidationError, correlation_id: Optional[UUID] = None
    ) -> JSONResponse:
        """
        Handle Pydantic validation error.

        Args:
            exc: Pydantic ValidationError
            correlation_id: Request correlation ID

        Returns:
            JSONResponse with RFC 7807 Problem Details
        """
        problem = ErrorHandler.create_problem_details(
            exc=exc,
            status_code=status.HTTP_400_BAD_REQUEST,
            correlation_id=correlation_id,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=problem.model_dump(exclude_none=True),
        )

    @staticmethod
    def handle_workflow_error(
        exc: WorkflowException, correlation_id: Optional[UUID] = None
    ) -> JSONResponse:
        """
        Handle workflow execution error.

        Args:
            exc: WorkflowException
            correlation_id: Request correlation ID

        Returns:
            JSONResponse with RFC 7807 Problem Details
        """
        # Determine status code based on exception type
        if isinstance(exc, TimeoutException):
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        elif isinstance(exc, ValidationException):
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        problem = ErrorHandler.create_problem_details(
            exc=exc, status_code=status_code, correlation_id=correlation_id
        )
        return JSONResponse(
            status_code=status_code, content=problem.model_dump(exclude_none=True)
        )

    @staticmethod
    def handle_generic_error(
        exc: Exception, correlation_id: Optional[UUID] = None
    ) -> JSONResponse:
        """
        Handle generic exceptions.

        Args:
            exc: Generic Exception
            correlation_id: Request correlation ID

        Returns:
            JSONResponse with RFC 7807 Problem Details
        """
        problem = ErrorHandler.create_problem_details(
            exc=exc,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            correlation_id=correlation_id,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=problem.model_dump(exclude_none=True),
        )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for FastAPI application.

    Args:
        request: FastAPI request object
        exc: Raised exception

    Returns:
        JSONResponse with RFC 7807 Problem Details
    """
    # Extract correlation ID from header if available
    correlation_id = request.headers.get("X-Correlation-ID")

    # Route to appropriate handler
    if isinstance(exc, ValidationError):
        return ErrorHandler.handle_validation_error(exc, correlation_id)
    elif isinstance(exc, WorkflowException):
        return ErrorHandler.handle_workflow_error(exc, correlation_id)
    else:
        return ErrorHandler.handle_generic_error(exc, correlation_id)
