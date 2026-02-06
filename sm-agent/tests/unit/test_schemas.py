"""Smoke tests for core schemas (happy path only)."""

import pytest
from pydantic import ValidationError
from src.core.schemas import (
    InvocationRequest,
    InvocationResponse,
    CsvUrlSource,
    SqlJsonSource,
    LakehouseSource,
    ProcessingOptions,
    DeploymentMode,
    ResponseStatus,
    TMSLArtifact,
    ExecutionSummary,
    WorkflowStatus,
    ErrorDetail,
)


class TestInvocationRequest:
    """Smoke tests for InvocationRequest validation."""

    def test_valid_csv_url_request(self):
        """Test valid CSV URL request creation."""
        from uuid import UUID
        
        request = InvocationRequest(
            schema_source=CsvUrlSource(
                type="csv_url",
                url="https://example.com/data.csv",
                sample_rows=100,
            ),
            workspace_id=UUID("00000000-0000-0000-0000-000000000000"),
            deployment_mode=DeploymentMode.DRY_RUN,
            options=ProcessingOptions(
                detect_measures=True,
                detect_hierarchies=True,
            ),
        )

        assert request.schema_source.type == "csv_url"
        assert str(request.workspace_id) == "00000000-0000-0000-0000-000000000000"
        assert request.deployment_mode == DeploymentMode.DRY_RUN
        assert request.options.detect_measures is True

    def test_valid_sql_json_request(self):
        """Test valid SQL JSON request creation."""
        from uuid import UUID
        
        request = InvocationRequest(
            schema_source=SqlJsonSource(
                type="sql_json",
                tables=[{"name": "Sales"}],
                columns=[{"name": "SalesID", "table": "Sales"}],
            ),
            workspace_id=UUID("00000000-0000-0000-0000-000000000000"),
            deployment_mode=DeploymentMode.VALIDATE_ONLY,
        )

        assert request.schema_source.type == "sql_json"
        assert request.deployment_mode == DeploymentMode.VALIDATE_ONLY

    def test_valid_lakehouse_request(self):
        """Test valid Lakehouse request creation."""
        from uuid import UUID
        
        request = InvocationRequest(
            schema_source=LakehouseSource(
                type="lakehouse_connection",
                workspace_id=UUID("11111111-1111-1111-1111-111111111111"),
                item_id=UUID("22222222-2222-2222-2222-222222222222"),
            ),
            workspace_id=UUID("00000000-0000-0000-0000-000000000000"),
            deployment_mode=DeploymentMode.AUTO_DEPLOY,
        )

        assert request.schema_source.type == "lakehouse_connection"
        assert str(request.schema_source.workspace_id) == "11111111-1111-1111-1111-111111111111"


class TestInvocationResponse:
    """Smoke tests for InvocationResponse serialization."""

    def test_successful_response_creation(self):
        """Test successful response creation."""
        from uuid import UUID
        
        response = InvocationResponse(
            correlation_id=UUID("00000000-0000-0000-0000-000000000123"),
            status=ResponseStatus.SUCCESS,
            tmsl_output=TMSLArtifact(
                model_name="TestModel",
                tmsl_content='{"name": "TestModel"}',
                database_name="TestDB",
            ),
            execution_summary=ExecutionSummary(
                status=WorkflowStatus.COMPLETED,
                total_steps=8,
                completed_steps=8,
            ),
        )

        assert response.status == ResponseStatus.SUCCESS
        assert response.tmsl_output.model_name == "TestModel"
        assert response.execution_summary.completed_steps == 8

    def test_validation_error_response(self):
        """Test validation error response creation."""
        from uuid import UUID
        
        response = InvocationResponse(
            correlation_id=UUID("00000000-0000-0000-0000-000000000123"),
            status=ResponseStatus.VALIDATION_ERROR,
            execution_summary=ExecutionSummary(
                status=WorkflowStatus.FAILED,
                total_steps=8,
                completed_steps=0,
                duration_ms=50,
            ),
        )

        assert response.status == ResponseStatus.VALIDATION_ERROR
        assert response.tmsl_output is None


class TestErrorDetail:
    """Smoke tests for RFC 7807 error responses."""

    def test_error_detail_creation(self):
        """Test error detail creation."""
        from uuid import UUID
        
        error = ErrorDetail(
            type="https://api.example.com/errors/validation",
            title="Validation Error",
            status=400,
            detail="Missing required field: schema_source",
            instance="/invoke",
            correlation_id=UUID("00000000-0000-0000-0000-000000000123"),
        )

        assert error.status == 400
        assert error.title == "Validation Error"
        assert "schema_source" in error.detail
