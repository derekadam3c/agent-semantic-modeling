"""Smoke tests for error handler (happy path only)."""

import pytest
from uuid import UUID
from pydantic import ValidationError as PydanticValidationError
from src.orchestration.error_handler import (
    ErrorHandler,
    ValidationException,
    WorkflowException,
    TimeoutException,
)
from src.core.schemas import ProblemDetails


class TestErrorHandler:
    """Smoke tests for ErrorHandler class."""

    def test_handle_validation_error(self):
        """Test handling of ValidationException."""
        exc = ValidationException(
            message="Invalid schema source",
            step_name="parse_schema",
        )

        problem = ErrorHandler.create_problem_details(
            exc=exc,
            status_code=400,
            correlation_id=UUID("00000000-0000-0000-0000-000000000123"),
        )

        assert isinstance(problem, ProblemDetails)
        assert problem.status == 400
        assert problem.title == "Workflow Validation Error"
        assert "Invalid schema source" in problem.detail

    def test_handle_workflow_error(self):
        """Test handling of WorkflowException."""
        exc = WorkflowException(
            message="Relationship analysis failed",
            step_name="analyze_relationships",
        )

        problem = ErrorHandler.create_problem_details(
            exc=exc,
            status_code=500,
            correlation_id=UUID("00000000-0000-0000-0000-000000000456"),
        )

        assert isinstance(problem, ProblemDetails)
        assert problem.status == 500
        assert problem.title == "Workflow Execution Failed"
        assert "Relationship analysis failed" in problem.detail

    def test_create_problem_details(self):
        """Test direct problem details creation."""
        exc = Exception("Test error message")

        problem = ErrorHandler.create_problem_details(
            exc=exc,
            status_code=400,
            correlation_id=UUID("00000000-0000-0000-0000-000000000789"),
        )

        assert problem.status == 400
        assert problem.title == "Internal Server Error"  # Default title for generic Exception
        assert "Test error message" in problem.detail


class TestCustomExceptions:
    """Smoke tests for custom exception classes."""

    def test_validation_exception(self):
        """Test ValidationException creation."""
        exc = ValidationException(
            message="Missing required field",
            step_name="parse_schema",
        )

        assert "Missing required field" in str(exc)
        assert exc.step_name == "parse_schema"

    def test_workflow_exception(self):
        """Test WorkflowException creation."""
        exc = WorkflowException(
            message="Step failed",
            step_name="parse_schema",
        )

        assert "Step failed" in str(exc)
        assert exc.step_name == "parse_schema"

    def test_timeout_exception(self):
        """Test TimeoutException creation."""
        exc = TimeoutException(
            message="Workflow timeout after 300 seconds",
            step_name="generate_tmsl",
        )

        assert "Workflow timeout" in str(exc)
        assert exc.step_name == "generate_tmsl"
